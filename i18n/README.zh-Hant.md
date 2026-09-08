[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*找到真實需求，寫出有用回答，坦誠說明關聯，再由人決定是否送出。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion 是一款在本機執行、先審後發的社交需求探索助手。它透過一個可見的專用 Chrome 設定檔操作 Reddit、X、Instagram 與 Hacker News 的真實網頁，把可能的配對記錄到 SQLite，使用登入帳戶所支援並建議的 Codex 模型與低推理強度起草有依據的回覆，並在公開送出前停止。它適合希望以相關開源成果幫助真實使用者的維護者，而不是把社群變成銷售隊列。

儲存庫也維護 `lachlanchen` 名下 108 個未封存公開原始碼儲存庫的清單，並把程式碼、書籍、知識圖譜、研究、媒體、語言學習與本地 AI 組合成以買方問題為中心、受證據門檻約束的機會。六條範圍固定的服務路線用來支持第一個經核實的 1,000 美元目標；點擊、Star、申請與排程中的貼文一律不算收入。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 運作約定

- 幫助優先：先回答對方的具體問題，再提及專案。
- 關聯透明：分享自己的連結時，以「我維護……」或「我開發了……」等自然措辭說明關係。
- 精確需求而非關鍵字重疊：在模型分流前過濾舊文、意圖含糊、自我推廣、引文中的求助與有歧義的短語。
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
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | 針對買方問題組合程式碼、書籍、知識系統與媒體的機會清單 |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | 依真實問題領域整理的完整公開作品地圖 |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | 帶證明要求與交付門檻的機會排序與服務約定 |
| [`docs/first-1000.md`](../docs/first-1000.md) | 六條有邊界的 250/500 美元服務路線與不誇大的里程碑計算 |
| [`metrics.py`](../metrics.py)、[`network.py`](../network.py) 與 [`signals.py`](../signals.py) | 有證據門檻的漏斗、公開關係圖與第一方需求訊號 |
| [`owned_monitor.py`](../owned_monitor.py) 與 [`lkt_inbox.py`](../lkt_inbox.py) | 唯讀發布監測與私密適配詢問收件 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 單一持久化 Xvfb/x11vnc/noVNC/Chrome 桌面 |
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

只有在人確認正確目標與完整文字後：

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

同一套探索流程支援 Reddit、X、Instagram 與 Hacker News。Hacker News 只用於研究：LazyPromotion 不會為它起草、核准、準備或送出留言。經人工審閱的第一方內容可以交由 Postiz 排程，但這條流程始終與面向社群成員的回覆分開。工作器、付款、聯盟行銷、交付、Postiz 與瀏覽器的詳細流程位於 [`docs/`](../docs/) 中。

## 執行隔離

啟動器只擁有一個 1920×1080 顯示器（`:116`）、VNC 連接埠 `5936`、noVNC 連接埠 `6136` 與回環 CDP 連接埠 `9436`。它重用一個持久化的專案專用 Chrome 設定檔，拒絕被未知程序占用的連接埠，記錄一份私密執行交接，且只清理自己擁有的過期資源。主機查看器應在 GNOME 工作區內最大化，但絕不進入全螢幕；沒有等待中的可見審閱時應停止整套服務。個人 Firefox 不屬於這套執行環境，也不得讀取、移動或重用其中的分頁與登入狀態。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 開源基線

核心刻意保持精簡：Playwright 負責可見瀏覽器，SQLite 保存耐久的本地狀態，帳戶支援的 Codex 模型負責結構化分流與起草。Postiz 只用於經過審閱的第一方排程。MCP 接入為可選並鎖定版本；模型子程序不會取得瀏覽器、排程器、憑證或付款權限。請見[完整評估](../docs/open-source-evaluation.md)。

作品集層不會一次推廣全部 108 個儲存庫，而是把公開專案整理成明確的機會約定。目前六條有界路線包括：本地資料集適配、論文修訂紅線、雙語講座交付、故事短片、書籍樣稿與 AI 短片組裝。詞彙資料匯入是可重用的 LKT 專項能力，並不表示某個已經關閉的市場需求仍然有效。

## 驗證

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
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
