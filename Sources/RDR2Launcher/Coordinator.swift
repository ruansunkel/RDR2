import AppKit
import LauncherCore
import CryptoKit

@MainActor final class Coordinator {
    let paths: DataPaths
    let resources: URL
    var session: Session
    var runtime: Runtime?
    var busy = false
    var changed: ((String) -> Void)?
    private var children: [Process] = []
    private var lockFD: Int32 = -1

    private let isolatedHome: URL?

    init(resources: URL, dataRoot: URL? = nil, usePrivateHome: Bool = false) throws {
        self.resources = resources
        paths = try dataRoot.map { DataPaths(root: $0) } ?? .standard()
        isolatedHome = usePrivateHome ? paths.root.appendingPathComponent("build-test-home") : nil
        try paths.create()
        if let isolatedHome { try FileManager.default.createDirectory(at: isolatedHome, withIntermediateDirectories: true) }
        lockFD = Darwin.open(paths.root.appendingPathComponent("state/launcher.lock").path, O_CREAT | O_RDWR, 0o600)
        guard lockFD >= 0, flock(lockFD, LOCK_EX | LOCK_NB) == 0 else {
            throw LauncherError.message("RDR2Launcher is already open for this user.")
        }
        session = try paths.load()
        // Cached progress is advisory; every operation checks real files and processes again.
    }
    deinit { if lockFD >= 0 { Darwin.close(lockFD) } }

    func status(_ stage: Stage, _ text: String) {
        session.stage = stage
        do { try paths.save(session) } catch { changed?("Could not save progress. Check data-folder permissions."); return }
        changed?(text)
        // Only application-defined events are logged; never Wine/client output or account data.
        let line = "\(ISO8601DateFormatter().string(from: Date())) \(stage.rawValue)\n"
        let log = paths.logs.appendingPathComponent("events.log")
        if !FileManager.default.fileExists(atPath: log.path) { FileManager.default.createFile(atPath: log.path, contents: nil) }
        if let h = try? FileHandle(forWritingTo: log) {
            defer { try? h.close() }
            _ = try? h.seekToEnd(); try? h.write(contentsOf: Data(line.utf8))
        }
    }

    func preflight() throws {
        #if !arch(arm64)
        throw LauncherError.message("This launcher requires an Apple Silicon Mac.")
        #endif
        guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion >= 14 else {
            throw LauncherError.message("macOS 14 or newer is required.")
        }
        guard SystemCheck.rosettaAvailable() else {
            status(.missingRosetta, "Rosetta 2 is required for the bundled Intel Wine engine. Use Apple’s installation prompt; then reopen this app.")
            throw LauncherError.message("Rosetta 2 is unavailable. No system software has been installed.")
        }
        guard FileManager.default.fileExists(atPath: resources.appendingPathComponent("runtime-manifest.json").path) else {
            status(.missingRuntime, "This is a launcher-only development preview. Build a bundle with the verified r27 runtime before installing Steam.")
            throw LauncherError.message("The Wine runtime is not bundled in this development preview.")
        }
        if runtime == nil { runtime = try Runtime.load(resources: resources) }
        session.stage = FileManager.default.fileExists(atPath: paths.steam.path) ? .needsSteamLogin : .needsSteam
    }

    func perform(_ action: SteamAction) {
        guard !busy else { return }
        Task {
            do {
                try await execute(action)
            } catch {
                if session.stage == .missingRosetta || session.stage == .missingRuntime {
                    changed?(error.localizedDescription)
                } else { status(.error, error.localizedDescription) }
            }
        }
    }

    func execute(_ action: SteamAction) async throws {
        guard !busy else { throw LauncherError.message("Setup is already running.") }
        busy = true
        defer { busy = false }
        try preflight()
        if !FileManager.default.fileExists(atPath: paths.steam.path) { try checkDisk(game: false) }
        try await initializePrefix()
        try await matchHostTimeZone()
        if !FileManager.default.fileExists(atPath: paths.steam.path) {
            try checkDisk(game: false)
            try await installSteam()
        }
        if case .install = action { try checkDisk() }
        if case .play = action {
            let tasks = try await wine(["tasklist", "/FO", "CSV", "/NH"], capture: true)
            if tasks.lowercased().contains("\"rdr2.exe\"") {
                changed?("RDR2 is already running in this prefix. Switch to its window. Story Mode has not been verified by this launcher.")
                return
            }
            let service = paths.prefix.appendingPathComponent("drive_c/Program Files/Rockstar Games/Launcher/RockstarService.exe")
            if FileManager.default.fileExists(atPath: service.path) {
                // A user client must keep Wine alive while its Windows service starts.
                // No prefix restart, service reinstall, or registry deletion is performed.
                try startSteam(.open)
                let state = try await wine(["sc", "query", "Rockstar Service"], capture: true)
                if !RockstarService.isRunning(state) {
                    status(.launching, "Starting Rockstar’s installed background service in the same Steam environment…")
                    try await wine(["sc", "start", "Rockstar Service"], capture: true)
                    let started = try await wine(["sc", "query", "Rockstar Service"], capture: true)
                    guard RockstarService.isRunning(started) else {
                        throw LauncherError.message("Rockstar’s background service did not remain running. Keep Steam open and retry Play; the game files have not been changed.")
                    }
                }
            }
            status(.launching, "Starting through Steam → Rockstar. Complete sign-in in their windows. A process starting does not verify Story Mode.")
        } else if case .install = action {
            status(.rdr2Downloading, "Steam will confirm ownership, installation location and download progress. Choose R:\\ in Steam for your selected folder. Press Play after Steam reports completion.")
        } else {
            status(.needsSteamLogin, "Steam handles sign-in, updates and verification. Its first update can take 15–25 minutes. Retry Open Steam after a client crash.")
        }
        try startSteam(action)
    }

