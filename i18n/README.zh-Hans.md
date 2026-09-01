[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*找到真实需求，写出有用回答，坦诚说明关联，再由人决定是否发送。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion 是一款本地运行、先审后发的社交需求发现助手。它通过一个可见且持久化的 Chrome 配置文件操作 Reddit、X 或 Instagram 的真实网页，把可能匹配的内容记录到 SQLite，使用低推理强度的 `gpt-5.6-sol` 起草有依据的回复，并在公开发送前停止。它用于以相关开源项目帮助别人，而不是批量营销。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 运行约定

- 帮助优先：先回答对方的具体问题，再提及项目。
- 关联透明：分享自己的链接时明确说“我维护……”或“我开发了……”。
- 一人一决策：不批量回复、不发未经请求的私信，不自动投票、关注或制造互动循环。
- 识别跨版转发：同一作者内容完全一致的长帖归并到一个主候选项，优先保留已经回复的版本。
- 默认关注新帖：记录来源时间和讨论数量；超过 30 天的帖子标记为过期，并拒绝生成草稿。
- 精确批准：草稿一旦修改，与内容哈希绑定的短期批准立即失效。
- 可见操作：Chrome 在 noVNC 中运行，本地证据截图由 Git 忽略。
- 会话保持私密：凭据、Cookie、浏览器配置、候选内容、草稿和批准都不会进入仓库。

## 当前内容

| 路径 | 用途 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台账、项目匹配、Codex 起草与批准 |
| [`browser.py`](../browser.py) | Playwright/CDP 搜索、检查、填写与受控发送 |
| [`catalog.json`](../catalog.json) | 将真实需求映射到有依据的维护项目 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 单一持久化 Xvfb/x11vnc/noVNC/Chrome 桌面 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 开源方案评估 |
| [`tests/`](../tests/) | 匹配、幂等性和精确批准测试 |

## 快速开始

需要 Linux、Python 3.10+、Chrome、Playwright for Python、Xvfb、x11vnc、noVNC/websockify、`tmux`，以及已登录的 Codex CLI。

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

只有在人确认了准确目标和完整文字后：

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## 运行隔离

默认使用一个 1920×1080 显示器（`:116`）、一个 VNC 端口 `5936` 和一个 noVNC 端口 `6136`。所有推广与联盟标签页保存在同一个持久化 Chrome 配置中；恢复出的每个 Chrome 窗口都会铺满桌面，可正常切换，不再被裁成相互干扰的区域。CDP 保持为 `127.0.0.1:9436`，会话名为 `lazypromotion-browser`。所有服务只绑定回环地址；启动器拒绝占用中的未知端口，只清理由自身记录证明已经失效的显示锁。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 开源基线

首个版本选择 Playwright 与 SQLite，而不是大型排程器或反检测框架。Postiz 和 Mixpost 可用于经过规划的活动；其他项目中的规避和自动互动功能不适合这种先审后发的流程。详见[完整评估](../docs/open-source-evaluation.md)。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

这是面向 Linux 的早期版本，第三方网站选择器可能变化。准确性、社区规则、平台条款、关联声明和最终发送始终由人负责。
