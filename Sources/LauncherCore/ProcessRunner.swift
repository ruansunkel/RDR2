import Foundation

public struct ProcessResult {
    public let status: Int32
    public let output: String
}

public enum ProcessRunner {
    public static func run(_ process: Process, captureIn directory: URL? = nil) async throws -> ProcessResult {
        let file = directory?.appendingPathComponent(".command-\(UUID().uuidString)")
        var writer: FileHandle?
        if let file {
            guard FileManager.default.createFile(atPath: file.path, contents: nil, attributes: [.posixPermissions: 0o600]) else {
                throw LauncherError.message("Could not create private command output file.")
            }
            writer = try FileHandle(forWritingTo: file)
            process.standardOutput = writer
        } else { process.standardOutput = FileHandle.nullDevice }
        process.standardError = FileHandle.nullDevice
        defer {
            try? writer?.close()
            if let file { try? FileManager.default.removeItem(at: file) }
        }
        let status: Int32 = try await withCheckedThrowingContinuation { continuation in
            process.terminationHandler = { child in continuation.resume(returning: child.terminationStatus) }
            do { try process.run() }
            catch { process.terminationHandler = nil; continuation.resume(throwing: error) }
        }
        try writer?.close()
        // Snapshot after the command exits. A Wine desktop/service child can
        // keep inherited pipe descriptors open indefinitely; EOF is not completion.
        let bytes = try file.map { try Data(contentsOf: $0) } ?? Data()
        return ProcessResult(status: status, output: String(decoding: bytes, as: UTF8.self))
    }
}
