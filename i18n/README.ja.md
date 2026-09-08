[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*本当の困りごとを見つけ、役立つ回答を書き、関係性を明示し、送信するかは人が決める。*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion は、ローカルで動くレビュー優先のソーシャル需要発見アシスタントです。一つの可視 Chrome プロファイルで Reddit、X、Instagram、Hacker News の実際の Web UI を検索し、候補を SQLite に記録します。ログイン中のアカウントに推奨される Codex モデルを低い推論強度で使い、根拠に沿った返信案を作りますが、公開送信の直前で必ず停止します。コミュニティを販売先の一覧に変えず、関連するオープンソース成果で困っている人を助けたい保守者のための道具です。

このリポジトリは、アーカイブされていない `lachlanchen` の公開ソースリポジトリ 108 件も一覧化し、コード、書籍、知識グラフ、研究、メディア、語学学習、ローカル AI を、買い手の課題を起点とした根拠付きの機会へ組み合わせます。最初の検証済み売上 USD 1,000 に向けて、範囲を限定した六つのサービス経路を用意しています。クリック、スター、応募、返信、予約投稿は売上として数えません。

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 運用契約

- 役立つことを優先：プロジェクトを紹介する前に、相手の具体的な問題に答えます。
- 関係性を明示：「私が保守しています」「私が作りました」など、自己のリンクであることを隠しません。
- キーワードではなく正確なニーズ：古い投稿、曖昧な意図、自己宣伝、引用された依頼、複数の意味を持つ語は、モデルによる判定の前に除外します。
- 提案より先に根拠：商用の経路には、公開して確認できる実例、明記された範囲と除外事項、適合確認が必要です。
- 一人に一つの判断：大量返信、未承諾 DM、自動投票・フォロー・反応ループは行いません。
- 厳密な承認：下書きを変更すると、内容ハッシュに紐づく短期承認は無効になります。送信内容と送信先は、確認されたものと完全に一致しなければなりません。
- 可視の操作：ブラウザ作業には専用の noVNC Chrome プロファイルだけを使います。個人用 Firefox のウィンドウは対象外であり、触れません。
- 既定で非公開：認証情報、Cookie、顧客資料、候補、下書き、承認、決済情報、実行時の証拠を Git に入れません。
- 厳格な計測：注目、問い合わせ、範囲合意、支払確認、納品、返金、受領済み売上を別々の状態として記録します。前の状態から楽観的に推測して進めません。

## 現在の内容

| パス | 役割 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 台帳、照合、Codex による判定と下書き、ハッシュに紐づく承認 |
| [`browser.py`](../browser.py) | Playwright/CDP による発見、確認、入力準備、保護された送信 |
| [`worker.py`](../worker.py) | 回数制限とクールダウンを備えた発見処理と非公開レビュー待ち行列。送信はしない |
| [`catalog.json`](../catalog.json) と [`github-repos.json`](../github-repos.json) | ニーズとの精選された対応表と、公開リポジトリの一覧 |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | コード、書籍、知識システム、メディアを買い手の課題に沿って組み合わせた機会 |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | 実際の問題領域ごとに整理した公開成果の全体図 |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | 根拠と納品条件を含む、優先順位付きの機会契約 |
| [`docs/first-1000.md`](../docs/first-1000.md) | USD 250／USD 500 の範囲限定サービス六経路と、誇張しない節目の計算 |
| [`metrics.py`](../metrics.py)、[`network.py`](../network.py)、[`signals.py`](../signals.py) | 根拠が必要なファネル、公開グラフ、ファーストパーティ需要シグナル |
| [`owned_monitor.py`](../owned_monitor.py) と [`lkt_inbox.py`](../lkt_inbox.py) | 公開状況の読み取り専用監視と、非公開の適合確認受付 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | プロジェクト専用の Xvfb/x11vnc/noVNC/Chrome レビューデスクトップ一式 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 監査可能なオープンソースおよび MCP ツールの選定記録 |

## クイックスタート

Linux、Python 3.10+、Chrome、Python 版 Playwright、Xvfb、x11vnc、`wmctrl`、noVNC/websockify、`tmux`、ログイン済み Codex CLI が必要です。

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
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

人が宛先と全文を確認した後に限り送信します。

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

同じ発見サイクルは Reddit、X、Instagram、Hacker News に対応します。ただし Hacker News は調査専用で、そこでのコメントの下書き、承認、入力準備、送信はできません。Postiz によるレビュー済みの自社アカウント向け予約投稿は、コミュニティへの返信とは別の経路です。ワーカー、決済、アフィリエイト、納品、Postiz、ブラウザの詳細な手順は [`docs/`](../docs/) にあります。

## ランタイム分離

ランチャーは 1920×1080 のディスプレイ（`:116`）、VNC ポート `5936`、noVNC ポート `6136`、ループバック CDP ポート `9436` を一組だけ所有します。一つの永続 Chrome プロファイルを再利用し、未知のプロセスが使用中のポートは拒否し、非公開のランタイム引き継ぎ記録を一つだけ残し、自身が所有すると確認できた古い資源だけを片付けます。ホスト側のビューアは GNOME の作業領域内で最大化し、全画面表示にはしません。表示レビューを待っていないときはスタックを停止します。個人用 Firefox や他プロジェクトのブラウザセッションには接続しません。

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## オープンソース基盤

中核は意図的に小さく保っています。可視ブラウザには Playwright、永続するローカル状態には SQLite、構造化された判定と下書きにはアカウントで利用可能な Codex モデルを使います。Postiz はレビュー済みのファーストパーティ予約投稿にだけ使用します。MCP 接続は任意でバージョンを固定し、モデルの子プロセスにはブラウザ、スケジューラ、認証情報、決済へのアクセスを与えません。検出回避、未承諾の自動反応、無差別投稿はこの基盤に含めません。

ポートフォリオ層は、108 件すべてを一度に宣伝するのではなく、公開プロジェクトを明示的な機会契約へ変換します。現在の六経路は、ローカル資料コレクションの適合診断、論文原稿の赤入れ、二言語講義資料の納品、物語クリップ制作、書籍見本制作、AI クリップ組み立てです。各経路には範囲、根拠、除外事項、納品条件があります。語彙データの取り込みは再利用できる LKT の専門領域ですが、終了した非公開マーケット案件が今も募集中だとは主張しません。詳しい評価は [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) を参照してください。

## 検証

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

これらの検査が保証するのはローカルの契約だけです。第三者サービスの可用性、コミュニティとの適合、翻訳品質、顧客成果、売上は保証しません。売上の状態は `attention → helpful interaction → fit inquiry → qualified lead → scope accepted → payment confirmed → delivered → received revenue` と厳密に進み、確認できる証拠なしに状態を飛ばしません。

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

これは Linux を中心とした初期リリースです。第三者サイトのセレクタ、プラットフォーム規則、アカウント機能は変更されることがあります。発見や下書きは支援にすぎず、返信すべきだという証拠にはなりません。正確性、利用権、関係性の開示、コミュニティとの適合、プラットフォーム規約、決済内容の確認、最終送信は運用者が判断します。サービスの価格は納品範囲に対するものであり、スター数や反応数、将来の収益を約束するものではありません。
