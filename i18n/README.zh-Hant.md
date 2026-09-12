[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*找到真實需求，寫出有用回答，坦誠說明關聯，再由人決定是否送出。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion 是一款在本機執行、先審後發的社交需求探索助手。它透過一個可見的專用 Chrome 設定檔操作 Reddit、X、Instagram 與 Hacker News 的真實網頁，把可能的配對記錄到 SQLite，使用登入帳戶所支援並建議的 Codex 模型與低推理強度起草有依據的回覆，並在公開送出前停止。它適合希望以相關開源成果幫助真實使用者的維護者，而不是把社群變成銷售隊列。

儲存庫也維護 `lachlanchen` 名下 108 個未封存公開原始碼儲存庫的清單，並把程式碼、書籍、知識圖譜、研究、媒體、語言學習與本地 AI 組合成以買方問題為中心、受證據門檻約束的機會。九條範圍固定的服務路線用來支持第一個經核實的 1,000 美元目標；點擊、Star、申請與排程中的貼文一律不算收入。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 運作約定

- 幫助優先：先回答對方的具體問題，再提及專案。
- 關聯透明：分享自己的連結時，以「我維護……」或「我開發了……」等自然措辭說明關係。
- 精確需求而非關鍵字重疊：在模型分流前過濾舊文、意圖含糊、自我推廣、引文中的求助與有歧義的短語。
- 及時脈絡：一般的公開協助候選項會在七天後過期；明確的付費機會保留 30 天審閱窗口，但聯絡前仍須即時確認機會尚未關閉。
- 先有證據再提供服務：商業路線必須具備可檢查的公開證明、書面範圍、明確排除項目與適配檢查。
- 一人一決策：不大量回覆、不發未經請求的私訊，也不自動投票、追蹤、反覆接觸或製造互動循環。
- 精確核准：草稿一經修改，與內容雜湊綁定的短期核准立即失效；送出目標與內容必須和人工審閱一致。
- 可見操作：瀏覽器工作只使用專用 noVNC Chrome 設定檔；個人 Firefox 視窗完全不在操作範圍內。
- 預設私密：憑證、Cookie、客戶資料、候選內容、草稿、核准、付款資料與執行證據都不會進入 Git。
- 嚴格計量：狀態依次為「關注 → 有幫助的互動 → 適配詢問 → 合格線索 → 接受範圍 → 確認付款 → 已交付 → 實際入帳」；退款另行記錄，任何一步都不得憑瀏覽量或樂觀推斷。

## 目前內容

| 路徑 | 用途 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台帳、需求配對、Codex 分流與起草，以及與雜湊綁定的核准 |
| [`browser.py`](../browser.py) | Playwright/CDP 探索、檢查、撰寫框準備與受控送出 |
| [`worker.py`](../worker.py) | 有限次數、帶冷卻的探索工作與私密審閱佇列；絕不自行送出 |
| [`catalog.json`](../catalog.json) 與 [`github-repos.json`](../github-repos.json) | 人工整理的需求配對規則與公開儲存庫清單 |
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | 對所有目前公開原始碼儲存庫進行私密、唯讀的關注度稽核；GitHub 流量永遠不計作潛在線索或收入 |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | 針對買方問題組合程式碼、書籍、知識系統與媒體的機會清單 |
| [`bounties.py`](../bounties.py) | 將公開懸賞與 GitHub 即時狀態核對，並拒絕不安全或已有爭議的工作 |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | 唯讀輪詢專案自有的 Bounty agent feed，僅將新的 ID 或版本轉成私密審閱提醒 |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | 依真實問題領域整理的完整公開作品地圖 |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | 帶證明要求與交付門檻的機會排序與服務約定 |
| [`docs/first-1000.md`](../docs/first-1000.md) | 九條有邊界的 250/400/500 美元服務路線與不誇大的里程碑計算 |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | 目前從作品集到收入的決策、註冊門檻與外部機會證據 |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | 面向基礎設施、程式碼稽核、多語工作與資格門檻的最新全球付費路線篩查 |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | 針對驗證、agent 任務設計、發音與本地知識工作的即時買方需求排序 |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | 目前直接路線篩查、證據缺口與提交門檻 |
| [`metrics.py`](../metrics.py)、[`network.py`](../network.py) 與 [`signals.py`](../signals.py) | 有證據門檻的漏斗、公開關係圖與第一方需求訊號 |
| [`owned_monitor.py`](../owned_monitor.py)、[`threads_inbound_monitor.py`](../threads_inbound_monitor.py)、[`github_inbound_monitor.py`](../github_inbound_monitor.py) 與 [`lkt_inbox.py`](../lkt_inbox.py) | 唯讀發布監測、Threads 回覆提醒、公開 issue 提醒與私密適配詢問收件 |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | 以彙總私密狀態唯讀偵測真實入帳；絕不建立 Stripe 物件或自動記帳收入 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 單一持久化 Xvfb/x11vnc/noVNC/Chrome 桌面 |
| [`application_watch.py`](../application_watch.py) 與 [`application_inbox_monitor.py`](../application_inbox_monitor.py) | 直接與分組申請的到期審閱日程，加上對已知申請對話串的唯讀彙總比對；執行中的監控器只嵌入隱私受限的到期摘要，絕不開啟郵件或跟進 |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | 透過一個重用的專案分頁監測已提交 Freelancer 出價的彙總訊息徽章或狀態變化，不開啟訊息也不回覆 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 可稽核的開源與 MCP 工具選擇 |

## 快速開始

需要 Linux、Python 3.10+、Chrome、Playwright for Python、Xvfb、x11vnc、`wmctrl`、noVNC/websockify、`tmux`，以及已登入的 Codex CLI。

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

在 noVNC 中手動登入，再針對明確需求進行小範圍搜尋：

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

如果即時貼文已解決或不再適配，應附上準確的公開證據在本機關閉候選項，而不是再起草一則回覆：

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

只有在人確認正確目標與完整文字後：

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

同一套探索流程支援 Reddit、X、Instagram 與 Hacker News。Hacker News 只用於研究：LazyPromotion 不會為它起草、核准、準備或送出留言。經人工審閱的第一方內容可以交由 Postiz 排程，但這條流程始終與面向社群成員的回覆分開。工作器、付款、聯盟行銷、交付、Postiz 與瀏覽器的詳細流程位於 [`docs/`](../docs/) 中。

可以篩查公開 GitHub 懸賞，而不認領或更改 issue：

```bash
python bounties.py
```

此看板僅用於探索。稽核器會核驗 issue 即時狀態和現有解決方案 pull request，拒絕不安全的指令要求，並將私密報告寫入 `.local/`。

也可以監控專案自有的 Bounty agent feed，而不留言、認領、傳訊息、下載附件或提交工作：

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

首次執行只會靜默建立私密基線。之後僅在出現新的可用 Bounty ID 或更高版本時提醒；五分鐘的最短間隔可防止過於頻繁的輪詢。詳見 [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md)。

可以觀察目前十五個高關注度或有服務路線儲存庫中的新公開 issue 和 pull request 活動，而不讀取正文或寫入 GitHub：

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

首次執行只會建立私密基線。之後僅提醒保留狀態中沒有的 issue 鍵。迴圈間隔不得短於 15 分鐘。固定允許清單與安全約定見 [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md)。

可以監測真實 Stripe 收款，而不建立 checkout 或保留客戶及付款詳情：

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

監控器只發出私密審閱提醒。付款只有在配對到已接受的範圍、產品訂單或捐款脈絡後才會計入。詳見 [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md)。

可以在專用瀏覽器的一個已登入專案分頁中依序檢查已提交的 Freelancer 出價：

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

監控器只記錄 campaign ID、彙總徽章數量、出價狀態與排名和 proposal 數量。它從不開啟對話或傳送回覆。詳見 [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md)。

## 執行隔離

啟動器只擁有一個 1920×1080 顯示器（`:116`）、VNC 連接埠 `5936`、noVNC 連接埠 `6136` 與回環 CDP 連接埠 `9436`。它重用一個持久化的專案專用 Chrome 設定檔，拒絕被未知程序占用的連接埠，記錄一份私密執行交接，且只清理自己擁有的過期資源。主機查看器應在 GNOME 工作區內最大化，但絕不進入全螢幕；沒有等待中的可見審閱時應停止整套服務。個人 Firefox 不屬於這套執行環境，也不得讀取、移動或重用其中的分頁與登入狀態。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 開源基線

核心刻意保持精簡：Playwright 負責可見瀏覽器，SQLite 保存耐久的本地狀態，帳戶支援的 Codex 模型負責結構化分流與起草。Postiz 只用於經過審閱的第一方排程。MCP 接入為可選並鎖定版本；模型子程序不會取得瀏覽器、排程器、憑證或付款權限。請見[完整評估](../docs/open-source-evaluation.md)。

作品集層不會一次推廣全部 108 個儲存庫，而是把公開專案整理成明確的機會約定。目前九條有界路線包括：本地資料集適配、論文修訂紅線、雙語講座交付、故事短片、書籍樣稿、KiCad 外掛評估、OpenHI 復現、LazyRemote 拓撲審查與發音微課。AI 短片組裝繼續暫停，直到更有說服力的證明通過人工審閱。可重現的 [KiCad 外掛評估樣例](../examples/kicad-plugin-evaluation/)為這條新路線提供支持；精簡的[受來源約束的教學提示樣例](../examples/source-bounded-educational-prompt/)則在面向學習者的工作中體現同樣的輸入、約束、證據與評估規範。詞彙資料匯入是可重用的 LKT 專項能力，並不表示某個已經關閉的市場需求仍然有效。

## 驗證

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
git diff --check
```

這些檢查驗證本地約定，但不證明第三方服務可用、社群配對正確、翻譯品質合格、客戶結果成立或已經產生收入。

## 引用

如果在研究中使用 LazyPromotion，請引用本儲存庫。GitHub 會讀取 [`CITATION.cff`](../CITATION.cff) 並顯示 **Cite this repository** 面板。

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## 狀態與範圍

這是以 Linux 為先的早期版本。第三方頁面選擇器、平台規則與帳戶能力都可能變動。探索和起草只是輔助，不代表某則回覆應當發布。操作者始終負責正確性、內容權利、關係揭露、社群適配、平台條款、付款複核與最後送出。
