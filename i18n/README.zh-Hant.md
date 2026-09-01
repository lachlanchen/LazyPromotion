[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*找到真實需求，寫出有用回答，坦誠說明關聯，再由人決定是否送出。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion 是一款在本機執行、先審後發的社交需求探索助手。它透過可見且持久化的 Chrome 設定檔操作 Reddit、X 或 Instagram 的真實網頁，把可能的配對記錄到 SQLite，使用低推理強度的 `gpt-5.6-sol` 起草有依據的回覆，並在公開送出前停止。它的目的，是用相關開源專案幫助別人，而不是進行大量行銷。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 運作約定

- 幫助優先：先回答對方的具體問題，再提及專案。
- 關聯透明：分享自己的連結時明確說「我維護……」或「我開發了……」。
- 一人一決策：不大量回覆、不發未經請求的私訊，也不自動投票、追蹤或製造互動循環。
- 識別跨版轉貼：同一作者內容完全相同的長文歸併為一個主要候選，優先保留已經回覆的版本。
- 預設關注新帖：記錄來源時間與討論數量；超過 30 天的貼文標記為過期，並拒絕產生草稿。
- 精確核准：草稿一經修改，與內容雜湊綁定的短期核准立即失效。
- 可見操作：Chrome 在 noVNC 中執行，本機證據截圖由 Git 忽略。
- 工作階段保持私密：憑證、Cookie、瀏覽器設定、候選內容、草稿與核准都不會進入儲存庫。

## 目前內容

| 路徑 | 用途 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台帳、專案配對、Codex 起草與核准 |
| [`browser.py`](../browser.py) | Playwright/CDP 搜尋、檢查、填寫與受控送出 |
| [`catalog.json`](../catalog.json) | 將真實需求映射到有依據的維護專案 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 單一持久化 Xvfb/x11vnc/noVNC/Chrome 桌面 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 開源方案評估 |
| [`tests/`](../tests/) | 配對、冪等性與精確核准測試 |

## 快速開始

需要 Linux、Python 3.10+、Chrome、Playwright for Python、Xvfb、x11vnc、noVNC/websockify、`tmux`，以及已登入的 Codex CLI。

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

## 執行隔離

預設在一個 3840×1080 顯示器（`:116`）上放置兩個互不重疊的 1920×1080 Chrome 區域，並共用同一個持久化設定檔。noVNC 在 `6138` 提供推廣區域、在 `6137` 提供聯盟區域、在 `6136` 提供全景；CDP 維持在 `127.0.0.1:9436`，工作階段為 `lazypromotion-browser`。所有服務只綁定回環位址；啟動器拒絕被未知程序占用的連接埠，只清理由自身記錄證明已失效的顯示鎖。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 開源基線

第一版選擇 Playwright 與 SQLite，而不是大型排程器或反偵測框架。Postiz 與 Mixpost 適合規劃好的活動；其他專案中的規避與自動互動功能不適合這種先審後發流程。請見[完整評估](../docs/open-source-evaluation.md)。

## 驗證

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

這是面向 Linux 的早期版本，第三方網站選擇器可能變動。正確性、社群規則、平台條款、關聯聲明與最終送出始終由人負責。
