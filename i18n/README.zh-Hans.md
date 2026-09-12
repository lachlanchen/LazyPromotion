[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*找到真实需求，写出有用回答，坦诚说明关联，再由人决定是否发送。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion 是一款本地运行、先审后发的社交需求发现助手。它通过一个可见的专用 Chrome 配置文件操作 Reddit、X、Instagram 和 Hacker News 的真实网页，把可能匹配的内容记录到 SQLite，使用登录账户所支持并推荐的 Codex 模型和低推理强度起草有依据的回复，并在公开发送前停止。它面向希望以相关开源成果帮助真实用户的维护者，而不是把社区变成销售队列。

仓库还维护 `lachlanchen` 名下 108 个未归档公开源码仓库的清单，并把代码、书籍、知识图谱、研究、媒体、语言学习和本地 AI 组合成以买方问题为中心、受证据门槛约束的机会。九条范围固定的服务路线用于支持第一个经核实的 1,000 美元目标；点击、Star、申请和排队中的帖子都不算收入。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 运行约定

- 帮助优先：先回答对方的具体问题，再提及项目。
- 关联透明：分享自己的链接时，用“我维护……”或“我开发了……”等自然措辞说明关系。
- 精确需求而非关键词重叠：在模型分流前过滤旧帖、意图含糊、自我推广、引用中的求助以及有歧义的短语。
- 及时语境：一般的公开帮助候选项会在七天后过期；明确的付费机会保留 30 天审阅窗口，但联系前仍须实时确认机会尚未关闭。
- 先有证据再提供服务：商业路线必须有可检查的公开证明、书面范围、明确排除项和适配检查。
- 一人一决策：不批量回复、不发未经请求的私信，不自动投票、关注、反复触达或制造互动循环。
- 精确批准：草稿一旦修改，与内容哈希绑定的短期批准立即失效；发送目标和内容必须与人工审阅的一致。
- 可见操作：浏览器工作只使用专用 noVNC Chrome 配置；个人 Firefox 窗口完全不在操作范围内。
- 默认私密：凭据、Cookie、客户材料、候选内容、草稿、批准、支付数据和运行证据都不会进入 Git。
- 严格计量：状态依次为“关注 → 有帮助的互动 → 适配咨询 → 合格线索 → 接受范围 → 确认付款 → 已交付 → 实际到账”；退款另行记录，任何一步都不能凭浏览量或乐观推断。

## 当前内容

| 路径 | 用途 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台账、需求匹配、Codex 分流与起草，以及与哈希绑定的批准 |
| [`browser.py`](../browser.py) | Playwright/CDP 发现、检查、撰写框准备与受控发送 |
| [`worker.py`](../worker.py) | 有限次数、带冷却的发现任务和私密审阅队列；永不自行发送 |
| [`catalog.json`](../catalog.json) 与 [`github-repos.json`](../github-repos.json) | 人工整理的需求匹配规则与公开仓库清单 |
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | 对所有当前公开源码仓库进行私密、只读的关注度审计；GitHub 流量永远不计作潜在线索或收入 |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | 面向买方问题组合代码、书籍、知识系统与媒体的机会清单 |
| [`bounties.py`](../bounties.py) | 将公开赏金与 GitHub 实时状态核对，并拒绝不安全或已有争议的工作 |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | 只读轮询项目自有的 Bounty agent feed，仅将新的 ID 或版本转为私密审阅提醒 |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | 按真实问题领域整理的完整公开作品地图 |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | 带证明要求和交付门槛的机会排序与服务约定 |
| [`docs/first-1000.md`](../docs/first-1000.md) | 九条有边界的 250/400/500 美元服务路线和不夸大的里程碑计算 |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | 当前从作品集到收入的决策、注册门槛与外部机会证据 |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | 面向基础设施、代码审计、多语言工作和资格门槛的最新全球付费路线筛查 |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | 针对验证、agent 任务设计、发音和本地知识工作的实时买方需求排序 |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | 当前直接路线筛查、证据缺口与提交门槛 |
| [`metrics.py`](../metrics.py)、[`network.py`](../network.py) 与 [`signals.py`](../signals.py) | 有证据门槛的漏斗、公开关系图与第一方需求信号 |
| [`owned_monitor.py`](../owned_monitor.py)、[`threads_inbound_monitor.py`](../threads_inbound_monitor.py)、[`github_inbound_monitor.py`](../github_inbound_monitor.py) 与 [`lkt_inbox.py`](../lkt_inbox.py) | 只读发布监测、Threads 回复提醒、公开 issue 提醒与私密适配咨询收件 |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | 以汇总私密状态只读检测真实入账；绝不创建 Stripe 对象或自动记账收入 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 单一持久化 Xvfb/x11vnc/noVNC/Chrome 桌面 |
| [`application_watch.py`](../application_watch.py) 与 [`application_inbox_monitor.py`](../application_inbox_monitor.py) | 直接与分组申请的到期审阅日程，加上对已知申请线程的只读汇总匹配；运行中的监控器只嵌入隐私受限的到期摘要，绝不打开邮件或跟进 |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | 通过一个复用的项目标签页监测已提交 Freelancer 出价的汇总消息徽标或状态变化，不打开消息也不回复 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 可审计的开源与 MCP 工具选择 |

## 快速开始

需要 Linux、Python 3.10+、Chrome、Playwright for Python、Xvfb、x11vnc、`wmctrl`、noVNC/websockify、`tmux`，以及已登录的 Codex CLI。

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

在 noVNC 中手动登录，然后围绕一个明确需求进行小范围搜索：

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

如果实时帖子已解决或不再适配，应附上准确的公开证据在本地关闭候选项，而不是再起草一条回复：

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

只有在人确认了准确目标和完整文字后：

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

同一套发现流程支持 Reddit、X、Instagram 和 Hacker News。Hacker News 只用于研究：LazyPromotion 不会为它起草、批准、准备或发送评论。经人工审阅的第一方内容可由 Postiz 排期，但这条流程始终与面向社区成员的回复分开。工作器、支付、联盟营销、交付、Postiz 和浏览器的详细流程位于 [`docs/`](../docs/) 中。

可以筛查公开 GitHub 赏金，而不认领或更改 issue：

```bash
python bounties.py
```

该看板仅用于发现。审计器会核验 issue 实时状态和现有解决方案 pull request，拒绝不安全的指令请求，并将私密报告写入 `.local/`。

也可以监控项目自有的 Bounty agent feed，而不评论、认领、发消息、下载附件或提交工作：

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

首次运行只静默建立私密基线。以后仅在出现新的可用 Bounty ID 或更高版本时提醒；五分钟的最短间隔可防止过于频繁的轮询。详见 [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md)。

可以观察当前十五个高关注度或有服务路线仓库中的新公开 issue 和 pull request 活动，而不读取正文或写入 GitHub：

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

首次运行只建立私密基线。以后仅提醒保留状态中没有的 issue 键。循环间隔不得短于 15 分钟。固定白名单和安全约定见 [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md)。

可以监测真实 Stripe 收款，而不创建 checkout 或保留客户及支付详情：

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

监控器只发出私密审阅提醒。付款只有在匹配到已接受的范围、产品订单或捐赠语境后才会计入。详见 [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md)。

可以在专用浏览器的一个已登录项目标签页中依次检查已提交的 Freelancer 出价：

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

监控器只记录 campaign ID、汇总徽标数量、出价状态与排名和 proposal 数量。它从不打开对话或发送回复。详见 [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md)。

## 运行隔离

启动器只拥有一个 1920×1080 显示器（`:116`）、VNC 端口 `5936`、noVNC 端口 `6136` 和回环 CDP 端口 `9436`。它复用一个持久化的项目专用 Chrome 配置，拒绝被未知进程占用的端口，记录一份私密运行交接，并且只清理自己拥有的过期资源。宿主机查看器应在 GNOME 工作区内最大化，但绝不进入全屏；没有等待中的可见审阅时应停止整套服务。个人 Firefox 不属于这套运行环境，也不得读取、移动或复用其中的标签页和登录状态。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 开源基线

核心刻意保持精简：Playwright 负责可见浏览器，SQLite 保存耐久的本地状态，账户支持的 Codex 模型负责结构化分流与起草。Postiz 只用于经过审阅的第一方排期。MCP 接入是可选且锁定版本的；模型子进程不会获得浏览器、排程器、凭据或支付权限。详见[完整评估](../docs/open-source-evaluation.md)。

作品集层不会一次推广全部 108 个仓库，而是把公开项目整理成明确的机会约定。目前九条有界路线包括：本地资料集适配、论文修订红线、双语讲座交付、故事短片、书籍样稿、KiCad 插件评估、OpenHI 复现、LazyRemote 拓扑审查和发音微课。AI 短片组装继续暂停，直到更有说服力的证明通过人工审阅。可复现的 [KiCad 插件评估样例](../examples/kicad-plugin-evaluation/)为这条新路线提供支持；精简的[受来源约束的教学提示样例](../examples/source-bounded-educational-prompt/)则在面向学习者的工作中体现同样的输入、约束、证据和评估规范。词汇数据导入是可复用的 LKT 专项能力，并不表示某个已经关闭的市场需求仍然有效。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
git diff --check
```

这些检查验证本地约定，但不证明第三方服务可用、社区匹配正确、翻译质量合格、客户结果成立或已经产生收入。

## 引用

如果在研究中使用 LazyPromotion，请引用本仓库。GitHub 会读取 [`CITATION.cff`](../CITATION.cff) 并显示 **Cite this repository** 面板。

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## 状态与范围

这是以 Linux 为先的早期版本。第三方页面选择器、平台规则和账户能力都可能变化。发现和起草只是辅助，不等于某条回复应当发布。操作者始终负责准确性、内容权利、关系披露、社区适配、平台条款、支付复核和最后发送。
