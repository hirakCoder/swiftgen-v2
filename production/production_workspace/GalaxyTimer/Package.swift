// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "GalaxyTimer",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "GalaxyTimer",
            targets: ["GalaxyTimer"]
        )
    ],
    targets: [
        .target(
            name: "GalaxyTimer",
            path: "Sources"
        )
    ]
)