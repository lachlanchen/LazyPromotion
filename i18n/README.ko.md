[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*실제 필요를 찾고, 유용한 답변을 쓰고, 관계를 밝힌 뒤, 보낼지는 사람이 결정합니다.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion은 로컬에서 실행되는 검토 우선 소셜 수요 탐색 도우미입니다. 하나의 보이는 영구 Chrome 프로필로 Reddit, X, Instagram의 실제 웹 UI를 검색하고, 후보를 SQLite에 기록하고, 낮은 추론 강도의 `gpt-5.6-sol`로 근거 있는 답글 하나를 작성한 뒤 공개 전송 직전에 멈춥니다. 대량 마케팅이 아니라 관련 오픈 소스 작업으로 사람을 돕기 위한 도구입니다.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 운영 원칙

- 도움 우선: 프로젝트를 언급하기 전에 상대의 구체적인 필요에 답합니다.
- 정직한 관계 공개: 자신의 링크에는 “제가 유지보수합니다” 또는 “제가 만들었습니다” 같은 설명을 붙입니다.
- 한 사람, 한 결정: 대량 답글, 원치 않는 DM, 자동 투표·팔로우·참여 루프를 만들지 않습니다.
- 교차 게시물 인식: 같은 작성자의 동일한 장문 사본은 하나의 대표 후보로 묶고, 이미 답변한 사본을 우선합니다.
- 최신 항목 우선: 원본 시각과 토론 규모를 기록하며 30일이 지난 게시물은 오래된 항목으로 표시해 초안 생성을 거부합니다.
- 정확한 승인: 초안을 바꾸면 콘텐츠 해시에 연결된 단기 승인이 무효가 됩니다.
- 보이는 운영: Chrome은 noVNC에서 실행되며 로컬 증거 스크린샷은 Git에서 제외됩니다.
- 비공개 세션: 자격 증명, 쿠키, 프로필, 후보, 초안, 승인은 저장소에 들어가지 않습니다.

## 현재 구성

| 경로 | 목적 |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite 원장, 프로젝트 매칭, Codex 초안 및 승인 |
| [`browser.py`](../browser.py) | Playwright/CDP 탐색, 검사, 작성 및 보호된 전송 |
| [`catalog.json`](../catalog.json) | 실제 필요와 유지보수 중인 프로젝트의 근거 기반 매핑 |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | 하나의 영구 Xvfb/x11vnc/noVNC/Chrome 데스크톱 |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | 오픈 소스 대안 평가 |
| [`tests/`](../tests/) | 매칭, 멱등성, 정확한 승인 테스트 |

## 빠른 시작

Linux, Python 3.10+, Chrome, Python용 Playwright, Xvfb, x11vnc, noVNC/websockify, `tmux`, 로그인된 Codex CLI가 필요합니다.

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

사람이 정확한 대상과 전체 문구를 검토한 뒤에만 전송합니다.

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## 런타임 격리

기본 설정은 1920×1080 디스플레이(`:116`) 하나, VNC 포트 `5936` 하나, noVNC 포트 `6136` 하나를 사용합니다. 모든 캠페인 및 제휴 탭은 동일한 영구 Chrome 프로필에 유지되며, 복원된 각 Chrome 창은 전체 데스크톱에 맞춰져 겹치는 잘린 영역 없이 정상적으로 전환할 수 있습니다. CDP는 `127.0.0.1:9436`, 세션은 `lazypromotion-browser`입니다. 모든 서비스는 루프백에만 바인딩되며, 알 수 없는 사용 중 포트를 거부하고 자체 기록으로 오래된 것이 확인된 디스플레이 잠금만 정리합니다.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## 오픈 소스 기반

첫 버전은 대형 스케줄러나 탐지 회피 프레임워크 대신 Playwright와 SQLite를 사용합니다. Postiz와 Mixpost는 계획된 캠페인에 유용하지만 자동 참여나 회피 기능은 이 검토 우선 흐름에 포함되지 않습니다. [전체 평가](../docs/open-source-evaluation.md)를 참고하세요.

## 검증

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

Linux 중심의 초기 버전입니다. 외부 사이트 선택자는 바뀔 수 있습니다. 정확성, 커뮤니티 규칙, 플랫폼 약관, 관계 공개, 최종 전송은 인간 운영자의 책임입니다.
