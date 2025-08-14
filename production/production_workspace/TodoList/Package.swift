// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TodoList",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "TodoList",
            targets: ["TodoList"]
        )
    ],
    targets: [
        .target(
            name: "TodoList",
            path: "Sources"
        )
    ]
)