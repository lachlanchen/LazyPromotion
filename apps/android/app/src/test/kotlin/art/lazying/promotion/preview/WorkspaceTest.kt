package art.lazying.promotion.preview

import org.junit.Assert.*
import org.junit.Test
import kotlinx.serialization.json.*

class WorkspaceTest {
    private fun fixture(): String = javaClass.getResourceAsStream("/workspace-preview.json")!!
        .bufferedReader().use { it.readText() }

    @Test fun realPublicHistoryKeepsUnknownOutcomes() {
        val data = WorkspaceCodec.decode(fixture())
        assertEquals(2, data.workspace.projects.size)
        assertEquals(5, data.workspace.projects.sumOf { it.publications.size })
        assertTrue(data.workspace.projects.all { p -> p.outcomes.values.all { it.value == JsonNull } })
        assertTrue(data.workspace.projects.flatMap { it.publications }.any { it.visibilityLabel == "Signed-in check only" })
    }

    @Test fun rejectsEnabledSendAndUnsupportedVersion() {
        assertThrows(Exception::class.java) { WorkspaceCodec.decode(fixture().replace("\"publish\": false", "\"publish\": true")) }
        assertThrows(Exception::class.java) { WorkspaceCodec.decode(fixture().replace("\"version\": 1", "\"version\": 2")) }
    }

    @Test fun neverTurnsMissingDataIntoZeroOrAcceptsChangedCopy() {
        assertThrows(Exception::class.java) { WorkspaceCodec.decode(fixture().replace("\"value\": null", "\"value\": 0")) }
        val post = WorkspaceCodec.decode(fixture()).workspace.projects.first().publications.first()
        assertThrows(Exception::class.java) { WorkspaceCodec.decode(fixture().replace(post.bodySha256, "0".repeat(64))) }
    }

    @Test fun rejectsPrivateAndExecutableLinks() {
        listOf("javascript:alert(1)", "http://github.com/lachlanchen", "https://github.com.evil.test/x",
            "https://token@github.com/x", "https://github.com:443/x", "https://127.0.0.1/x",
            "https://github.com/x#token", "https://github.com/x\n").forEach {
            assertFalse(it, WorkspaceCodec.safeLink(it))
        }
        assertTrue(WorkspaceCodec.safeLink("https://play.google.com/store/apps/details?id=art.lazying.landn"))
    }

    @Test fun duplicateProjectAndMissingFieldsFailClosed() {
        val root = Json.parseToJsonElement(fixture()).jsonObject
        val ws = root.getValue("workspace").jsonObject
        val product = ws.getValue("projects").jsonArray.first()
        val duplicate = JsonObject(root + ("workspace" to JsonObject(ws + ("projects" to JsonArray(listOf(product, product))))))
        assertThrows(Exception::class.java) { WorkspaceCodec.decode(duplicate.toString()) }
        assertThrows(Exception::class.java) { WorkspaceCodec.decode("{}") }
    }
}