    func checkDisk(game: Bool = true) throws {
        let library = URL(fileURLWithPath: session.library ?? paths.root.path)
        let required: Int64 = (game ? 150 : 8) * 1024 * 1024 * 1024
        guard try SystemCheck.availableBytes(at: library) >= required else {
            throw LauncherError.message(game ? "At least 150 GiB free is required before a fresh game installation. Choose a larger game folder, or use Play for an existing installation." : "At least 8 GiB free is required for Windows Steam setup.")
        }
    }

    func matchHostTimeZone() async throws {
        if let pending = session.pendingTimeZoneBackup {
            try await WineTimeZoneRepair.restoreMissing(backupKey: pending) { try await self.wine($0, capture: true) }
            session.pendingTimeZoneBackup = nil
            try paths.save(session)
        }
        let hostZone = TimeZone.autoupdatingCurrent.identifier
        guard hostZone == "Africa/Johannesburg" else { return }
        let reported = try await wine(["reg", "query", WineTimeZoneRepair.info, "/v", "TimeZoneKeyName"], capture: true)
        guard WineTimeZoneRepair.needed(hostZone: hostZone, reported: reported) else { return }
        let tag = "native-\(Int(Date().timeIntervalSince1970))-\(UUID().uuidString)"
        let backup = paths.root.appendingPathComponent("state/timezone-repair-\(tag)")
        try FileManager.default.createDirectory(at: backup, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try FileManager.default.copyItem(at: paths.prefix.appendingPathComponent("system.reg"), to: backup.appendingPathComponent("system.reg.backup"))
        let key = WineTimeZoneRepair.backupRoot + "\\" + tag
        // Persist before the first registry change, so a crash between moves is
        // repaired on the next launch without resetting any other prefix data.
        session.pendingTimeZoneBackup = key
        try paths.save(session)
        status(.needsPrefix, "Matching this Windows environment’s timezone to South Africa; preserving the original definitions…")
        try await WineTimeZoneRepair.apply(backupKey: key, year: Calendar.current.component(.year, from: Date())) { command in
            try await self.wine(command, capture: true)
        }
        let journal: [String: Any] = ["prefix": paths.prefix.path, "target": WineTimeZoneRepair.target,
                                     "backup_registry_key": key, "moved": WineTimeZoneRepair.conflicts,
                                     "verified_windows_timezone": WineTimeZoneRepair.target, "macos_timezone_unchanged": true]
        try JSONSerialization.data(withJSONObject: journal, options: .prettyPrinted).write(to: backup.appendingPathComponent("recovery.json"), options: .atomic)
        session.pendingTimeZoneBackup = nil
        try paths.save(session)
    }

    func process(_ arguments: [String]) throws -> Process {
        guard let runtime else { throw LauncherError.message("The bundled runtime has not been validated.") }
        let p = Process()
        p.executableURL = try Runtime.safeURL(runtime.wine, root: resources)
        p.arguments = arguments
        p.environment = runtime.environment(resources: resources, paths: paths)
        if let isolatedHome { p.environment?["HOME"] = isolatedHome.path }
        p.currentDirectoryURL = paths.root
        p.standardOutput = FileHandle.nullDevice; p.standardError = FileHandle.nullDevice
        return p
    }

    @discardableResult func wine(_ args: [String], capture: Bool = false) async throws -> String {
        let p = try process(args)
        // Capture only public process/service/timezone responses, never account
        // output. The private temporary snapshot is removed after command exit.
        let result = try await ProcessRunner.run(p, captureIn: capture ? paths.state.deletingLastPathComponent() : nil)
        guard result.status == 0 else { throw LauncherError.message("Wine operation failed (exit \(result.status)). Use Repair or retry; account output is intentionally not logged.") }
        return result.output
    }

    func initializePrefix() async throws {
        let marker = paths.root.appendingPathComponent("state/prefix-configured")
        guard !FileManager.default.fileExists(atPath: marker.path) ||
                !FileManager.default.fileExists(atPath: paths.prefix.appendingPathComponent("system.reg").path) else { return }
        status(.needsPrefix, "Initializing a private Windows environment. Keep this app open.")
        try await wine(["wineboot", "--init"])
        try await wine(["wineboot", "--update"])
        // Wine may link Documents/Desktop to the host. Keep new-prefix game saves inside app data.
        let users = paths.prefix.appendingPathComponent("drive_c/users")
        for user in try FileManager.default.contentsOfDirectory(at: users, includingPropertiesForKeys: nil) {
            for name in ["Documents", "Desktop", "Downloads", "Music", "Pictures", "Videos"] {
                let folder = user.appendingPathComponent(name)
                if (try? FileManager.default.destinationOfSymbolicLink(atPath: folder.path)) != nil {
                    try FileManager.default.moveItem(at: folder, to: folder.appendingPathExtension(DataPaths.backupSuffix()))
                    try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
                }
            }
        }
        // Back up registry before applying the pinned Rockstar and RDR2 recipe settings.
        for name in ["system.reg", "user.reg", "userdef.reg"] {
            let file = paths.prefix.appendingPathComponent(name)
            if FileManager.default.fileExists(atPath: file.path) {
                try FileManager.default.copyItem(at: file, to: file.appendingPathExtension(DataPaths.backupSuffix()))
            }
        }
        for (key, name, type, value) in [
            ("HKLM\\System\\CurrentControlSet\\Control", "ServicesPipeTimeout", "REG_SZ", "60000"),
            ("HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\Rockstar-Games-Launcher.exe", "GlobalFlag", "REG_DWORD", "16"),
            ("HKCU\\Software\\Wine\\AppDefaults\\RDR2.exe\\DllOverrides", "vulkan-1", "REG_SZ", "native,builtin")
        ] {
            try await wine(["reg", "add", key, "/v", name, "/t", type, "/d", value, "/f"])
        }
        if let library = session.library { try mapLibrary(library) }
        try Data("r27; sync=none; dxmt; Vulkan\n".utf8).write(to: marker, options: .atomic)
    }

    func installSteam() async throws {
        status(.needsSteam, "Downloading the official Windows Steam installer from Valve over HTTPS.")
        let url = URL(string: "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe")!
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200,
              http.url?.scheme == "https", http.url?.host == url.host,
              data.count > 2, data.count < 100 * 1024 * 1024, data.prefix(2) == Data([0x4d, 0x5a]) else {
            throw LauncherError.message("Valve’s installer download failed validation. Check the network and retry.")
        }
        let installer = paths.downloads.appendingPathComponent("SteamSetup-\(UUID().uuidString).exe")
        try data.write(to: installer, options: .atomic)
        let provenance = "Source: \(url.absoluteString)\nSHA256: \(try Runtime.digest(installer))\nTransport: HTTPS; Valve provides no pinned hash in the upstream recipe. Authenticode not independently verified.\n"
        try Data(provenance.utf8).write(to: installer.appendingPathExtension("provenance.txt"))
        status(.steamUpdating, "Installing Steam. Complete any installer/license windows. Steam’s own updater may take 15–25 minutes.")
        try await wine([installer.path, "/S"])
        guard FileManager.default.fileExists(atPath: paths.steam.path) else {
            throw LauncherError.message("The Steam installer exited without creating steam.exe. Retry Install & Play.")
        }
    }

    func startSteam(_ action: SteamAction) throws {
        let p = try process([paths.steam.path] + action.arguments)
        children.removeAll { !$0.isRunning }
        // Steam's own single-instance IPC routes URI requests to the existing client.
        try p.run()
        children.append(p)
    }

    func mapLibrary(_ path: String) throws {
        let drive = paths.prefix.appendingPathComponent("dosdevices/r:")
        if let existing = try? FileManager.default.destinationOfSymbolicLink(atPath: drive.path) {
            guard existing == path else { throw LauncherError.message("The R: drive is already mapped. Preserve the existing library; use Steam’s Storage settings to move it.") }
        } else {
            try FileManager.default.createSymbolicLink(atPath: drive.path, withDestinationPath: path)
        }
    }

    func chooseLibrary() {
        guard !busy else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true; panel.canChooseFiles = false; panel.canCreateDirectories = true
        panel.message = "Choose a persistent Steam library folder. Select R:\\ in Steam’s Storage settings. Existing game files are never moved or deleted."
        if panel.runModal() == .OK, let url = panel.url {
            do {
                guard FileManager.default.isWritableFile(atPath: url.path),
                      !url.resolvingSymlinksInPath().pathComponents.contains(where: { $0.hasSuffix(".app") }) else {
                    throw LauncherError.message("Choose a writable folder outside any application bundle.")
                }
                if FileManager.default.fileExists(atPath: paths.prefix.appendingPathComponent("dosdevices").path) { try mapLibrary(url.path) }
                session.library = url.path; try paths.save(session)
                changed?("Game folder selected. In Windows Steam, use Storage settings to add a library on R:\\.")
            } catch { status(.error, error.localizedDescription) }
        }
    }

    func repair() {
        // Steam owns validation. Never erase prefixes, registry, saves or libraries.
        runtime = nil
        perform(.verify)
    }
}
