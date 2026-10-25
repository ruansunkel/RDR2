import Foundation

/// Wine 11 matches offsets to the first Windows zone. On Johannesburg that can
/// select Kaliningrad. Preserve the three conflicting definitions outside the
/// matching list, with exact-value verification and rollback on failure.
public enum WineTimeZoneRepair {
    public static let zones = #"HKLM\Software\Microsoft\Windows NT\CurrentVersion\Time Zones"#
    public static let info = #"HKLM\System\CurrentControlSet\Control\TimeZoneInformation"#
    public static let backupRoot = #"HKLM\Software\RDR2Launcher\TimezoneBackups"#
    public static let target = "South Africa Standard Time"
    public static let conflicts = ["Kaliningrad Standard Time", "Libya Standard Time", "Namibia Standard Time"]

    public static func needed(hostZone: String, reported: String) -> Bool {
        hostZone == "Africa/Johannesburg" && conflicts.contains(where: reported.contains)
    }

    public static func binaryValue(_ reply: String) throws -> [UInt8] {
        guard let marker = reply.range(of: "REG_BINARY") else { throw LauncherError.message("Missing timezone definition.") }
        let hex = reply[marker.upperBound...].filter { !$0.isWhitespace }
        guard hex.count == 88 else { throw LauncherError.message("Unexpected timezone definition size.") }
        var bytes: [UInt8] = []
        var index = hex.startIndex
        while index < hex.endIndex {
            let next = hex.index(index, offsetBy: 2)
            guard let byte = UInt8(hex[index..<next], radix: 16) else { throw LauncherError.message("Invalid timezone definition.") }
            bytes.append(byte); index = next
        }
        return bytes
    }

    private static func isFixedUTCPlusTwo(_ bytes: [UInt8]) -> Bool {
        bytes.count == 44 && Array(bytes[0..<4]) == [0x88, 0xff, 0xff, 0xff] &&
        bytes[14] == 0 && bytes[15] == 0 && bytes[30] == 0 && bytes[31] == 0
    }

    private static func validateBackupKey(_ backupKey: String) throws {
        let suffix = backupKey.dropFirst(backupRoot.count + 1)
        guard backupKey.hasPrefix(backupRoot + "\\"), !suffix.isEmpty,
              suffix.allSatisfy({ $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-") }) else {
            throw LauncherError.message("Invalid timezone backup destination.")
        }
    }

    public static func restoreMissing(backupKey: String, run: ([String]) async throws -> String) async throws {
        try validateBackupKey(backupKey)
        for name in conflicts {
            let source = zones + "\\" + name
            if (try? await run(["reg", "query", source, "/v", "TZI"])) != nil { continue }
            let backup = backupKey + "\\" + name
            _ = try binaryValue(try await run(["reg", "query", backup, "/v", "TZI"]))
            _ = try await run(["reg", "copy", backup, source, "/s", "/f"])
        }
    }

    public static func apply(backupKey: String, year: Int,
                             run: ([String]) async throws -> String) async throws {
        try validateBackupKey(backupKey)
        let targetValue = try binaryValue(try await run(["reg", "query", zones + "\\" + target, "/v", "TZI"]))
        guard isFixedUTCPlusTwo(targetValue) else { throw LauncherError.message("The South Africa timezone definition is unexpected; nothing was changed.") }
        // Verify applicability before making any change. Use the same year-specific
        // definition/fallback that this Wine engine uses.
        for name in conflicts {
            let base = try binaryValue(try await run(["reg", "query", zones + "\\" + name, "/v", "TZI"]))
            let dynamic = try? await run(["reg", "query", zones + "\\" + name + "\\Dynamic DST", "/v", String(year)])
            let effective = try dynamic.map(binaryValue) ?? base
            guard isFixedUTCPlusTwo(effective) else { throw LauncherError.message("A timezone definition differs from the verified workaround; nothing was changed.") }
        }
        var moved: [String] = []
        do {
            for name in conflicts {
                let source = zones + "\\" + name, backup = backupKey + "\\" + name
                let original = try binaryValue(try await run(["reg", "query", source, "/v", "TZI"]))
                _ = try await run(["reg", "copy", source, backup, "/s", "/f"])
                let copied = try binaryValue(try await run(["reg", "query", backup, "/v", "TZI"]))
                guard copied == original else { throw LauncherError.message("Timezone backup verification failed.") }
            }
            for name in conflicts {
                _ = try await run(["reg", "delete", zones + "\\" + name, "/f"])
                moved.append(name)
            }
            let selected = try await run(["reg", "query", info, "/v", "TimeZoneKeyName"])
            guard selected.contains(target) else { throw LauncherError.message("Wine did not select the South Africa timezone.") }
        } catch {
            var restored = true
            for name in moved {
                do { _ = try await run(["reg", "copy", backupKey + "\\" + name, zones + "\\" + name, "/s", "/f"]) }
                catch { restored = false }
            }
            if !restored { throw LauncherError.message("Timezone correction failed; automatic restore was incomplete. Original definitions remain at \(backupKey). Game files were not changed.") }
            throw error
        }
    }
}
