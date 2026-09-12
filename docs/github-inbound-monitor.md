# GitHub inbound issue, pull-request, and reply monitor

`github_inbound_monitor.py` observes public issue and pull-request metadata for this fixed
`lachlanchen` repository allowlist:

- `uu-remote-ubuntu-bridge`
- `LazyTunnel`
- `LocalKnowledgeTerminal`
- `leonardsusskind`
- `OpenHI`
- `Kindle`
- `Video2Book`
- `LazyEdit`
- `L-and-N`
- `AgInTi-LabCanvas`
- `LocalVideoGen`
- `LazyPromotion`
- `Musia`
- `LinguaLeaf`
- `PocketPolyglot`

`AiMemo` is intentionally excluded while it is private. The monitor refuses
authenticated private-repository data rather than copying it into the shared
promotion workflow.

The fixed external-thread allowlist currently contains
`arjun-techjays/bos#18`, `pilotariak/azkena#14`, and
`hivtools/hivtools-mcp#10`, where `lachlanchen` posted reviewed,
issue-specific answers, plus `punkpeye/mcp-remote#361`, which is linked to a
submitted upstream fix. For these threads the same GraphQL query requests only repository
visibility, issue number, title, URL, state, update time, and aggregate comment
count. It requests neither the issue body nor any comment body. A newly added
external thread is baselined once; a later metadata or comment-count change
creates a manual-review alert. It never opens the response or replies.

The added agent, video, music, and multilingual-book repositories are current
public, non-fork, non-archived projects with owner-visible attention in the
September 11 portfolio audit. The allowlist remains intentionally narrower
than the complete portfolio so the monitor follows projects with an active
offer, strong attention, or a direct product path instead of treating every
issue as buyer intent.

Each pass makes one authenticated GitHub GraphQL query. The query requests the
repository's visibility and at most the latest 100 issues and 100 pull
requests. For issues it records number, title, URL, state, timestamps, and
author login. Pull requests add draft state plus comment and review counts.
It requests no issue, pull-request, comment, or review body. Every repository
must identify itself as `PUBLIC` in the same response before any result is
accepted. The query contains no mutation, and the monitor has no comment,
reply, merge, close, label, or other write operation.

## State and alerts

The default state is the Git-ignored
`.local/github-inbound-monitor-status.json`. The monitor refuses destinations
outside `.local`, tracked or non-ignored destinations, non-JSON files,
symbolic-link path components, non-regular files, and multiply linked state
files. State replacement is atomic and the resulting file mode is `0600`.

The first successful pass records existing issue and pull-request keys as a
baseline and emits no alerts. Upgrading an older issue-only state also
baselines current pull requests once, avoiding a false alert storm. When a new
public repository is appended to the fixed allowlist, its existing activity is
baselined while previously watched repositories keep their seen history.
Later passes alert for a new issue, a new pull request, or a changed public
pull-request activity timestamp. An explicit external thread also alerts when
its state, update time, or aggregate comment count changes. Seen keys and the
last activity summaries are retained when an item leaves a bounded current
window. An API or validation failure leaves the last complete state untouched.
An alert asks for manual relevance review; it is not a lead, customer, sale, or
revenue classification, and it never triggers a GitHub response or merge.

## Operation

Run a single pass:

```bash
python github_inbound_monitor.py once
```

Run the loop directly (15 minutes is the minimum):

```bash
python github_inbound_monitor.py loop --interval-minutes 15
```

The wrapper maintains one project-owned tmux session and an owner-readable
private stdout log:

```bash
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

Override the interval with
`GITHUB_INBOUND_MONITOR_INTERVAL_MINUTES`; values below 15 are refused. Starting
the wrapper when its session already exists is a no-op. Stopping it retains the
seen state so the next pass does not re-alert old issues.
