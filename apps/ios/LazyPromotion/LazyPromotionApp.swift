import SwiftUI

@main
struct LazyPromotionApp: App {
    var body: some Scene { WindowGroup { WorkspaceView() } }
}

private struct WorkspaceView: View {
    @State private var snapshot: PreviewSnapshot?
    @State private var failed = false

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("A useful answer starts with a real need.").font(.headline)
                    Text("LOCAL PREVIEW · READ ONLY").font(.caption).bold()
                    Text("Bundled campaign history, not a live account. Nothing is posted from this preview.")
                    if let snapshot { Text("Snapshot: \(snapshot.fetchedAt)").font(.caption).foregroundStyle(.secondary) }
                }
                if failed {
                    Section {
                        Text("Campaign data unavailable. The bundled copy could not be verified.")
                        Button("Retry", action: load)
                    }
                } else if let snapshot {
                    Section("Products") {
                        if snapshot.workspace.projects.isEmpty { Text("No products in this snapshot.") }
                        ForEach(snapshot.workspace.projects) { project in
                            NavigationLink {
                                ProductView(project: project)
                            } label: {
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(project.name).font(.headline)
                                    Text("\(project.publications.count) recorded publications").font(.subheadline).foregroundStyle(.secondary)
                                }.padding(.vertical, 6)
                            }
                        }
                    }
                } else { ProgressView("Reading campaign snapshot…") }
            }
            .navigationTitle("LazyPromotion")
            .task { load() }
        }
        .tint(Color(red: 0.07, green: 0.42, blue: 0.38))
    }

    private func load() {
        do {
            guard let url = Bundle.main.url(forResource: "workspace-preview", withExtension: "json") else { throw ContractError.unsupported }
            snapshot = try PreviewSnapshot.decode(Data(contentsOf: url)); failed = false
        } catch { snapshot = nil; failed = true }
    }
}

private struct ProductView: View {
    let project: Project
    var body: some View {
        List {
            Section("Public product links") {
                ForEach(project.links.keys.sorted(), id: \.self) { kind in
                    if let raw = project.links[kind], let url = safeLink(raw) { Link("Open \(kind)", destination: url) }
                }
            }
            Section("Results") {
                LabeledContent("Installs", value: "Not connected")
                LabeledContent("Customers", value: "Not connected")
                LabeledContent("Received revenue", value: "Not connected")
                Text("A published post is not evidence of an install or a sale.").font(.caption)
            }
            Section("Campaign history · bundled snapshot") {
                if project.publications.isEmpty { Text("No recorded publications.") }
                ForEach(project.publications) { post in
                    VStack(alignment: .leading, spacing: 10) {
                        Text(post.community ?? post.platform).font(.caption).bold()
                        if let title = post.title { Text(title).font(.headline) }
                        Text(post.visibilityLabel).font(.subheadline)
                        Text("Published \(post.publishedAt)\nRecord checked \(post.recordCheckedOn)").font(.caption).foregroundStyle(.secondary)
                        DisclosureGroup("Read published text") { Text(post.body).textSelection(.enabled) }
                        if let url = safeLink(post.url) {
                            Link("Open original post", destination: url)
                            ShareLink("Share public link…", item: url)
                        }
                    }.padding(.vertical, 8)
                }
            }
        }.navigationTitle(project.name).navigationBarTitleDisplayMode(.inline)
    }
}
