import Foundation

public enum LauncherEdition: String {
    case standard
    case moltenvkControl = "moltenvk-control"
    case moltenvkCandidate = "moltenvk-candidate"

    public static var current: LauncherEdition {
        LauncherEdition(rawValue: Bundle.main.object(forInfoDictionaryKey: "RDR2LauncherEdition") as? String ?? "") ?? .standard
    }

    public var defaultDataDirectory: String {
        switch self {
        case .standard: return "RDR2Launcher"
        case .moltenvkControl: return "RDR2Launcher-MoltenVK-Control"
        case .moltenvkCandidate: return "RDR2Launcher-MoltenVK-Candidate"
        }
    }

    public var displayName: String {
        switch self {
        case .standard: return "RDR2 Launcher"
        case .moltenvkControl: return "RDR2 MoltenVK Control"
        case .moltenvkCandidate:
            return Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String ?? "RDR2 Tree Experiment"
        }
    }

    public var subtitle: String {
        switch self {
        case .standard: return "Steam edition · Story Mode · Vulkan / patched MoltenVK\nSign in only inside Steam and Rockstar."
        case .moltenvkControl: return "Baseline renderer comparison\nUse the same save and graphics settings for each comparison."
        case .moltenvkCandidate:
            return Bundle.main.object(forInfoDictionaryKey: "RDR2LauncherSubtitle") as? String ??
                "Experimental tree rendering\nCompare trees, water, shadows and performance with the control build."
        }
    }
}
