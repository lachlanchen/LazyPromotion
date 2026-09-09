# GitHub inbound issue monitor

`github_inbound_monitor.py` observes public issue metadata for this fixed
`lachlanchen` repository allowlist:

- `uu-remote-ubuntu-bridge`
- `LazyTunnel`
- `LocalKnowledgeTerminal`
- `leonardsusskind`
- `OpenHI`
- `Kindle`
- `Video2Book`
- `LazyEdit`

Each pass makes one authenticated GitHub GraphQL query. The query requests the
repository's visibility and at most the latest 100 issue records: number,
title, URL, state, timestamps, and author login. It requests no issue body,
comments, or replies. Every repository must identify itself as `PUBLIC` in the
same response before any result is accepted. The query contains no mutation,
and the monitor has no comment, reply, close, label, or other write operation.

## State and alerts

The default state is the Git-ignored
`.local/github-inbound-monitor-status.json`. The monitor refuses destinations
outside `.local`, tracked or non-ignored destinations, non-JSON files,
symbolic-link path components, non-regular files, and multiply linked state
files. State replacement is atomic and the resulting file mode is `0600`.

The first successful pass records existing issue keys as a baseline and emits
no alerts. Later passes alert only for keys absent from all prior successful
passes. Seen keys are retained even after an issue leaves the bounded current
window. An API or validation failure leaves the last complete state untouched.
An alert asks for manual relevance review; it is not a lead, customer, sale, or
revenue classification, and it never triggers a GitHub response.

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
