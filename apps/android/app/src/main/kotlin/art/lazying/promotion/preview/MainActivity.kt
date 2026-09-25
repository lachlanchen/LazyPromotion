package art.lazying.promotion.preview

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(primary = Color(0xFF136C61))) {
                PreviewApp(
                    load = { WorkspaceCodec.decode(assets.open("workspace-preview.json").bufferedReader().use { it.readText() }) },
                    open = { link ->
                        if (WorkspaceCodec.safeLink(link)) runCatching {
                            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(link)))
                        }
                    },
                    share = { link ->
                        if (WorkspaceCodec.safeLink(link)) runCatching {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"; putExtra(Intent.EXTRA_TEXT, link)
                            }, "Share public link"))
                        }
                    }
                )
            }
        }
    }
}

@Composable
private fun PreviewApp(load: () -> PreviewSnapshot, open: (String) -> Unit, share: (String) -> Unit) {
    var attempt by remember { mutableIntStateOf(0) }
    val result = remember(attempt) { runCatching(load) }
    var selectedId by rememberSaveable { mutableStateOf<String?>(null) }
    val snapshot = result.getOrNull()
    val selected = snapshot?.workspace?.projects?.find { it.id == selectedId }
    BackHandler(enabled = selected != null) { selectedId = null }
    Surface(modifier = Modifier.fillMaxSize()) {
        LazyColumn(
            modifier = Modifier.fillMaxSize().safeDrawingPadding(),
            contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                Text("LazyPromotion", style = MaterialTheme.typography.headlineLarge)
                Text("A useful answer starts with a real need.", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(12.dp))
                Text("LOCAL PREVIEW · READ ONLY", style = MaterialTheme.typography.labelLarge)
                Text("Bundled campaign history, not a live account. Nothing is posted from this preview.")
                snapshot?.let { Text("Snapshot: ${it.fetchedAt}", style = MaterialTheme.typography.bodySmall) }
            }
            if (snapshot == null) {
                item {
                    Text("Campaign data unavailable. The bundled copy could not be verified.")
                    Button(onClick = { attempt++ }) { Text("Retry") }
                }
            } else if (selected == null) {
                item { Text("Products", style = MaterialTheme.typography.titleLarge) }
                if (snapshot.workspace.projects.isEmpty()) item { Text("No products in this snapshot.") }
                items(snapshot.workspace.projects, key = { it.id }) { project ->
                    Card(onClick = { selectedId = project.id }, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text(project.name, style = MaterialTheme.typography.titleLarge)
                            Text("${project.publications.size} recorded publications")
                            Text("View campaign history →")
                        }
                    }
                }
            } else {
                item {
                    TextButton(onClick = { selectedId = null }) { Text("← Products") }
                    Text(selected.name, style = MaterialTheme.typography.headlineSmall)
                    selected.links.forEach { (kind, link) ->
                        TextButton(onClick = { open(link) }) { Text("Open $kind") }
                    }
                    Text("Results", style = MaterialTheme.typography.titleLarge)
                    Text("Installs: Not connected\nCustomers: Not connected\nReceived revenue: Not connected")
                    Text("A published post is not evidence of an install or a sale.", style = MaterialTheme.typography.bodySmall)
                }
                if (selected.publications.isEmpty()) item { Text("No recorded publications.") }
                items(selected.publications, key = { it.id }) { post ->
                    PublicationCard(post, open, share)
                }
            }
        }
    }
}

@Composable
private fun PublicationCard(post: Publication, open: (String) -> Unit, share: (String) -> Unit) {
    var expanded by rememberSaveable(post.id) { mutableStateOf(false) }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(post.community ?: post.platform, style = MaterialTheme.typography.labelLarge)
            post.title?.let { Text(it, style = MaterialTheme.typography.titleMedium) }
            Text(post.visibilityLabel)
            Text("Published ${post.publishedAt}\nRecord checked ${post.recordCheckedOn}", style = MaterialTheme.typography.bodySmall)
            TextButton(onClick = { expanded = !expanded }) { Text(if (expanded) "Hide published text" else "Read published text") }
            if (expanded) SelectionContainer { Text(post.body) }
            TextButton(onClick = { open(post.url) }) { Text("Open original post") }
            TextButton(onClick = { share(post.url) }) { Text("Share public link…") }
        }
    }
}
