import Foundation
import CryptoKit

public struct PreviewSnapshot: Decodable {
    public let fetchedAt: String
    public let workspace: Workspace

    public static func decode(_ data: Data) throws -> PreviewSnapshot {
        guard data.count <= 524288 else { throw ContractError.unsupported }
        let snapshot = try JSONDecoder().decode(Self.self, from: data)
        guard ISO8601DateFormatter().date(from: snapshot.fetchedAt) != nil else { throw ContractError.unsupported }
        try snapshot.workspace.validate()
        return snapshot
    }
}

public struct Workspace: Decodable {
    public let version: Int
    public let mode: String
    public let capabilities: [String: Bool]
    public let projects: [Project]

    func validate() throws {
        guard version == 1, mode == "public_campaign_preview", capabilities == [
            "readPublishedCampaigns": true, "discover": false, "draft": false,
            "approve": false, "publish": false, "paymentAttribution": false
        ], projects.count <= 20, Set(projects.map(\.id)).count == projects.count else {
            throw ContractError.unsupported
        }
        for project in projects { try project.validate() }
    }
}

public struct Project: Decodable, Identifiable {
    public let id: String
    public let name: String
    public let links: [String: String]
    public let publications: [Publication]
    public let outcomes: [String: Outcome]

    func validate() throws {
        try checkedText(id, maximum: 120); try checkedText(name, maximum: 300)
        let linkKinds: Set<String> = ["apple", "google", "reader", "video", "repository"]
        guard Set(links.keys).isSubset(of: linkKinds), links.values.allSatisfy({ safeLink($0) != nil }),
              publications.count <= 100, Set(publications.map(\.id)).count == publications.count,
              Set(outcomes.keys) == Set(["installs", "customers", "receivedGrossUsd"]) else {
            throw ContractError.unsupported
        }
        for post in publications { try post.validate() }
    }
}

public struct Outcome: Decodable {
    public let state: String
    enum CodingKeys: String, CodingKey { case state, value }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        state = try values.decode(String.self, forKey: .state)
        // decodeNil throws on missing value; absence is not an observed zero.
        guard state == "not_connected", try values.decodeNil(forKey: .value) else { throw ContractError.unsupported }
    }
}

public struct Publication: Decodable, Identifiable {
    public let id: String
    public let platform: String
    public let community: String?
    public let title: String?
    public let body: String
    public let bodySha256: String
    public let publishedAt: String
    public let recordCheckedOn: String
    public let url: String
    public let visibilityEvidence: String

    public var visibilityLabel: String {
        switch visibilityEvidence {
        case "public_verified": return "Public visibility checked"
        case "account_verified": return "Signed-in check only"
        default: return "Visibility unverified"
        }
    }

    func validate() throws {
        try checkedText(id, maximum: 300); try checkedText(body, maximum: 20000)
        if let title { try checkedText(title, maximum: 300) }
        if let community { try checkedText(community, maximum: 120) }
        let digest = SHA256.hash(data: Data(body.utf8)).map { String(format: "%02x", $0) }.joined()
        let calendarDate = DateFormatter()
        calendarDate.locale = Locale(identifier: "en_US_POSIX")
        calendarDate.timeZone = TimeZone(secondsFromGMT: 0)
        calendarDate.dateFormat = "yyyy-MM-dd"
        calendarDate.isLenient = false
        guard ["reddit", "x"].contains(platform), safeLink(url) != nil,
              ["public_verified", "account_verified", "unverified"].contains(visibilityEvidence),
              digest == bodySha256, ISO8601DateFormatter().date(from: publishedAt) != nil,
              recordCheckedOn.count == 10, calendarDate.date(from: recordCheckedOn) != nil else {
            throw ContractError.unsupported
        }
    }
}

public enum ContractError: Error { case unsupported }

private func checkedText(_ value: String, maximum: Int) throws {
    guard !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
          value.count <= maximum, !value.unicodeScalars.contains(where: { $0.value < 32 && $0 != "\n" && $0 != "\t" }) else {
        throw ContractError.unsupported
    }
}

public func safeLink(_ raw: String) -> URL? {
    let hosts: Set<String> = ["apps.apple.com", "play.google.com", "www.youtube.com",
        "github.com", "lachlan.lazying.art", "www.reddit.com", "reddit.com", "x.com", "twitter.com"]
    guard raw.count <= 2048, !raw.unicodeScalars.contains(where: { CharacterSet.whitespacesAndNewlines.contains($0) || $0.value < 32 }),
          let parts = URLComponents(string: raw), parts.scheme == "https",
          let host = parts.host, hosts.contains(host), parts.user == nil, parts.password == nil,
          parts.port == nil, parts.fragment == nil else { return nil }
    return parts.url
}
