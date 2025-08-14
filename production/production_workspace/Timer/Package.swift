// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Timer",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Timer",
            targets: ["Timer"]
        )
    ],
    targets: [
        .target(
            name: "Timer",
            path: "Sources"
        )
    ]
)