import Foundation
import LauncherCore

// Foundation-only checks also run on build Macs with CLT and no XCTest/Xcode.
func XCTAssertEqual<T: Equatable>(_ lhs: T, _ rhs: T) { precondition(lhs == rhs, "Expected \(lhs) == \(rhs)") }
func XCTAssertTrue(_ value: Bool) { precondition(value) }
func XCTAssertNil<T>(_ value: T?) { precondition(value == nil) }
func XCTAssertThrowsError<T>(_ expression: @autoclosure () throws -> T) {
    do { _ = try expression() } catch { return }
    fatalError("Expected operation to throw")
}
func XCTAssertNoThrow<T>(_ expression: @autoclosure () throws -> T) {
    do { _ = try expression() } catch { fatalError("Unexpected error: \(error)") }
}

actor TimeZoneRegistryFixture {
    var definitions: [String: String] = [:]
    var corruptBackup = false
    var failSecondDelete = false
    var deletes = 0
    init(corruptBackup: Bool = false, failSecondDelete: Bool = false) {
        self.corruptBackup = corruptBackup; self.failSecondDelete = failSecondDelete
        let value = "88FFFFFF" + String(repeating: "00", count: 40)
        for name in WineTimeZoneRepair.conflicts + [WineTimeZoneRepair.target] {
            definitions[WineTimeZoneRepair.zones + "\\" + name] = value
        }
    }
    func run(_ args: [String]) throws -> String {
        let key = args[2]
        if args[1] == "query", key == WineTimeZoneRepair.info {
            let missing = WineTimeZoneRepair.conflicts.allSatisfy { definitions[WineTimeZoneRepair.zones + "\\" + $0] == nil }
            return "TimeZoneKeyName REG_SZ " + (missing ? WineTimeZoneRepair.target : "Kaliningrad Standard Time")
        }
        if args[1] == "query" {
            guard let value = definitions[key] else { throw LauncherError.message("No such timezone") }
            return "TZI REG_BINARY " + (corruptBackup && key.hasPrefix(WineTimeZoneRepair.backupRoot) ? String(repeating: "00", count: 44) : value)
        }
        if args[1] == "copy" {
            guard let value = definitions[key] else { throw LauncherError.message("Missing source") }
            definitions[args[3]] = value; return "copied"
        }
        if args[1] == "delete" {
            if failSecondDelete && key.hasSuffix("Libya Standard Time") { throw LauncherError.message("Injected deletion failure") }
            definitions.removeValue(forKey: key); deletes += 1; return "deleted"
        }
        throw LauncherError.message("Unexpected command")
    }
    func originalsIntact() -> Bool {
        WineTimeZoneRepair.conflicts.allSatisfy { definitions[WineTimeZoneRepair.zones + "\\" + $0] != nil }
    }
    func deletionCount() -> Int { deletes }
}

final class LauncherCoreChecks {
    var root: URL!
    func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent("rdr2-test-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }
    func tearDownWithError() throws { try FileManager.default.removeItem(at: root) }

    func testResumePreservesLibraryAndBacksUpOldState() throws {
        let paths = DataPaths(root: root)
        try paths.create()
        var session = Session()
        session.library = "/Volumes/Games With Spaces/Steam Library"
        session.stage = .rdr2Downloading
        try paths.save(session)
        let oldBytes = try Data(contentsOf: paths.state)
        session.stage = .error
        try paths.save(session)
        let resumed = try paths.load()
        XCTAssertEqual(resumed.library, session.library)
        XCTAssertEqual(resumed.stage, .error)
        let backups = try FileManager.default.contentsOfDirectory(at: paths.state.deletingLastPathComponent(), includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.contains("backup-") }
        XCTAssertEqual(backups.count, 1)
        XCTAssertEqual(try Data(contentsOf: backups[0]), oldBytes)
    }

    func testCorruptStateIsNotSilentlyReset() throws {
        let paths = DataPaths(root: root)
        try paths.create()
        try Data("not json".utf8).write(to: paths.state)
        XCTAssertThrowsError(try paths.load())
    }

    func testTraversalAndEscapingSymlinksAreRejected() throws {
        XCTAssertThrowsError(try Runtime.safeURL("../escape", root: root))
        XCTAssertThrowsError(try Runtime.safeURL("/usr/bin/true", root: root))
        try FileManager.default.createSymbolicLink(atPath: root.appendingPathComponent("outside").path, withDestinationPath: "/usr/bin/true")
        XCTAssertThrowsError(try Runtime.safeURL("outside", root: root))
        let target = root.appendingPathComponent("valid file")
        try Data().write(to: target)
        try FileManager.default.createSymbolicLink(atPath: root.appendingPathComponent("inside").path, withDestinationPath: "valid file")
        XCTAssertNoThrow(try Runtime.safeURL("inside", root: root))
    }

    func testChangedRuntimeBytesFailIntegrity() throws {
        let file = root.appendingPathComponent("wine")
        try Data("engine bytes".utf8).write(to: file)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: file.path)
        let manifest: [String: Any] = ["engineID": "x64-crossover26.3-r27", "wine": "wine", "baseEnv": [:],
                                     "files": [["path": "wine", "sha256": try Runtime.digest(file)]]]
        try JSONSerialization.data(withJSONObject: manifest).write(to: root.appendingPathComponent("runtime-manifest.json"))
        XCTAssertNoThrow(try Runtime.load(resources: root))
        try Data("altered bytes".utf8).write(to: file)
        XCTAssertThrowsError(try Runtime.load(resources: root))
    }

