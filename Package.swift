// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "RDR2Launcher", platforms: [.macOS(.v14)],
    products: [.executable(name: "RDR2Launcher", targets: ["RDR2Launcher"])],
    targets: [
        .target(name: "LauncherCore"),
        .executableTarget(name: "RDR2Launcher", dependencies: ["LauncherCore"]),
        .executableTarget(name: "LauncherCoreChecks", dependencies: ["LauncherCore"], path: "Tests/LauncherCoreTests")
    ])
