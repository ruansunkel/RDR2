import Foundation
import Darwin

public enum GameProcess {
    public static func arguments(pid: pid_t) -> [String]? {
        var mib: [Int32] = [CTL_KERN, KERN_PROCARGS2, pid]
        var size = 0
        guard sysctl(&mib, u_int(mib.count), nil, &size, nil, 0) == 0, size > MemoryLayout<Int32>.size else { return nil }
        var data = [UInt8](repeating: 0, count: size)
        guard sysctl(&mib, u_int(mib.count), &data, &size, nil, 0) == 0 else { return nil }
        let argc = data.withUnsafeBytes { $0.loadUnaligned(as: Int32.self) }
        guard argc > 0, argc < 4096 else { return nil }
        var offset = MemoryLayout<Int32>.size
        // Skip the kernel executable path and padding. Read argv only, never env.
        while offset < size && data[offset] != 0 { offset += 1 }
        while offset < size && data[offset] == 0 { offset += 1 }
        var result: [String] = []
        for _ in 0..<argc {
            guard offset < size else { return nil }
            let start = offset
            while offset < size && data[offset] != 0 { offset += 1 }
            result.append(String(decoding: data[start..<offset], as: UTF8.self))
            offset += 1
        }
        return result
    }

    /// Ignore launcher arguments that mention RDR2 later in their command line.
    /// The first Windows executable must be the game itself.
    public static func isRDR2(arguments: [String]) -> Bool {
        for argument in arguments {
            let name = argument.replacingOccurrences(of: "\\", with: "/")
                .split(separator: "/").last.map(String.init)?.lowercased() ?? ""
            if name.hasSuffix(".exe") { return name == "rdr2.exe" }
        }
        return false
    }
}
