// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PromotionCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "PromotionCore", targets: ["PromotionCore"])],
    targets: [
        .target(name: "PromotionCore", path: "LazyPromotion/Core"),
        .testTarget(name: "PromotionCoreTests", dependencies: ["PromotionCore"], path: "Tests")
    ]
)
