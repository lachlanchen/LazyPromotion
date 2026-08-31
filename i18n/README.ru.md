[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Найти реальную потребность, написать полезный ответ, раскрыть свою связь с проектом и оставить решение об отправке человеку.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion — локальный помощник для поиска запросов в социальных сетях с обязательной проверкой человеком. Он работает с настоящим веб-интерфейсом Reddit, X или Instagram в видимом постоянном профиле Chrome, сохраняет возможные совпадения в SQLite, создаёт обоснованный черновик через `gpt-5.6-sol` с низким уровнем рассуждения и останавливается до публичной отправки. Цель — помочь подходящим открытым проектом, а не автоматизировать массовую рекламу.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Правила работы

- Сначала польза: ответ решает конкретную задачу до упоминания проекта.
- Честная аффилиация: собственная ссылка сопровождается словами «я поддерживаю…» или «я создал…».
- Один человек — одно решение: без массовых ответов, нежелательных личных сообщений, автоматических голосов, подписок и циклов вовлечения.
- Точное одобрение: любое изменение черновика аннулирует краткосрочное одобрение, связанное с хешем.
- Видимая работа: Chrome открыт через noVNC, а локальные снимки исключены из Git.
- Сеансы остаются приватными: учётные данные, cookies, профили, кандидаты, черновики и одобрения не попадают в репозиторий.

## Содержимое

| Путь | Назначение |
| --- | --- |
| [`promotion.py`](../promotion.py) | Журнал SQLite, сопоставление, черновики Codex и одобрения |
| [`browser.py`](../browser.py) | Поиск Playwright/CDP, проверка, подготовка и защищённая отправка |
| [`catalog.json`](../catalog.json) | Обоснованное соответствие потребностей поддерживаемым проектам |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Один постоянный рабочий стол Xvfb/x11vnc/noVNC/Chrome |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Сравнение открытых решений |
| [`tests/`](../tests/) | Тесты совпадений, идемпотентности и точного одобрения |

## Быстрый старт

Нужны Linux, Python 3.10+, Chrome, Playwright для Python, Xvfb, x11vnc, noVNC/websockify, `tmux` и авторизованная CLI Codex.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Войдите вручную через noVNC и выполните узкий поиск по конкретной потребности:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Только после проверки точного адресата и текста:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## Изоляция среды

По умолчанию используются дисплей `:116`, VNC `127.0.0.1:5936`, noVNC `127.0.0.1:6136`, CDP `127.0.0.1:9436` и сессия `lazypromotion-browser`. Все службы доступны только через loopback. Запуск отклоняет неизвестные занятые порты и удаляет лишь собственную подтверждённо устаревшую блокировку дисплея.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Основа из открытого ПО

Первая версия использует Playwright и SQLite вместо крупного планировщика или средств обхода обнаружения. Postiz и Mixpost могут пригодиться для запланированных кампаний; функции обхода и автоматического вовлечения других проектов не соответствуют процессу с обязательной проверкой. См. [полное сравнение](../docs/open-source-evaluation.md).

## Проверка

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

## Цитирование

Если вы используете LazyPromotion в исследовании, процитируйте репозиторий. GitHub читает [`CITATION.cff`](../CITATION.cff) и показывает панель **Cite this repository**.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## Статус и границы

Это ранняя версия для Linux. Селекторы сторонних сайтов могут меняться. За точность, правила сообщества, условия платформы, раскрытие аффилиации и окончательную отправку отвечает человек.
