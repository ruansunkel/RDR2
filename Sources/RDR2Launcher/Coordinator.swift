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

    init(resources: URL) throws {
        self.resources = resources
        paths = try .standard()
        try paths.create()
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
        let memory = ProcessInfo.processInfo.physicalMemory
        guard memory == 0 || memory >= 16 * 1024 * 1024 * 1024 else {
            throw LauncherError.message("This Vulkan baseline requires at least 16 GiB RAM; 8 GiB is insufficient in upstream tests. No game software has been installed.")
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
        busy = true
        Task {
            defer { busy = false }
            do {
                try preflight()
                if !FileManager.default.fileExists(atPath: paths.steam.path) { try checkDisk() }
                try await initializePrefix()
                if !FileManager.default.fileExists(atPath: paths.steam.path) {
                    try checkDisk()
                    try await installSteam()
                }
                if case .install = action { try checkDisk() }
                if case .play = action {
                    let tasks = try await wine(["tasklist", "/FO", "CSV", "/NH"], capture: true)
                    if tasks.lowercased().contains("\"rdr2.exe\"") {
                        changed?("RDR2 is already running in this prefix. Switch to its window. Story Mode has not been verified by this launcher.")
                        return
                    }
                    status(.launching, "Starting through Steam → Rockstar. Complete sign-in in their windows. A process starting does not verify Story Mode.")
                } else if case .install = action {
                    status(.rdr2Downloading, "Steam will confirm ownership, installation location and download progress. Choose R:\\ in Steam for your selected folder. Press Play after Steam reports completion.")
                } else {
                    status(.needsSteamLogin, "Steam handles sign-in, updates and verification. Its first update can take 15–25 minutes. Retry Open Steam after a client crash.")
                }
                try startSteam(action)
            } catch {
                if session.stage == .missingRosetta || session.stage == .missingRuntime {
                    changed?(error.localizedDescription)
                } else { status(.error, error.localizedDescription) }
            }
        }
    }

    func checkDisk() throws {
        let library = URL(fileURLWithPath: session.library ?? paths.root.path)
        guard try SystemCheck.availableBytes(at: library) >= 150 * 1024 * 1024 * 1024 else {
            throw LauncherError.message("At least 150 GiB free is required before a fresh installation. Choose a larger game folder, or use Play for an existing Steam installation.")
        }
    }

    func process(_ arguments: [String]) throws -> Process {
        guard let runtime else { throw LauncherError.message("The bundled runtime has not been validated.") }
        let p = Process()
        p.executableURL = try Runtime.safeURL(runtime.wine, root: resources)
        p.arguments = arguments
        p.environment = runtime.environment(resources: resources, paths: paths)
        p.currentDirectoryURL = paths.root
        p.standardOutput = FileHandle.nullDevice; p.standardError = FileHandle.nullDevice
        return p
    }

    @discardableResult func wine(_ args: [String], capture: Bool = false) async throws -> String {
        let p = try process(args)
        // Only tasklist is captured, into memory; never stored. Drain concurrently to avoid pipe deadlocks.
        let pipe = capture ? Pipe() : nil
        if let pipe { p.standardOutput = pipe }
        let dataTask = pipe.map { output in Task.detached { output.fileHandleForReading.readDataToEndOfFile() } }
        let code: Int32 = try await withCheckedThrowingContinuation { continuation in
            p.terminationHandler = { child in continuation.resume(returning: child.terminationStatus) }
            do { try p.run(); try? pipe?.fileHandleForWriting.close() }
            catch { p.terminationHandler = nil; try? pipe?.fileHandleForWriting.close(); continuation.resume(throwing: error) }
        }
        let data = await dataTask?.value ?? Data()
        guard code == 0 else { throw LauncherError.message("Wine operation failed (exit \(code)). Use Repair or retry; account output is intentionally not logged.") }
        return String(decoding: data, as: UTF8.self)
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
