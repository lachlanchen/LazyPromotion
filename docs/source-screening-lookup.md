# Look up prior screening before revisiting a source

Use the existing private graph before opening a rediscovered paid request:

```bash
python network.py lookup 'https://example.com/jobs/123/'
```

Up to twenty URLs may be passed together. The command opens the existing SQLite
database read-only, does not synchronize or create it, and never fetches a page,
changes a candidate, sends a message, or makes a revenue entry. Use `--db PATH`
after `lookup` for a different existing graph.

The output is private operating context. It reports matching entity identifiers,
stored screening decisions, explicit review dates/triggers, and evidence-file
references when present. It omits labels, correspondence, customer fields and
unrelated metadata. Do not commit or publish its output. Decisions must be
recorded in the graph to be found; this does not search private Markdown files.

`not_recorded` means only that no matching URL is stored. It does not mean the
request is eligible, new, unanswered, or available. A graph update timestamp
is not a fresh observation of the source. Conflicting records or unreadable
metadata require inspection of the original private evidence.

Matching ignores UTM tracking parameters and normalizes host/scheme case.
It preserves meaningful query parameters, fragments, path case, trailing slashes
and HTTP versus HTTPS. Redirect aliases must be checked explicitly; the lookup
does not visit redirects or infer that two different requests are one buyer.

For a recorded exclusion, reopen the source only when its recorded review date
is due or a relevant new invitation, changed scope, or other explicit trigger
exists. Existing applications should go through their narrow inbound monitor,
not a duplicate pitch. The lookup itself neither grants permission nor enforces
a sending decision.
