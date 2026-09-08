[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*실제 필요를 찾고, 유용한 답변을 쓰고, 관계를 밝힌 뒤, 보낼지는 사람이 결정합니다.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion은 로컬에서 실행되는 검토 우선 소셜 수요 탐색 도우미입니다. 하나의 보이는 Chrome 프로필에서 Reddit, X, Instagram, Hacker News의 실제 웹 인터페이스를 검색하고, 가능한 연결점을 SQLite에 기록하며, 로그인한 계정에 권장되는 Codex 모델을 낮은 추론 강도로 사용해 근거 있는 답글을 작성합니다. 그러나 공개 전송 직전에는 반드시 멈춥니다. 커뮤니티를 영업 목록으로 바꾸지 않으면서 관련 오픈 소스 작업으로 사람을 돕고 싶은 유지보수자를 위한 도구입니다.

이 저장소에는 보관 처리되지 않은 `lachlanchen` 공개 소스 저장소 108개의 목록도 있습니다. 코드, 책, 지식 그래프, 연구, 미디어, 언어 학습, 로컬 AI를 서로 결합하되, 구매자가 실제로 이해할 수 있고 공개 증거로 뒷받침되는 기회만 제시합니다. 첫 번째로 검증된 매출 USD 1,000을 향한 고정 범위 서비스 경로는 여섯 가지입니다. 클릭, 별, 지원서, 예약 게시물은 매출로 계산하지 않습니다.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 운영 원칙

- 도움 우선: 프로젝트를 언급하기 전에 상대의 구체적인 필요에 답합니다.
- 정직한 관계 공개: 자신의 링크에는 “제가 유지보수합니다” 또는 “제가 만들었습니다” 같은 설명을 붙입니다.
- 단어가 아니라 필요를 대조: 오래된 게시물, 모호한 의도, 자기 홍보, 인용된 요청, 여러 뜻으로 해석되는 문구는 모델 분류 전에 걸러냅니다.
- 제안보다 증거 우선: 상업 서비스가 되려면 확인 가능한 공개 증거, 서면 범위, 제외 사항, 적합성 확인 절차가 있어야 합니다.
- 한 사람, 한 결정: 대량 답글, 원치 않는 DM, 자동 투표·팔로우, 반복 접촉, 참여 루프를 만들지 않습니다.
- 정확한 승인: 초안을 편집하면 짧은 유효기간과 콘텐츠 해시에 연결된 승인이 무효가 됩니다. 전송되는 목적지와 문구는 검토한 내용과 정확히 같아야 합니다.
- 보이는 운영: 브라우저 작업은 전용 noVNC Chrome 프로필에서만 합니다. 개인 Firefox 창은 작업 범위에 포함되지 않습니다.
- 기본은 비공개: 자격 증명, 쿠키, 고객 자료, 후보, 초안, 승인, 결제 정보, 런타임 증거는 Git에 넣지 않습니다.
- 엄격한 측정: `관심 → 유용한 상호작용 → 적합성 문의 → 적격 리드 → 범위 수락 → 결제 확인 → 납품 → 수령 매출`은 서로 다른 상태입니다. 방문이나 낙관만으로 다음 상태를 추정하지 않습니다.

## 현재 구성

| 경로 | 목적 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 원장, 매칭, Codex 분류·초안, 해시에 연결된 승인 |
| [`browser.py`](../browser.py) | Playwright/CDP 탐색, 검사, 작성창 준비, 보호된 전송 |
| [`worker.py`](../worker.py) | 전송 기능 없이, 유한한 검색과 대기 시간을 적용하는 비공개 검토 대기열 |
| [`catalog.json`](../catalog.json) 및 [`github-repos.json`](../github-repos.json) | 선별된 필요 매칭과 공개 저장소 108개의 목록 |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | 코드, 책, 지식 시스템, 미디어를 구매자 문제 중심으로 결합한 기회 |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | 실제 문제 영역별로 정리한 공개 작업 전체 지도 |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | 증거와 납품 조건을 포함한 우선순위별 기회 계약 |
| [`docs/first-1000.md`](../docs/first-1000.md) | 범위가 정해진 USD 250·USD 500 서비스 여섯 가지와 정직한 목표 계산 |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py), [`signals.py`](../signals.py) | 증거 기반 퍼널, 공개 관계 그래프, 자사 채널 수요 신호 |
| [`owned_monitor.py`](../owned_monitor.py) 및 [`lkt_inbox.py`](../lkt_inbox.py) | 읽기 전용 게시 상태 감시와 비공개 적합성 문의 수신 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 프로젝트 전용 Xvfb/x11vnc/noVNC/Chrome 검토 데스크톱 하나 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 감사 가능한 오픈 소스 및 MCP 도구 선택 근거 |