    func existingEnvironment(_ name: String = "Saved installation") throws -> URL {
        let data = root.appendingPathComponent(name)
        let paths = DataPaths(root: data)
        try paths.create()
        try FileManager.default.createDirectory(at: paths.steam.deletingLastPathComponent(), withIntermediateDirectories: true)
        try Data().write(to: paths.prefix.appendingPathComponent("system.reg"))
        try Data().write(to: paths.steam)
        return data
    }

    func testSelectedEnvironmentSurvivesLauncherRestart() throws {
        let data = try existingEnvironment()
        try FileManager.default.createDirectory(at: data.appendingPathComponent("build-test-home"), withIntermediateDirectories: true)
        let store = EnvironmentSelectionStore(defaultDataRoot: root.appendingPathComponent("Default"))
        try store.save(EnvironmentSelection(existingDataRoot: data))
        let reopened = EnvironmentSelectionStore(defaultDataRoot: root.appendingPathComponent("Default"))
        XCTAssertEqual(try reopened.load()?.url.path, data.resolvingSymlinksInPath().path)
        XCTAssertEqual(try reopened.load()?.usePrivateHome, true)
    }

    func testMissingSelectedEnvironmentDoesNotFallBack() throws {
        let data = try existingEnvironment()
        let store = EnvironmentSelectionStore(defaultDataRoot: root.appendingPathComponent("Default"))
        try store.save(EnvironmentSelection(existingDataRoot: data))
        try FileManager.default.moveItem(at: data, to: root.appendingPathComponent("Disconnected"))
        XCTAssertThrowsError(try store.load())
        XCTAssertTrue(!FileManager.default.fileExists(atPath: root.appendingPathComponent("Default/prefixes/default").path))
    }

