import Foundation
import XCTest
@testable import PromotionCore

final class WorkspaceTests: XCTestCase {
    private func fixture() throws -> Data {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
        return try Data(contentsOf: root.appendingPathComponent("shared/workspace-preview.json"))
    }
    private func replacing(_ from: String, _ to: String) throws -> Data {
        Data(try String(decoding: fixture(), as: UTF8.self).replacingOccurrences(of: from, with: to).utf8)
    }
    func testPublicHistoryPreservesUnknownOutcomesAndAccountOnlyVisibility() throws {
        let value = try PreviewSnapshot.decode(fixture())
        XCTAssertEqual(value.workspace.projects.count, 2)
        let posts = value.workspace.projects.flatMap(\.publications)
        XCTAssertEqual(posts.count, 5)
        XCTAssertTrue(posts.contains { $0.visibilityLabel == "Signed-in check only" })
        XCTAssertTrue(value.workspace.projects.allSatisfy { $0.outcomes.values.allSatisfy { $0.state == "not_connected" } })
    }
    func testRejectsUnsupportedVersionAndPublishingCapability() throws {
        XCTAssertThrowsError(try PreviewSnapshot.decode(replacing("\"version\": 1", "\"version\": 2")))
        XCTAssertThrowsError(try PreviewSnapshot.decode(replacing("\"publish\": false", "\"publish\": true")))
    }
    func testMissingOutcomesNeverBecomeZero() throws {
        XCTAssertThrowsError(try PreviewSnapshot.decode(replacing("\"value\": null", "\"value\": 0")))
        XCTAssertThrowsError(try PreviewSnapshot.decode(Data("{}".utf8)))
    }
    func testModifiedCopyFailsItsHash() throws {
        let post = try PreviewSnapshot.decode(fixture()).workspace.projects[0].publications[0]
        XCTAssertThrowsError(try PreviewSnapshot.decode(replacing(post.bodySha256, String(repeating: "0", count: 64))))
    }
    func testLinkBoundaries() {
        for url in ["javascript:alert(1)", "http://github.com/x", "https://github.com.evil.test/x",
                    "https://token@github.com/x", "https://github.com:443/x", "https://127.0.0.1/x",
                    "https://github.com/x#token", "https://github.com/x\n"] {
            XCTAssertNil(safeLink(url), url)
        }
        XCTAssertNotNil(safeLink("https://play.google.com/store/apps/details?id=art.lazying.landn"))
    }
}