## 빠른 시작

Linux, Python 3.10+, Chrome, Python용 Playwright, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux`, 로그인된 Codex CLI가 필요합니다.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

noVNC에서 직접 로그인한 뒤 하나의 명확한 필요를 중심으로 작은 검색을 실행합니다.

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

사람이 정확한 대상과 전체 문구를 확인한 뒤에만 전송합니다.

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

같은 탐색 흐름이 Reddit, X, Instagram, Hacker News를 지원합니다. 다만 Hacker News는 조사 전용이므로 LazyPromotion에서 댓글 초안 작성, 승인, 작성창 준비, 전송을 할 수 없습니다. Postiz를 통한 검토된 자사 채널 예약 발행도 커뮤니티 답글과 별도로 운영합니다. 작업자, 결제, 제휴, 납품, Postiz, 브라우저에 관한 자세한 절차는 [`docs/`](../docs/)에 있습니다.

## 런타임 격리

실행기는 1920×1080 디스플레이(`:116`) 하나, VNC 포트 `5936`, noVNC 포트 `6136`, 루프백 CDP 포트 `9436`을 소유합니다. 영구 Chrome 프로필 하나를 재사용하고, 출처를 모르는 점유 포트에서는 시작을 거부하며, 비공개 런타임 인계 문서 하나를 기록하고, 자신이 소유한 오래된 리소스만 정리합니다. 호스트의 뷰어는 GNOME 작업 영역 안에서 최대화하되 절대 전체 화면으로 전환하지 않습니다. 보이는 검토를 기다리는 사람이 없으면 스택을 중지합니다. 개인 Firefox는 열거나 건드리지 않습니다.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 오픈 소스 기반

핵심 구성은 의도적으로 작게 유지합니다. 보이는 브라우저에는 Playwright, 지속 가능한 로컬 상태에는 SQLite, 구조화된 분류와 초안에는 로그인 계정이 지원하는 Codex 모델을 사용합니다. Postiz는 검토를 마친 자사 채널 예약 발행에만 사용합니다. MCP 연결은 선택 사항이며 버전을 고정합니다. 모델 하위 프로세스에는 브라우저, 예약 발행기, 자격 증명, 결제 권한을 넘기지 않습니다.

포트폴리오 계층은 저장소를 한꺼번에 홍보하는 대신 공개 프로젝트를 명시적인 기회 계약으로 바꿉니다. 현재 서비스 경로는 로컬 자료 컬렉션 적합성 진단, 논문 수정본 대조, 이중 언어 강의 자료 납품, 스토리 클립, 책 샘플 제작, AI 클립 조립입니다. 어휘 데이터 수집은 재사용 가능한 LKT 전문 영역이지만, 종료된 외부 마켓플레이스 공고가 아직 열려 있다는 주장은 하지 않습니다. 선택 근거는 [전체 오픈 소스 및 MCP 평가](../docs/open-source-evaluation.md)에서 확인할 수 있습니다.

## 검증

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

이 검사는 로컬 계약을 검증할 뿐, 외부 서비스의 가용성, 커뮤니티 적합성, 번역 품질, 고객 성과, 매출을 보증하지 않습니다.

## 인용

연구에서 LazyPromotion을 사용한다면 저장소를 인용해 주세요. GitHub는 [`CITATION.cff`](../CITATION.cff)를 읽고 **Cite this repository** 패널을 표시합니다.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## 상태와 범위

Linux 중심의 초기 버전입니다. 외부 사이트 선택자, 플랫폼 규칙, 계정 기능은 바뀔 수 있습니다. 탐색과 초안은 답글을 올려야 한다는 근거가 아니라 판단 보조 수단입니다. 정확성, 저작권과 이용 권한, 관계 공개, 커뮤니티 적합성, 플랫폼 약관, 결제 검토, 최종 전송에 대한 책임은 운영자에게 있습니다.
