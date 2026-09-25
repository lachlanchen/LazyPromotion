package art.lazying.promotion.preview

import java.net.URI
import java.security.MessageDigest
import java.time.Instant
import java.time.LocalDate
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull

@Serializable data class PreviewSnapshot(val fetchedAt: String, val workspace: Workspace)
@Serializable data class Workspace(
    val version: Int, val mode: String, val capabilities: Map<String, Boolean>,
    val projects: List<Project>
)
@Serializable data class Project(
    val id: String, val name: String, val links: Map<String, String>,
    val publications: List<Publication>, val outcomes: Map<String, Outcome>
)
@Serializable data class Outcome(val state: String, val value: JsonElement)
@Serializable data class Publication(
    val id: String, val platform: String, val community: String?, val title: String?,
    val body: String, val bodySha256: String, val publishedAt: String,
    val recordCheckedOn: String, val url: String, val visibilityEvidence: String
) {
    val visibilityLabel: String get() = when (visibilityEvidence) {
        "public_verified" -> "Public visibility checked"
        "account_verified" -> "Signed-in check only"
        else -> "Visibility unverified"
    }
}

object WorkspaceCodec {
    private val json = Json { ignoreUnknownKeys = false; explicitNulls = true }
    private val hosts = setOf("apps.apple.com", "play.google.com", "www.youtube.com",
        "github.com", "lachlan.lazying.art", "www.reddit.com", "reddit.com", "x.com", "twitter.com")
    private val capabilities = mapOf("readPublishedCampaigns" to true, "discover" to false,
        "draft" to false, "approve" to false, "publish" to false, "paymentAttribution" to false)

    fun safeLink(raw: String): Boolean = runCatching {
        val url = URI(raw)
        raw.length <= 2048 && raw.none { it.isWhitespace() || it.code < 32 } &&
            url.scheme == "https" && url.host in hosts && url.rawUserInfo == null &&
            url.port == -1 && url.rawFragment == null && url.rawAuthority == url.host
    }.getOrDefault(false)

    private fun text(value: String, max: Int) {
        require(value.isNotBlank() && value.length <= max)
        require(value.none { it.code < 32 && it != '\n' && it != '\t' })
    }

    fun decode(raw: String): PreviewSnapshot {
        require(raw.toByteArray(Charsets.UTF_8).size <= 524288)
        val snapshot = json.decodeFromString<PreviewSnapshot>(raw)
        Instant.parse(snapshot.fetchedAt)
        val workspace = snapshot.workspace
        require(workspace.version == 1 && workspace.mode == "public_campaign_preview")
        require(workspace.capabilities == capabilities)
        require(workspace.projects.size <= 20)
        require(workspace.projects.map { it.id }.toSet().size == workspace.projects.size)
        workspace.projects.forEach { project ->
            text(project.id, 120); text(project.name, 300)
            require(project.links.keys.all { it in setOf("apple", "google", "reader", "video", "repository") })
            require(project.links.values.all(::safeLink))
            require(project.publications.size <= 100)
            require(project.publications.map { it.id }.toSet().size == project.publications.size)
            project.publications.forEach { post ->
                text(post.id, 300); text(post.body, 20000)
                post.title?.let { text(it, 300) }; post.community?.let { text(it, 120) }
                require(post.platform in setOf("reddit", "x"))
                require(safeLink(post.url))
                require(post.visibilityEvidence in setOf("public_verified", "account_verified", "unverified"))
                Instant.parse(post.publishedAt); LocalDate.parse(post.recordCheckedOn)
                val digest = MessageDigest.getInstance("SHA-256").digest(post.body.toByteArray(Charsets.UTF_8))
                    .joinToString("") { "%02x".format(it) }
                require(digest == post.bodySha256)
            }
            require(project.outcomes.keys == setOf("installs", "customers", "receivedGrossUsd"))
            require(project.outcomes.values.all { it.state == "not_connected" && it.value == JsonNull })
        }
        return snapshot
    }
}
