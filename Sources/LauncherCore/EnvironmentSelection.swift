import Foundation

public struct EnvironmentSelection: Codable, Equatable {
    public let dataRoot: String
    public let usePrivateHome: Bool
    public var url: URL { URL(fileURLWithPath: dataRoot) }

    public init(existingDataRoot: URL) throws {
        let root = existingDataRoot.standardizedFileURL.resolvingSymlinksInPath()
        let paths = DataPaths(root: root)
        guard !root.pathComponents.contains(where: { $0.hasSuffix(".app") }),
              FileManager.default.fileExists(atPath: paths.prefix.appendingPathComponent("system.reg").path),
              FileManager.default.fileExists(atPath: paths.steam.path) else {
            throw LauncherError.message("Choose the existing launcher data folder containing prefixes/default and Windows Steam. Selecting only a game folder does not select its Steam environment.")
        }
        dataRoot = root.path
        usePrivateHome = FileManager.default.fileExists(atPath: root.appendingPathComponent("build-test-home").path)
    }
}

public struct EnvironmentSelectionStore {
    private struct Settings: Codable { var environment: EnvironmentSelection? }
    public let file: URL
    public init(defaultDataRoot: URL) {
        file = defaultDataRoot.appendingPathComponent("state/selected-environment.json")
    }
    public func load() throws -> EnvironmentSelection? {
        guard FileManager.default.fileExists(atPath: file.path) else { return nil }
        guard let saved = try JSONDecoder().decode(Settings.self, from: Data(contentsOf: file)).environment else { return nil }
        // An unavailable selected drive/folder must never silently create a fresh Steam prefix.
        do { _ = try EnvironmentSelection(existingDataRoot: saved.url) }
        catch { throw LauncherError.message("The selected Steam environment is unavailable: \(saved.dataRoot). Reconnect its drive or use ‘Use existing environment’. No replacement prefix has been created.") }
        return saved
    }
    public func save(_ selection: EnvironmentSelection?) throws {
        if let selection { _ = try EnvironmentSelection(existingDataRoot: selection.url) }
        try FileManager.default.createDirectory(at: file.deletingLastPathComponent(), withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        if FileManager.default.fileExists(atPath: file.path) {
            try FileManager.default.copyItem(at: file, to: file.appendingPathExtension(DataPaths.backupSuffix()))
        }
        try JSONEncoder().encode(Settings(environment: selection)).write(to: file, options: .atomic)
    }
}
