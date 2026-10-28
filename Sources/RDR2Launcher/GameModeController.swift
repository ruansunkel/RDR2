import AppKit
import ApplicationServices
import CoreServices
import Darwin
import LauncherCore

/// Game Mode itself belongs to macOS. This controller registers Wine's game
/// bundle and optionally enters native full screen on the game's own window.
@MainActor final class GameModeController {
    private let helper: URL
    private let executable: URL
    private var timer: Timer?
    private var completed = Set<pid_t>()
    var changed: ((String) -> Void)?

    init(resources: URL) {
        helper = resources.appendingPathComponent("runtime/RDR2WineGame.app")
        executable = helper.appendingPathComponent("Contents/MacOS/wine").resolvingSymlinksInPath()
    }

    func start() {
        guard FileManager.default.isExecutableFile(atPath: executable.path) else {
            changed?("Game Mode: rebuild with the game-enabled Wine loader.")
            return
        }
        // Register the nested game bundle after relocation, before Wine starts.
        let registration = LSRegisterURL(helper as CFURL, true)
        guard registration == noErr else {
            changed?("Game Mode: could not register the game helper (\(registration)).")
            return
        }
        reportReadiness()
        guard timer == nil else { return }
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tick() }
        }
    }

    func configure() {
        let alert = NSAlert()
        alert.messageText = "Game Mode"
        alert.informativeText = "macOS enables Game Mode when RDR2 is focused and full screen. You can enter full screen with the game window’s green button.\n\nAutomatic full screen needs Accessibility access for this launcher. It applies once to each RDR2 session; you can exit full screen afterward. Check Game Mode with Command–Esc → Settings."
        alert.addButton(withTitle: "Enable automatic full screen")
        alert.addButton(withTitle: "Use manual full screen")
        alert.addButton(withTitle: "Cancel")
        switch alert.runModal() {
        case .alertFirstButtonReturn:
            UserDefaults.standard.set(true, forKey: "automaticGameFullScreen")
            let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
            _ = AXIsProcessTrustedWithOptions(options)
            start()
        case .alertSecondButtonReturn:
            UserDefaults.standard.set(false, forKey: "automaticGameFullScreen")
            reportReadiness()
        default: break
        }
    }

    private func reportReadiness() {
        if UserDefaults.standard.bool(forKey: "automaticGameFullScreen") {
            changed?(AXIsProcessTrusted()
                ? "Game Mode: automatic full screen ready; macOS controls activation."
                : "Game Mode: allow Accessibility for automatic full screen, or enter it manually.")
        } else {
            changed?("Game Mode: enter full screen in RDR2, or enable automatic full screen…")
        }
    }

    private func tick() {
        completed = completed.filter { NSRunningApplication(processIdentifier: $0) != nil }
        guard UserDefaults.standard.bool(forKey: "automaticGameFullScreen"), AXIsProcessTrusted(),
              let app = NSWorkspace.shared.frontmostApplication,
              !completed.contains(app.processIdentifier),
              app.executableURL?.resolvingSymlinksInPath() == executable,
              let arguments = GameProcess.arguments(pid: app.processIdentifier),
              GameProcess.isRDR2(arguments: arguments) else { return }
        let application = AXUIElementCreateApplication(app.processIdentifier)
        AXUIElementSetMessagingTimeout(application, 0.3)
        var value: CFTypeRef?
        guard AXUIElementCopyAttributeValue(application, kAXWindowsAttribute as CFString, &value) == .success,
              let windows = value as? [AXUIElement] else { return }
        for window in windows {
            var title: CFTypeRef?
            guard AXUIElementCopyAttributeValue(window, kAXTitleAttribute as CFString, &title) == .success,
                  let name = title as? String,
                  ["red dead redemption 2", "rdr2"].contains(name.lowercased().trimmingCharacters(in: .whitespacesAndNewlines))
            else { continue }
            let attribute = "AXFullScreen" as CFString
            var fullScreen: CFTypeRef?
            if AXUIElementCopyAttributeValue(window, attribute, &fullScreen) == .success,
               (fullScreen as? Bool) == true {
                completed.insert(app.processIdentifier)
                return
            }
            var settable = DarwinBoolean(false)
            guard AXUIElementIsAttributeSettable(window, attribute, &settable) == .success, settable.boolValue,
                  AXUIElementSetAttributeValue(window, attribute, kCFBooleanTrue) == .success else { continue }
            completed.insert(app.processIdentifier)
            changed?("RDR2 full screen requested. Check Game Mode with Command–Esc → Settings.")
            return
        }
    }
}
