// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MartianCounter",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "MartianCounter",
            targets: ["MartianCounter"]
        )
    ],
    targets: [
        .target(
            name: "MartianCounter",
            path: "Sources"
        )
    ]
)