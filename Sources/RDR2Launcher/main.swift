import AppKit
import LauncherCore

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var coordinator: Coordinator?
    let label = NSTextField(wrappingLabelWithString: "Checking launcher…")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let menu = NSMenu()
        let appItem = NSMenuItem(); menu.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        appMenu.addItem(withTitle: "Quit RDR2Launcher", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        NSApp.mainMenu = menu
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 620, height: 370),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "RDR2 Launcher — Development Build"
        window.center()
        let title = NSTextField(labelWithString: "Red Dead Redemption 2")
        title.font = .boldSystemFont(ofSize: 24)
        let subtitle = NSTextField(wrappingLabelWithString: "Steam edition · Story Mode · Vulkan / patched MoltenVK\nSign in only inside Steam and Rockstar. Gameplay and clean-host portability require validation.")
        label.font = .systemFont(ofSize: 14)
        label.setContentHuggingPriority(.defaultLow, for: .vertical)
        let row1 = NSStackView(views: [button("Install & Play", #selector(install)), button("Play", #selector(play)), button("Open Steam", #selector(openSteam))])
        let row2 = NSStackView(views: [button("Repair", #selector(repair)), button("Choose game folder", #selector(choose)), button("View logs", #selector(logs)), button("Rosetta help", #selector(rosettaHelp)), button("Quit", #selector(quit))])
        let stack = NSStackView(views: [title, subtitle, label, row1, row2])
        stack.orientation = .vertical; stack.alignment = .leading; stack.spacing = 18
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 24),
            stack.bottomAnchor.constraint(equalTo: window.contentView!.bottomAnchor, constant: -24)
        ])
        do {
            guard let resources = Bundle.main.resourceURL else { throw LauncherError.message("Open the packaged .app bundle.") }
            coordinator = try Coordinator(resources: resources)
            coordinator?.changed = { [weak self] text in self?.label.stringValue = text }
            if !FileManager.default.fileExists(atPath: resources.appendingPathComponent("runtime-manifest.json").path) {
                label.stringValue = "Launcher-only preview: the verified Wine engine is not bundled. See BUILD.md to stage the runtime. No game launch has been verified."
            } else {
                label.stringValue = "Choose a game folder, then Install & Play. Steam confirms ownership and download completion; press Play when it is ready."
            }
        } catch { label.stringValue = error.localizedDescription }
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
    }
    func button(_ title: String, _ action: Selector) -> NSButton { NSButton(title: title, target: self, action: action) }
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
        print("Rosetta available: \(SystemCheck.rosettaAvailable())")
        exit(0)
    } catch { fputs("Diagnostic: \(error.localizedDescription)\n", stderr); exit(1) }
}
MainActor.assumeIsolated {
    let delegate = AppDelegate()
    let app = NSApplication.shared
    app.delegate = delegate
    app.run()
}
