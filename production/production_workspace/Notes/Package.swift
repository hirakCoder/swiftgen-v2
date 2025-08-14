// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Notes",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Notes",
            targets: ["Notes"]
        )
    ],
    targets: [
        .target(
            name: "Notes",
            path: "Sources"
        )
    ]
)