    func testSwitchingEnvironmentKeepsExistingFilesAndBackup() throws {
        let data = try existingEnvironment()
        let paths = DataPaths(root: data)
        let game = paths.steam.deletingLastPathComponent().appendingPathComponent("steamapps/common/Red Dead Redemption 2")
        try FileManager.default.createDirectory(at: game, withIntermediateDirectories: true)
        try Data("existing files".utf8).write(to: game.appendingPathComponent("RDR2.exe"))
        let store = EnvironmentSelectionStore(defaultDataRoot: root.appendingPathComponent("Default"))
        try store.save(EnvironmentSelection(existingDataRoot: data))
        try store.save(nil)
        XCTAssertNil(try store.load())
        XCTAssertEqual(try Data(contentsOf: game.appendingPathComponent("RDR2.exe")), Data("existing files".utf8))
        XCTAssertEqual(paths.gameDirectory()?.path, game.path)
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: store.file.deletingLastPathComponent().path).contains { $0.contains("backup-") })
    }

    func testGameFolderIsNotAnExistingEnvironment() throws {
        XCTAssertThrowsError(try EnvironmentSelection(existingDataRoot: root))
    }

    func testRockstarServiceRequiresActualRunningState() {
        XCTAssertTrue(RockstarService.isRunning("SERVICE_NAME: Rockstar Service\n STATE : 4 RUNNING\n WIN32_EXIT_CODE : 0"))
        XCTAssertTrue(!RockstarService.isRunning("STATE : 1 STOPPED\n WIN32_EXIT_CODE : 4"))
        XCTAssertTrue(!RockstarService.isRunning("STATE : 2 START_PENDING"))
    }

    func testBackgroundChildDoesNotHoldCommandCaptureOpen() async throws {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-c", "(/bin/sleep 6) & printf 'STATE : 4 RUNNING'"]
        let started = Date()
        let result = try await ProcessRunner.run(process, captureIn: root)
        XCTAssertEqual(result.status, 0)
        XCTAssertTrue(RockstarService.isRunning(result.output))
        XCTAssertTrue(Date().timeIntervalSince(started) < 4)
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: root.path).isEmpty)
    }

    func testTimezoneCorrectionIsHostSpecificAndPreservesBackups() async throws {
        XCTAssertTrue(WineTimeZoneRepair.needed(hostZone: "Africa/Johannesburg", reported: "Kaliningrad Standard Time"))
        XCTAssertTrue(!WineTimeZoneRepair.needed(hostZone: "Europe/Kaliningrad", reported: "Kaliningrad Standard Time"))
        let registry = TimeZoneRegistryFixture()
        let key = WineTimeZoneRepair.backupRoot + "\\test-repair"
        try await WineTimeZoneRepair.apply(backupKey: key, year: 2026) { try await registry.run($0) }
        XCTAssertEqual(await registry.deletionCount(), 3)
        for name in WineTimeZoneRepair.conflicts {
            XCTAssertTrue(try await registry.run(["reg", "query", key + "\\" + name, "/v", "TZI"]).contains("REG_BINARY"))
        }
    }

    func testTimezoneCorruptBackupCannotRemoveDefinitions() async throws {
        let registry = TimeZoneRegistryFixture(corruptBackup: true)
        do {
            try await WineTimeZoneRepair.apply(backupKey: WineTimeZoneRepair.backupRoot + "\\test-repair", year: 2026) { try await registry.run($0) }
            fatalError("Corrupt backup must reject the change")
        } catch { }
        XCTAssertEqual(await registry.deletionCount(), 0)
        XCTAssertTrue(await registry.originalsIntact())
    }

    func testTimezonePartialFailureRestoresOriginalDefinitions() async throws {
        let registry = TimeZoneRegistryFixture(failSecondDelete: true)
        do {
            try await WineTimeZoneRepair.apply(backupKey: WineTimeZoneRepair.backupRoot + "\\test-repair", year: 2026) { try await registry.run($0) }
            fatalError("Injected failure must abort")
        } catch { }
        XCTAssertTrue(await registry.originalsIntact())
    }

    func testTimezoneInterruptedMoveCanResumeWithoutPrefixReset() async throws {
        let registry = TimeZoneRegistryFixture()
        let key = WineTimeZoneRepair.backupRoot + "\\interrupted-repair"
        for name in WineTimeZoneRepair.conflicts {
            _ = try await registry.run(["reg", "copy", WineTimeZoneRepair.zones + "\\" + name, key + "\\" + name, "/s", "/f"])
        }
        _ = try await registry.run(["reg", "delete", WineTimeZoneRepair.zones + "\\Kaliningrad Standard Time", "/f"])
        try await WineTimeZoneRepair.restoreMissing(backupKey: key) { try await registry.run($0) }
        XCTAssertTrue(await registry.originalsIntact())
    }

    func testSteamActionsKeepEntitlementChain() {
        XCTAssertEqual(SteamAction.play.arguments, ["-applaunch", "1174180"])
        XCTAssertEqual(SteamAction.install.arguments, ["steam://install/1174180"])
        XCTAssertEqual(SteamAction.verify.arguments, ["steam://validate/1174180"])
    }

    func testRuntimeEnvironmentIsPrivateAndRelocates() throws {
        let json = #"{"engineID":"x64-crossover26.3-r27","wine":"runtime/engine/bin/wine","files":[],"baseEnv":{"DYLD_FALLBACK_LIBRARY_PATH":"${frameworks}","WINEDEBUG":"fixme-all"}}"#
        let runtime = try JSONDecoder().decode(Runtime.self, from: Data(json.utf8))
        let env = runtime.environment(resources: root, paths: DataPaths(root: root.appendingPathComponent("User Data")))
        XCTAssertEqual(env["DYLD_FALLBACK_LIBRARY_PATH"], root.appendingPathComponent("runtime/frameworks").path)
        XCTAssertEqual(env["WINEDEBUG"], "-all")
        XCTAssertEqual(env["WINEMSYNC"], "0")
        XCTAssertEqual(env["PATH"], "/usr/bin:/bin:/usr/sbin:/sbin")
        XCTAssertTrue(env["WINEPREFIX"]!.contains("User Data"))
        XCTAssertNil(env["DYLD_LIBRARY_PATH"])
        XCTAssertEqual(env["GST_PLUGIN_SYSTEM_PATH_1_0"], "")
        XCTAssertTrue(env["GST_REGISTRY_1_0"]!.hasPrefix(root.path))
    }

    func testExperimentalEditionsKeepSelectionAndVariablesSeparate() throws {
        let normal = DataPaths(root: root.appendingPathComponent(LauncherEdition.standard.defaultDataDirectory))
        let control = DataPaths(root: root.appendingPathComponent(LauncherEdition.moltenvkControl.defaultDataDirectory))
        let candidate = DataPaths(root: root.appendingPathComponent(LauncherEdition.moltenvkCandidate.defaultDataDirectory))
        for paths in [normal, control, candidate] { try paths.create() }
        var original = Session(); original.library = "/original/game/library"
        try normal.save(original)
        let saved = try Data(contentsOf: normal.state)
        var test = Session(); test.library = candidate.root.appendingPathComponent("SteamLibrary").path
        try candidate.save(test)
        try EnvironmentSelectionStore(defaultDataRoot: candidate.root).save(nil)
        XCTAssertEqual(try Data(contentsOf: normal.state), saved)
        XCTAssertTrue(!FileManager.default.fileExists(atPath: control.state.path))
        let json = #"{"engineID":"x64-crossover26.3-r27","wine":"runtime/engine/bin/wine","files":[],"baseEnv":{}}"#
        let runtime = try JSONDecoder().decode(Runtime.self, from: Data(json.utf8))
        let normalEnv = runtime.environment(resources: root, paths: normal, edition: .standard)
        let controlEnv = runtime.environment(resources: root, paths: control, edition: .moltenvkControl)
        let patched = runtime.environment(resources: root, paths: normal, edition: .patched)
        let enabled = runtime.environment(resources: root, paths: candidate, edition: .moltenvkCandidate)
        let disabled = runtime.environment(resources: root, paths: candidate, edition: .moltenvkCandidate, treeFixEnabled: false)
        XCTAssertNil(normalEnv["RDR2_MVK_DEDICATED_BUFFER_NO_HEAP"])
        XCTAssertNil(controlEnv["RDR2_MVK_DEDICATED_BUFFER_NO_HEAP"])
        XCTAssertEqual(LauncherEdition.patched.defaultDataDirectory, LauncherEdition.standard.defaultDataDirectory)
        XCTAssertTrue(!LauncherEdition.patched.isExperimental)
        XCTAssertTrue(LauncherEdition.moltenvkCandidate.isExperimental)
        XCTAssertTrue(LauncherEdition.moltenvkControl.isExperimental)
        XCTAssertEqual(patched["RDR2_MVK_DEDICATED_BUFFER_NO_HEAP"], "1")
        XCTAssertEqual(patched["RDR2_MVK_ALLOCATION_MARKER_FILE"], normal.root.appendingPathComponent("state/tree-allocation-events.log").path)
        XCTAssertEqual(enabled["RDR2_MVK_DEDICATED_BUFFER_NO_HEAP"], "1")
        XCTAssertNil(disabled["RDR2_MVK_DEDICATED_BUFFER_NO_HEAP"])
        XCTAssertEqual(enabled["RDR2_MVK_ALLOCATION_MARKER_FILE"], candidate.root.appendingPathComponent("state/tree-allocation-events.log").path)
    }
}

