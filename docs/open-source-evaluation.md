# Open-source options evaluated

Checked on 2026-08-31. LazyPromotion deliberately starts smaller than a social
media management suite: one persistent visible browser, one SQLite ledger, one
relevance filter, one bounded drafting call, and an exact-content approval gate.

| Project | Useful ideas | Why it is not the default runtime |
| --- | --- | --- |
| [Postiz](https://github.com/gitroomhq/postiz-app) | Mature scheduler, many providers, CLI | The already-open hosted account stops at a payment-verified trial, while self-hosting is much larger than the reply-assistance loop needs. |
| [Mixpost Lite](https://github.com/inovector/mixpost) | MIT-licensed calendar, templates, official integrations | Laravel/PHP application stack; useful later for planned campaigns, not necessary for direct one-at-a-time help replies. |
| [Postmill](https://github.com/postmill-ai/postmill-app) | Agent/API concepts, guardrails, cross-channel inbox | AGPL monorepo using Next.js, NestJS, PostgreSQL, Redis, and Inngest; significantly heavier and currently a very young fork. |
| [SocialCrabs](https://github.com/adolfousier/socialcrabs) | Playwright adapters for Instagram, X, and LinkedIn | Its automated likes/follows/DMs and “human simulation” scope conflicts with this project's anti-spam, explicit-action design; Reddit support is also only planned. |
| [Steadfast](https://github.com/getsteadfast/steadfast) | Persistent sessions, VNC login, per-platform adapters | Cookie import, anti-detect behavior, and automated likes/upvotes are broader and riskier than needed. We retain the good session-persistence idea without adopting evasion features. |
| [Playwright](https://github.com/microsoft/playwright-python) | Direct DOM control, CDP attachment, screenshots | Selected. It is already installed on this workstation and can reuse system Chrome without another SDK or browser download. |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Open-source semantic snapshots and agent tools with an official CDP attachment mode | Selected as an optional, pinned interface over the same browser. Direct `browser.py` checks remain authoritative for public sends. |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Deep console, network, performance, and Chrome diagnostics with `--browser-url` attachment | Strong debugging alternative, but redundant for the initial runtime. Its metrics are enabled by default unless explicitly disabled, while Playwright MCP aligns with the existing controller. |

The approval boundary follows current Reddit requirements: each user action must
be a separate, explicit manual choice, and repeated unsolicited engagement is
spam whether it is automated or manual.

- [Reddit User Actions requirements](https://developers.reddit.com/docs/capabilities/server/userActions)
- [Reddit spam policy](https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam)

The drafter uses `gpt-5.6-sol` with `reasoning.effort=low`, the exact requested
combination. OpenAI's current model documentation lists `low` as supported and
recommends it for latency-sensitive workloads:

- [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)
