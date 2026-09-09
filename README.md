[English](README.md) · [العربية](i18n/README.ar.md) · [Español](i18n/README.es.md) · [Français](i18n/README.fr.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Tiếng Việt](i18n/README.vi.md) · [中文 (简体)](i18n/README.zh-Hans.md) · [中文（繁體）](i18n/README.zh-Hant.md) · [Deutsch](i18n/README.de.md) · [Русский](i18n/README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Find a real need, write a useful answer, disclose your connection, and let a human decide whether to send it.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion is a local, review-first social discovery assistant. It searches
the real Reddit, X, Instagram, and Hacker News web interfaces in one visible
Chrome profile, records possible matches in SQLite, drafts grounded replies
with the signed-in account's recommended Codex model at low reasoning effort,
and stops before public send. It is for maintainers who want to help people
with relevant open-source work without turning communities into a sales queue.

The repository also keeps a public inventory of 108 non-archived
`lachlanchen` source repositories and combines them into buyer-shaped,
evidence-gated opportunities across code, books, knowledge graphs, research,
media, language learning, and local AI. Eight fixed-scope service routes support
the first verified USD 1,000 goal; clicks, stars, applications, and queued posts
never count as revenue.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## The operating contract

- Helpful first: answer the person's concrete problem before naming a project.
- Honest affiliation: use plain disclosure such as “I maintain…” or “I built…”.
- Exact need, not keyword overlap: stale posts, vague intent, self-promotion,
  quoted requests, and ambiguous phrases are filtered before model triage.
- Evidence before offer: a route needs inspectable public proof, written scope,
  exclusions, and a fit check before it can become commercial.
- One person, one decision: no mass replies, unsolicited DMs, automated votes,
  follows, repeated outreach, or engagement loops.
- Exact approval: editing a draft invalidates its short-lived, hash-bound
  approval; a send must match the reviewed destination and content.
- Visible operation: browser work uses the dedicated noVNC Chrome profile.
  Personal browser windows are out of scope.
- Private by default: credentials, cookies, customer material, candidates,
  drafts, approvals, payment data, and runtime evidence never enter Git.
- Strict measurement: attention, inquiries, accepted scopes, confirmed
  payments, delivery, refunds, and received revenue remain separate states.

## Current contents

| Path | Purpose |
| --- | --- |
| [`promotion.py`](promotion.py) | SQLite ledger, matching, Codex triage/drafting, and hash-bound approval |
| [`browser.py`](browser.py) | Playwright/CDP discovery, inspection, composer preparation, and guarded send |
| [`worker.py`](worker.py) | Finite, cooldown-based discovery and private review queue; never sends |
| [`catalog.json`](catalog.json) and [`github-repos.json`](github-repos.json) | Curated need matching plus the public repository inventory |
| [`portfolio-opportunities.json`](portfolio-opportunities.json) | Buyer-shaped combinations of code, books, knowledge systems, and media |
| [`bounties.py`](bounties.py) | Reconciles public bounty listings with live GitHub state and rejects unsafe or already-contested work |
| [`docs/portfolio-inventory.md`](docs/portfolio-inventory.md) | Complete public work map grouped by real problem area |
| [`docs/compound-opportunities.md`](docs/compound-opportunities.md) | Ranked opportunity contracts with proof and delivery gates |
| [`docs/first-1000.md`](docs/first-1000.md) | Eight bounded USD 250/USD 500 service routes and truthful milestone math |
| [`docs/paid-need-decision-2026-09-09.md`](docs/paid-need-decision-2026-09-09.md) | Current direct-route screen, evidence gaps, and submission gates |
| [`metrics.py`](metrics.py), [`network.py`](network.py), and [`signals.py`](signals.py) | Evidence-gated funnel, public graph, and first-party demand signals |
| [`owned_monitor.py`](owned_monitor.py) and [`lkt_inbox.py`](lkt_inbox.py) | Read-only publication monitoring and private fit-check intake |
| [`scripts/desktop.sh`](scripts/desktop.sh) | One project-owned Xvfb/x11vnc/noVNC/Chrome review desktop |
| [`application_watch.py`](application_watch.py) | Read-only due-review report for sent applications; never opens mail or follows up |
| [`docs/open-source-evaluation.md`](docs/open-source-evaluation.md) | Auditable open-source and MCP tool choices |

## Quick start

Requires Linux, Python 3.10+, Chrome, Playwright for Python, Xvfb, x11vnc,
`wmctrl`, noVNC/websockify, `tmux`, and an authenticated Codex CLI.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Sign in manually through noVNC, then run one narrow, need-oriented search:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Only after a human confirms the exact destination and complete text:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

The same discovery cycle supports Reddit, X, Instagram, and Hacker News.
Hacker News is research-only: LazyPromotion cannot draft, approve, prepare, or
send comments there. Reviewed first-party scheduling through Postiz stays
separate from community replies. Detailed worker, payment, affiliate, delivery,
Postiz, and browser procedures live under [`docs/`](docs/).

Public GitHub bounties can be screened without claiming or changing an issue:

```bash
python bounties.py
```

The board is discovery only. The auditor verifies live issue state and existing
solution pull requests, rejects unsafe instruction requests, and writes its
private report under `.local/`.

## Runtime isolation

The launcher owns one 1920×1080 display (`:116`), VNC port `5936`, noVNC
port `6136`, and loopback CDP port `9436`. It reuses one persistent Chrome
profile, refuses unknown occupied ports, records one private runtime handoff,
and removes only stale resources that it owns. Keep the host viewer maximized
inside the GNOME work area, never full-screen. Stop the stack when no visible
review is waiting.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Open-source baseline

The core is deliberately small: Playwright for the visible browser, SQLite for
durable local state, and the account-supported Codex model for structured
triage and drafting. Postiz is used only for reviewed first-party scheduling.
MCP attachments are optional and pinned; model subprocesses do not receive
browser, scheduler, credential, or payment access.

The portfolio layer turns public projects into explicit opportunity contracts
rather than promoting all repositories at once. Current routes include local
collection fit, manuscript redline, bilingual lecture delivery, story clips,
book specimens, and AI clip assembly. Lexical ingestion is a reusable LKT
specialization, not a claim that a closed marketplace listing is still open.

## Validation

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py
bash -n scripts/desktop.sh
git diff --check
```

These checks validate local contracts, not third-party availability, community
fit, translation quality, customer outcomes, or revenue.

## Citation

If you use LazyPromotion in research, cite the repository. GitHub reads
[`CITATION.cff`](CITATION.cff) and shows a **Cite this repository** panel.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## Status and scope

This is an early Linux-first release. Third-party selectors, platform rules,
and account capabilities can change. Discovery and drafting are assistance,
not evidence that a reply should be posted. The operator remains responsible
for accuracy, rights, disclosure, community fit, platform terms, payment
review, and final send.