@main struct CheckRunner {
    static func main() async throws {
        let checks = LauncherCoreChecks()
        let tests: [(String, () throws -> Void)] = [
            ("persisted state and backup", checks.testResumePreservesLibraryAndBacksUpOldState),
            ("selected environment persists", checks.testSelectedEnvironmentSurvivesLauncherRestart),
            ("missing environment fails safely", checks.testMissingSelectedEnvironmentDoesNotFallBack),
            ("environment switching preserves game", checks.testSwitchingEnvironmentKeepsExistingFilesAndBackup),
            ("game folder selection is distinct", checks.testGameFolderIsNotAnExistingEnvironment),
            ("Rockstar service running state", checks.testRockstarServiceRequiresActualRunningState),
            ("corrupt state", checks.testCorruptStateIsNotSilentlyReset),
            ("runtime path containment", checks.testTraversalAndEscapingSymlinksAreRejected),
            ("runtime integrity", checks.testChangedRuntimeBytesFailIntegrity),
            ("Steam entitlement route", checks.testSteamActionsKeepEntitlementChain),
            ("relocated process environment", checks.testRuntimeEnvironmentIsPrivateAndRelocates),
            ("experimental edition isolation", checks.testExperimentalEditionsKeepSelectionAndVariablesSeparate)
        ]
        for (name, test) in tests {
            try checks.setUpWithError()
            do { try test() } catch { try? checks.tearDownWithError(); throw error }
            try checks.tearDownWithError()
            print("PASS: \(name)")
        }
        try checks.setUpWithError()
        try await checks.testBackgroundChildDoesNotHoldCommandCaptureOpen()
        try checks.tearDownWithError()
        print("PASS: background child cannot hold command capture open")
        try await checks.testTimezoneCorrectionIsHostSpecificAndPreservesBackups()
        try await checks.testTimezoneCorruptBackupCannotRemoveDefinitions()
        try await checks.testTimezonePartialFailureRestoresOriginalDefinitions()
        try await checks.testTimezoneInterruptedMoveCanResumeWithoutPrefixReset()
        print("PASS: timezone applicability, verified backups and rollback")
        print("17 Swift core checks passed")
    }
}
