// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Counter",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Counter",
            targets: ["Counter"]
        )
    ],
    targets: [
        .target(
            name: "Counter",
            path: "Sources"
        )
    ]
)