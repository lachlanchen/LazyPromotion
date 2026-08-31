[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*本当の困りごとを見つけ、役立つ回答を書き、関係性を明示し、送信するかは人が決める。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion は、ローカルで動くレビュー優先のソーシャル需要発見アシスタントです。可視の永続 Chrome プロファイルから Reddit、X、Instagram の実際の Web UI を検索し、候補を SQLite に記録し、低推論の `gpt-5.6-sol` で根拠のある返信を一件だけ下書きして、公開送信の直前で停止します。大量マーケティングではなく、関連するオープンソース成果で人を助けるためのツールです。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 運用契約

- 役立つことを優先：プロジェクトを紹介する前に、相手の具体的な問題に答えます。
- 関係性を明示：「私が保守しています」「私が作りました」など、自己のリンクであることを隠しません。
- 一人に一つの判断：大量返信、未承諾 DM、自動投票・フォロー・反応ループは行いません。
- 厳密な承認：下書きを変更すると、内容ハッシュに紐づく短期承認は無効になります。
- 可視の操作：Chrome は noVNC 上で動き、証拠スクリーンショットは Git の対象外です。
- セッションは非公開：認証情報、Cookie、プロファイル、候補、下書き、承認をリポジトリに入れません。

## 現在の内容

| パス | 役割 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台帳、照合、Codex 下書き、承認 |
| [`browser.py`](../browser.py) | Playwright/CDP による発見、確認、入力、保護された送信 |
| [`catalog.json`](../catalog.json) | 実際のニーズと保守中プロジェクトの根拠付き対応表 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 一つの永続 Xvfb/x11vnc/noVNC/Chrome デスクトップ |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | オープンソース候補の評価 |
| [`tests/`](../tests/) | 照合、冪等性、厳密承認のテスト |

## クイックスタート

Linux、Python 3.10+、Chrome、Python 版 Playwright、Xvfb、x11vnc、noVNC/websockify、`tmux`、ログイン済み Codex CLI が必要です。

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

noVNC で手動ログインし、明確なニーズを対象に小さく検索します。

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

人が宛先と全文を確認した後に限り送信します。

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## ランタイム分離

既定ではディスプレイ `:116`、VNC `127.0.0.1:5936`、noVNC `127.0.0.1:6136`、CDP `127.0.0.1:9436`、セッション `lazypromotion-browser` を使います。全サービスはループバックだけにバインドされ、未知の使用中ポートを拒否し、自身の記録で古いと確認できるディスプレイロックだけを削除します。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## オープンソース基盤

初版は大規模スケジューラや検出回避フレームワークではなく、Playwright と SQLite を選びました。Postiz と Mixpost は計画的なキャンペーンに使えますが、自動反応や回避機能はこのレビュー優先フローに含めません。[評価全文](../docs/open-source-evaluation.md)を参照してください。

## 検証

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

## 引用

研究で LazyPromotion を使用する場合はリポジトリを引用してください。GitHub は [`CITATION.cff`](../CITATION.cff) を読み取り、**Cite this repository** パネルを表示します。

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## 状態と範囲

Linux 向けの初期版です。外部サイトのセレクタは変更される場合があります。正確性、コミュニティ規則、プラットフォーム規約、関係性の開示、最終送信の責任は人間の運用者にあります。
