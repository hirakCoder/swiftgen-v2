// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Calculator",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Calculator",
            targets: ["Calculator"]
        )
    ],
    targets: [
        .target(
            name: "Calculator",
            path: "Sources"
        )
    ]
)