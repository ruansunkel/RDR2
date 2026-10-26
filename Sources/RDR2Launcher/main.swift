import AppKit
import LauncherCore

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate {
    let edition = LauncherEdition.current
    var window: NSWindow!
    var coordinator: Coordinator?
    let label = NSTextField(wrappingLabelWithString: "Checking launcher…")
    let dataLabel = NSTextField(labelWithString: "")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let menu = NSMenu()
        let appItem = NSMenuItem(); menu.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        appMenu.addItem(withTitle: "Quit RDR2Launcher", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        NSApp.mainMenu = menu
        let environmentItem = NSMenuItem(title: "Environment", action: nil, keyEquivalent: "")
        let environmentMenu = NSMenu(title: "Environment")
        environmentMenu.addItem(withTitle: "Use existing environment…", action: #selector(existingEnvironment), keyEquivalent: "")
        environmentMenu.addItem(withTitle: "Use default environment", action: #selector(defaultEnvironment), keyEquivalent: "")
        environmentItem.submenu = environmentMenu; menu.addItem(environmentItem)
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 650, height: 450),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = edition.displayName
        window.center()
        let title = NSTextField(labelWithString: "Red Dead Redemption 2")
        title.font = .boldSystemFont(ofSize: 24)
        let subtitle = NSTextField(wrappingLabelWithString: edition.subtitle)
        label.font = .systemFont(ofSize: 14)
        dataLabel.font = .systemFont(ofSize: 11)
        dataLabel.textColor = .secondaryLabelColor
        dataLabel.isSelectable = true
        dataLabel.lineBreakMode = .byTruncatingMiddle
        label.setContentHuggingPriority(.defaultLow, for: .vertical)
        let row1 = NSStackView(views: [button("Install & Play", #selector(install)), button("Play", #selector(play)), button("Open Steam", #selector(openSteam))])
        let row2 = NSStackView(views: [button("Repair", #selector(repair)), button("Choose game folder", #selector(choose)), button("View logs", #selector(logs)), button("Rosetta help", #selector(rosettaHelp)), button("Quit", #selector(quit))])
        let row3 = NSStackView(views: [button("Use existing environment…", #selector(existingEnvironment)), button("Show game files", #selector(gameFiles))])
        let stack = NSStackView(views: [title, subtitle, dataLabel, label, row1, row2, row3])
        stack.orientation = .vertical; stack.alignment = .leading; stack.spacing = 14
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 24),
            stack.bottomAnchor.constraint(equalTo: window.contentView!.bottomAnchor, constant: -24)
        ])
        do {
            let store = EnvironmentSelectionStore(defaultDataRoot: try DataPaths.standard().root)
            let args = CommandLine.arguments
            let selection: EnvironmentSelection?
            if let index = args.firstIndex(of: "--data-directory") {
                guard args.indices.contains(index + 1), args[index + 1].hasPrefix("/") else {
                    throw LauncherError.message("--data-directory requires an absolute existing launcher data folder.")
                }
                selection = try EnvironmentSelection(existingDataRoot: URL(fileURLWithPath: args[index + 1]))
            } else { selection = try store.load() }
            try connect(selection, remember: args.contains("--remember-environment"))
            guard let resources = Bundle.main.resourceURL else { throw LauncherError.message("Missing app resources") }
            if !FileManager.default.fileExists(atPath: resources.appendingPathComponent("runtime-manifest.json").path) {
                label.stringValue = "Launcher-only preview: the verified Wine engine is not bundled. See BUILD.md to stage the runtime. No game launch has been verified."
            } else {
                label.stringValue = coordinator?.paths.gameDirectory(library: coordinator?.session.library) != nil
                    ? "Existing RDR2 files found in this environment. Open Steam to confirm installation and use Play."
                    : "Steam confirms ownership and download completion. If your game is in another environment, select Use existing environment."
            }
        } catch { label.stringValue = error.localizedDescription }
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
        if CommandLine.arguments.contains("--play-game") { coordinator?.perform(.play) }
    }
    func button(_ title: String, _ action: Selector) -> NSButton { NSButton(title: title, target: self, action: action) }
    func connect(_ selection: EnvironmentSelection?, remember: Bool) throws {
        guard coordinator?.busy != true else { throw LauncherError.message("Wait for the current setup operation to finish.") }
        guard let resources = Bundle.main.resourceURL else { throw LauncherError.message("Missing app resources") }
        let root = try selection?.url ?? DataPaths.standard().root
        if edition != .standard,
           root.standardizedFileURL.resolvingSymlinksInPath() == (try DataPaths.standard(edition: .standard).root).standardizedFileURL.resolvingSymlinksInPath() {
            throw LauncherError.message("Choose a copied test environment. The experimental launcher uses separate data so the regular installation stays available.")
        }
        if coordinator?.paths.root.standardizedFileURL.resolvingSymlinksInPath().path != root.standardizedFileURL.resolvingSymlinksInPath().path {
            let next = try Coordinator(resources: resources, dataRoot: root, usePrivateHome: selection?.usePrivateHome ?? false)
            if remember { try EnvironmentSelectionStore(defaultDataRoot: DataPaths.standard().root).save(selection) }
            coordinator = next
        } else if remember { try EnvironmentSelectionStore(defaultDataRoot: DataPaths.standard().root).save(selection) }
        coordinator?.changed = { [weak self] text in self?.label.stringValue = text }
        dataLabel.stringValue = "Data folder: \(root.path)"
        window.title = "\(edition.displayName) — \(root.lastPathComponent)"
    }
    @objc func existingEnvironment() {
        guard coordinator?.busy != true else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true; panel.canChooseFiles = false
        panel.message = "Choose the existing launcher DATA folder containing prefixes/default and Steam. This reuses the installation and sign-in without moving or copying files."
        if panel.runModal() == .OK, let url = panel.url {
            do {
                try connect(EnvironmentSelection(existingDataRoot: url), remember: true)
                label.stringValue = "Using the selected existing Steam environment. Open Steam to see its installed games."
            } catch { label.stringValue = error.localizedDescription }
        }
    }
    @objc func defaultEnvironment() {
        do { try connect(nil, remember: true); label.stringValue = "Using the default environment. Other environments and game files are preserved." }
        catch { label.stringValue = error.localizedDescription }
    }
    @objc func gameFiles() {
        if let folder = coordinator?.paths.gameDirectory(library: coordinator?.session.library) { NSWorkspace.shared.open(folder) }
        else { label.stringValue = "No RDR2 folder found in this environment. Use existing environment or check Steam’s Storage settings for another library." }
    }
    @objc func install() { coordinator?.perform(.install) }
    @objc func play() { coordinator?.perform(.play) }
    @objc func openSteam() { coordinator?.perform(.open) }
    @objc func repair() { coordinator?.repair() }
    @objc func choose() { coordinator?.chooseLibrary() }
    @objc func logs() { if let paths = coordinator?.paths { NSWorkspace.shared.open(paths.logs) } }
    @objc func rosettaHelp() { NSWorkspace.shared.open(URL(string: "https://support.apple.com/en-us/102527")!) }
    @objc func quit() { NSApp.terminate(nil) }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard coordinator?.busy == true else { return .terminateNow }
        let alert = NSAlert()
        alert.messageText = "Setup is still running"
        alert.informativeText = "Keep this launcher open until setup completes. Steam downloads continue in Steam."
        alert.runModal()
        return .terminateCancel
    }
}

// A read-only bundle diagnostic is also used by the relocation script. It creates no prefix.
if CommandLine.arguments.contains("--diagnose-launcher") {
    guard Bundle.main.bundleURL.pathExtension == "app", let resources = Bundle.main.resourceURL else {
        fputs("Open the packaged app bundle.\n", stderr); exit(1)
    }
    print("Native launcher started from app bundle.")
    print("Runtime manifest present: \(FileManager.default.fileExists(atPath: resources.appendingPathComponent("runtime-manifest.json").path))")
    print("This check does not verify Wine, Steam, gameplay, Gatekeeper or clean-host portability.")
    exit(0)
}
if CommandLine.arguments.contains("--diagnose") {
    do {
        guard let resources = Bundle.main.resourceURL else { throw LauncherError.message("Missing app resources") }
        let runtime = try Runtime.load(resources: resources)
        print("Runtime integrity: passed; engine \(runtime.engineID)")
        print("Launcher edition: \(LauncherEdition.current.rawValue)")
        print("Default data folder: \(LauncherEdition.current.defaultDataDirectory)")
        print("Rosetta available: \(SystemCheck.rosettaAvailable())")
        exit(0)
    } catch { fputs("Diagnostic: \(error.localizedDescription)\n", stderr); exit(1) }
}
if CommandLine.arguments.contains("--bootstrap-steam") {
    guard let index = CommandLine.arguments.firstIndex(of: "--data-directory"),
          CommandLine.arguments.indices.contains(index + 1), CommandLine.arguments[index + 1].hasPrefix("/") else {
        fputs("Build-only usage: --bootstrap-steam --data-directory ABSOLUTE_PRIVATE_TEST_DIRECTORY\n", stderr); exit(2)
    }
    let root = URL(fileURLWithPath: CommandLine.arguments[index + 1])
    _ = MainActor.assumeIsolated {
        Task { @MainActor in
            do {
                guard let resources = Bundle.main.resourceURL else { throw LauncherError.message("Missing resources") }
                let coordinator = try Coordinator(resources: resources, dataRoot: root, usePrivateHome: true)
                coordinator.changed = { print($0); fflush(stdout) }
                try await coordinator.execute(.open)
                print("Steam launch requested. Client login, game download and gameplay remain unverified.")
                exit(0)
            } catch { fputs("Bootstrap failed: \(error.localizedDescription)\n", stderr); exit(1) }
        }
    }
    RunLoop.main.run()
}
MainActor.assumeIsolated {
    let delegate = AppDelegate()
    let app = NSApplication.shared
    app.delegate = delegate
    app.run()
}
