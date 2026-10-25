import Foundation
import CryptoKit

public struct Runtime: Decodable {
    public struct FileRecord: Decodable {
        public var path: String
        public var sha256: String?
        public var symlink: String?
    }
    public var engineID: String
    public var wine: String
    public var baseEnv: [String: String]
    public var files: [FileRecord]

    public static func load(resources: URL) throws -> Runtime {
        let runtime = try JSONDecoder().decode(Runtime.self, from: Data(contentsOf:
            resources.appendingPathComponent("runtime-manifest.json")))
        guard runtime.engineID == "x64-crossover26.3-r27", !runtime.files.isEmpty else {
            throw LauncherError.message("The bundled runtime is incomplete or has an unsupported engine.")
        }
        for item in runtime.files {
            let url = try safeURL(item.path, root: resources)
            if let target = item.symlink {
                guard try FileManager.default.destinationOfSymbolicLink(atPath: url.path) == target else {
                    throw LauncherError.message("A runtime link has changed: \(item.path)")
                }
            } else if let expected = item.sha256 {
                let actual = try digest(url)
                guard actual == expected else { throw LauncherError.message("Runtime checksum mismatch: \(item.path)") }
            } else { throw LauncherError.message("Missing runtime checksum: \(item.path)") }
        }
        let binary = try safeURL(runtime.wine, root: resources)
        guard FileManager.default.isExecutableFile(atPath: binary.path) else {
            throw LauncherError.message("The bundled Wine loader is missing or not executable.")
        }
        return runtime
    }

    public static func digest(_ url: URL) throws -> String {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        var hash = SHA256()
        while let bytes = try handle.read(upToCount: 1024 * 1024), !bytes.isEmpty { hash.update(data: bytes) }
        return hash.finalize().map { String(format: "%02x", $0) }.joined()
    }

    public static func safeURL(_ path: String, root: URL) throws -> URL {
        guard !path.isEmpty, !path.hasPrefix("/"), !path.split(separator: "/").contains("..") else {
            throw LauncherError.message("Invalid bundle-relative runtime path.")
        }
        let result = root.appendingPathComponent(path)
        let base = root.resolvingSymlinksInPath().standardizedFileURL.path + "/"
        guard result.resolvingSymlinksInPath().standardizedFileURL.path.hasPrefix(base) else {
            throw LauncherError.message("Runtime symlink leaves the app bundle.")
        }
        return result
    }

    public func environment(resources: URL, paths: DataPaths) -> [String: String] {
        // Deliberately do not inherit DYLD_*, WINE*, tokens or the developer's PATH.
        var env = ["PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": FileManager.default.homeDirectoryForCurrentUser.path,
                   "TMPDIR": NSTemporaryDirectory(), "WINEPREFIX": paths.prefix.path,
                   "WINEDEBUG": "-all", "WINEMSYNC": "0", "WINEESYNC": "0",
                   "WINEDLLOVERRIDES": "winemenubuilder.exe=d",
                   "WINEDLLPATH_PREPEND": resources.appendingPathComponent("runtime/renderers/dxmt/wine").path]
        let fw = resources.appendingPathComponent("runtime/frameworks").path
        for (key, value) in baseEnv where key != "WINEDEBUG" {
            env[key] = value.replacingOccurrences(of: "${frameworks}", with: fw)
        }
        env["GST_PLUGIN_SYSTEM_PATH_1_0"] = ""
        env["GST_PLUGIN_SCANNER"] = fw + "/GStreamer.framework/Versions/1.0/libexec/gstreamer-1.0/gst-plugin-scanner"
        env["GST_REGISTRY_1_0"] = paths.root.appendingPathComponent("state/gstreamer-registry.bin").path
        // r27's Wine bridge finds MoltenVK through engine/lib relative symlinks;
        // no guessed ICD or DYLD_LIBRARY_PATH setting is necessary.
        return env
    }
}

public enum SystemCheck {
    public static func rosettaAvailable() -> Bool {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/arch")
        p.arguments = ["-x86_64", "/usr/bin/true"]
        p.standardOutput = FileHandle.nullDevice; p.standardError = FileHandle.nullDevice
        do { try p.run(); p.waitUntilExit(); return p.terminationStatus == 0 } catch { return false }
    }
    public static func availableBytes(at url: URL) throws -> Int64 {
        let attrs = try FileManager.default.attributesOfFileSystem(forPath: url.path)
        guard let value = attrs[.systemFreeSize] as? NSNumber else {
            throw LauncherError.message("Could not determine available disk space.")
        }
        return value.int64Value
    }
}
