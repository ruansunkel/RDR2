import Foundation

public enum Stage: String, Codable {
    case missingRuntime = "missing_runtime", missingRosetta = "missing_rosetta"
    case needsPrefix = "needs_prefix", needsSteam = "needs_steam", steamUpdating = "steam_updating"
    case needsSteamLogin = "needs_steam_login", needsRDR2Install = "needs_rdr2_install"
    case rdr2Downloading = "rdr2_downloading", needsRockstarLogin = "needs_rockstar_login"
    case launching, error
    // Steam and Rockstar own readiness/authentication. Never infer gameplay from an ACF file.
}

public struct Session: Codable {
    public var stage: Stage = .needsPrefix
    public var library: String?
    public var updated = Date()
    public init() {}
}

public struct DataPaths {
    public let root: URL
    public var prefix: URL { root.appendingPathComponent("prefixes/default") }
    public var logs: URL { root.appendingPathComponent("logs") }
    public var downloads: URL { root.appendingPathComponent("downloads") }
    public var state: URL { root.appendingPathComponent("state/session.json") }
    public var steam: URL { prefix.appendingPathComponent("drive_c/Program Files (x86)/Steam/steam.exe") }
    public init(root: URL) { self.root = root }
    public static func standard() throws -> DataPaths {
        let support = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                 appropriateFor: nil, create: true)
        return DataPaths(root: support.appendingPathComponent("RDR2Launcher"))
    }
    public func create() throws {
        for dir in [root, logs, downloads, state.deletingLastPathComponent(), prefix.deletingLastPathComponent()] {
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true,
                                                    attributes: [.posixPermissions: 0o700])
        }
    }
    public func load() throws -> Session {
        guard FileManager.default.fileExists(atPath: state.path) else { return Session() }
        return try JSONDecoder().decode(Session.self, from: Data(contentsOf: state))
    }
    public func save(_ session: Session) throws {
        var value = session
        value.updated = Date()
        if FileManager.default.fileExists(atPath: state.path) {
            let backup = state.appendingPathExtension(Self.backupSuffix())
            try FileManager.default.copyItem(at: state, to: backup)
        }
        try JSONEncoder().encode(value).write(to: state, options: .atomic)
    }
    public static func backupSuffix() -> String {
        "backup-\(Int(Date().timeIntervalSince1970))-\(UUID().uuidString)"
    }
}

public enum LauncherError: LocalizedError {
    case message(String)
    public var errorDescription: String? { if case let .message(s) = self { return s }; return nil }
}

public enum SteamAction {
    case open, install, play, verify
    public var arguments: [String] {
        switch self {
        case .open: return []
        case .install: return ["steam://install/1174180"]
        case .play: return ["-applaunch", "1174180"]
        case .verify: return ["steam://validate/1174180"]
        }
    }
}
