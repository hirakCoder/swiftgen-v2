// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Weather",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Weather",
            targets: ["Weather"]
        )
    ],
    targets: [
        .target(
            name: "Weather",
            path: "Sources"
        )
    ]
)