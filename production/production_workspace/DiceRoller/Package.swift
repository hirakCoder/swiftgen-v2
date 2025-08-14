// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "DiceRoller",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "DiceRoller",
            targets: ["DiceRoller"]
        )
    ],
    targets: [
        .target(
            name: "DiceRoller",
            path: "Sources"
        )
    ]
)