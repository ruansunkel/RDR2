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
    }
}

@main struct CheckRunner {
    static func main() throws {
        let checks = LauncherCoreChecks()
        let tests: [(String, () throws -> Void)] = [
            ("persisted state and backup", checks.testResumePreservesLibraryAndBacksUpOldState),
            ("corrupt state", checks.testCorruptStateIsNotSilentlyReset),
            ("runtime path containment", checks.testTraversalAndEscapingSymlinksAreRejected),
            ("runtime integrity", checks.testChangedRuntimeBytesFailIntegrity),
            ("Steam entitlement route", checks.testSteamActionsKeepEntitlementChain),
            ("relocated process environment", checks.testRuntimeEnvironmentIsPrivateAndRelocates)
        ]
        for (name, test) in tests {
            try checks.setUpWithError()
            do { try test() } catch { try? checks.tearDownWithError(); throw error }
            try checks.tearDownWithError()
            print("PASS: \(name)")
        }
        print("6 Swift core checks passed")
    }
}
