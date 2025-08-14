// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NeonCalc",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "NeonCalc",
            targets: ["NeonCalc"]
        )
    ],
    targets: [
        .target(
            name: "NeonCalc",
            path: "Sources"
        )
    ]
)