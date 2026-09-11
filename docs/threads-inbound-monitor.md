# Threads reply monitor

Threads is not one of the five channels connected to the current Postiz
account, so Postiz analytics cannot reliably surface replies there. This small
monitor closes that gap through the existing dedicated noVNC browser.

Open the project browser first. Its workspace restores exactly one authenticated
Threads Replies activity tab:

```bash
scripts/desktop.sh start
python threads_inbound_monitor.py once
python threads_inbound_monitor.py status
```

The read pass brings that already-open tab to the front and inspects only page
state and reply-link targets. It does not follow a notification or read a
thread. Stored activity identities are SHA-256 fingerprints; usernames, reply
text, post URLs, cookies, and account identifiers are not written to the
status or log.

The first successful observation establishes a quiet baseline. A later new
fingerprint, a larger notification count, or an authenticated page whose
layout can no longer be recognized creates a review alert and saves one private
screenshot. It never replies automatically and never classifies engagement as
a lead, buyer, or revenue.

The optional loop is suitable only while the dedicated browser remains open:

```bash
python threads_inbound_monitor.py loop --interval-minutes 30
```

Stop the browser when no visible review is pending. A stopped browser is an
expected unavailable state, not permission to touch personal Firefox or open a
second profile.
