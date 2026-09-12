[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Найти реальную потребность, написать полезный ответ, раскрыть свою связь с проектом и оставить решение об отправке человеку.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion — локальный помощник для поиска запросов в социальных сетях с обязательной проверкой человеком. Он работает с настоящими веб-интерфейсами Reddit, X, Instagram и Hacker News в видимом выделенном профиле Chrome, сохраняет возможные совпадения в SQLite, создаёт обоснованные черновики через поддерживаемую и рекомендованную для учётной записи модель Codex с низким уровнем рассуждения и останавливается до публичной отправки. Инструмент предназначен для разработчиков, которые хотят помогать людям подходящими открытыми проектами, не превращая сообщества в очередь продаж.

Репозиторий также содержит открытый каталог 108 неархивированных исходных репозиториев `lachlanchen`. Код, книги, графы знаний, исследования, медиа, языковые материалы и локальный ИИ объединяются в возможности, сформулированные как конкретные задачи покупателей и ограниченные проверяемыми доказательствами. Основной MCP-аудит за 500 долларов и девять смежных услуг с фиксированным объёмом поддерживают цель первых подтверждённых 1000 долларов США; клики, звёзды, заявки и публикации в очереди доходом не считаются.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Правила работы

- Сначала польза: ответ решает конкретную задачу до упоминания проекта.
- Честная аффилиация: собственная ссылка сопровождается естественной фразой вроде «я поддерживаю…» или «я создал…».
- Точная потребность, а не совпадение слов: до модельного отбора исключаются старые записи, неясные намерения, самореклама, цитируемые просьбы и двусмысленные фразы.
- Актуальный контекст: обычные кандидаты для публичной помощи истекают через семь дней; явно оплачиваемые возможности остаются в окне проверки 30 дней, но перед контактом всё равно требуется проверить их доступность вживую.
- Сначала доказательства, затем предложение: коммерческому маршруту нужны доступное для проверки публичное подтверждение, письменный объём, исключения и проверка пригодности.
- Один человек — одно решение: без массовых ответов, нежелательных личных сообщений, автоматических голосов, подписок, повторных обращений и циклов вовлечения.
- Точное одобрение: любое изменение черновика аннулирует краткосрочное одобрение, связанное с хешем; адресат и текст отправки должны совпадать с проверенной версией.
- Видимая работа: браузерные действия выполняются только в выделенном профиле Chrome через noVNC; личные окна Firefox находятся вне области доступа.
- Приватность по умолчанию: учётные данные, cookies, клиентские материалы, кандидаты, черновики, одобрения, платёжные сведения и рабочие доказательства не попадают в Git.
- Строгий учёт: состояния идут отдельно — внимание → полезное взаимодействие → запрос на проверку пригодности → квалифицированный контакт → согласованный объём → подтверждённый платёж → выполненная работа → фактически полученный доход. Возвраты записываются отдельно; переход нельзя вывести из просмотров или ожиданий.

## Содержимое

| Путь | Назначение |
| --- | --- |
| [`promotion.py`](../promotion.py) | Журнал SQLite, сопоставление потребностей, отбор и черновики Codex, одобрение по хешу |
| [`browser.py`](../browser.py) | Обнаружение и проверка через Playwright/CDP, подготовка поля ответа и защищённая отправка |
| [`worker.py`](../worker.py) | Ограниченный поиск с периодами ожидания и приватная очередь проверки; ничего не отправляет |
| [`catalog.json`](../catalog.json) и [`github-repos.json`](../github-repos.json) | Ручные правила соответствия потребностей и открытый каталог репозиториев |
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | Приватный аудит внимания только для чтения по всем текущим публичным исходным репозиториям; трафик GitHub никогда не считается контактом или доходом |
| [`mcp_public_preflight.py`](../mcp_public_preflight.py) | Статическая предварительная проверка публичного GitHub-репозитория с фиксацией ревизии для MCP-аудита; код не клонируется и не запускается |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Сочетания кода, книг, систем знаний и медиа, сформированные вокруг задач покупателей |
| [`bounties.py`](../bounties.py) | Сверяет публичные вознаграждения с текущим состоянием GitHub и отклоняет небезопасную или уже оспариваемую работу |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | Опрашивает принадлежащий проекту поток Bounty только для чтения и создаёт приватные уведомления лишь для новых ID или версий |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Полная карта открытых работ, сгруппированная по реальным проблемам |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Ранжированные контракты возможностей с требованиями к доказательствам и поставке |
| [`docs/first-1000.md`](../docs/first-1000.md) | Основной MCP-маршрут за 500 долларов, девять смежных ограниченных услуг и честный расчёт этапа |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | Текущее решение о превращении портфолио в доход, регистрационные барьеры и доказательства внешних возможностей |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | Новая глобальная проверка платных маршрутов в инфраструктуре, аудите кода, многоязычной работе и квалификационных барьерах |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | Ранжированные актуальные задачи покупателей в проверке, проектировании заданий для агентов, произношении и локальных знаниях |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | Текущая проверка прямых маршрутов, пробелов в доказательствах и условий подачи |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) и [`signals.py`](../signals.py) | Воронка с доказательствами, открытый граф связей и собственные сигналы спроса |
| [`owned_monitor.py`](../owned_monitor.py), [`threads_inbound_monitor.py`](../threads_inbound_monitor.py), [`github_inbound_monitor.py`](../github_inbound_monitor.py) и [`lkt_inbox.py`](../lkt_inbox.py) | Мониторинг публикаций только для чтения, уведомления об ответах Threads и публичных issues, а также приватный приём запросов на проверку соответствия |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | Обнаруживает реальные платежи только для чтения с агрегированным приватным состоянием; не создаёт объекты Stripe и не записывает доход автоматически |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Один постоянный рабочий стол Xvfb/x11vnc/noVNC/Chrome |
| [`application_watch.py`](../application_watch.py) и [`application_inbox_monitor.py`](../application_inbox_monitor.py) | Расписание проверок прямых и групповых заявок и агрегированное сопоставление известных цепочек только для чтения; работающий монитор включает лишь ограниченную для приватности сводку сроков и не открывает почту и не напоминает |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | Следит за отправленными ставками Freelancer через одну повторно используемую вкладку, замечая агрегированный значок сообщений или смену состояния, но не открывая сообщения и не отвечая |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Проверяемый выбор открытых инструментов и MCP |

## Быстрый старт

Нужны Linux, Python 3.10+, Chrome, Playwright для Python, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux` и авторизованная CLI Codex.

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
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Если задача в живой ветке уже решена или больше не подходит, закройте кандидата локально с точным публичным доказательством вместо подготовки ещё одного ответа:

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

Только после проверки точного адресата и текста:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

Один цикл обнаружения поддерживает Reddit, X, Instagram и Hacker News. Для Hacker News разрешено только исследование: LazyPromotion не создаёт, не одобряет, не подготавливает и не отправляет туда комментарии. Проверенное человеком планирование собственных публикаций через Postiz остаётся отдельным от ответов участникам сообществ. Подробные процедуры для рабочего процесса, платежей, партнёрских программ, поставки, Postiz и браузера находятся в каталоге [`docs/`](../docs/).

Публичные вознаграждения GitHub можно проверять, не заявляя права на issue и не меняя его:

```bash
python bounties.py
```

Доска служит только для обнаружения. Аудитор проверяет актуальное состояние issue и существующие pull requests с решениями, отклоняет опасные запросы инструкций и записывает приватный отчёт в `.local/`.

Принадлежащий проекту поток Bounty тоже можно наблюдать, не комментируя, не заявляя права, не отправляя сообщения, не загружая вложения и не представляя работу:

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

Первый проход тихо создаёт приватную исходную точку. Последующие проходы сообщают только о новом доступном ID Bounty или более высокой версии, а пятиминутный минимум предотвращает агрессивный опрос. См. [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md).

Новые публичные issues и активность pull requests в пятнадцати текущих репозиториях с высоким вниманием или предложениями можно наблюдать, не читая содержимое и не записывая ничего в GitHub:

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

Первый проход лишь создаёт приватную исходную точку. Последующие проходы сообщают только о ключах issues, которых ещё нет в сохранённом состоянии. Интервал цикла не может быть короче 15 минут. Фиксированный список и правила безопасности описаны в [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md).

Реальные поступления Stripe можно отслеживать, не создавая checkout и не сохраняя данные клиента или платежа:

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

Наблюдатель создаёт только приватное уведомление для проверки. Платёж учитывается после сопоставления с принятым объёмом, заказом продукта или пожертвованием. См. [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md).

Отправленные ставки Freelancer можно последовательно проверять через авторизованную вкладку проекта в выделенном браузере:

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

Монитор записывает лишь ID кампаний, агрегированное число на значке, состояние и место ставки, а также число предложений. Он никогда не открывает разговор и не отвечает. См. [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md).

## Изоляция среды

Запуск владеет ровно одним дисплеем 1920×1080 (`:116`), портом VNC `5936`, портом noVNC `6136` и локальным портом CDP `9436`. Он повторно использует один постоянный профиль Chrome только для этого проекта, отклоняет занятые неизвестными процессами порты, ведёт одну приватную запись передачи состояния и удаляет лишь собственные устаревшие ресурсы. Окно просмотра на основной системе следует развернуть в рабочей области GNOME, но не переводить в полноэкранный режим; когда видимая проверка не ожидается, весь стек нужно остановить. Личный Firefox к этой среде не относится: его вкладки и сеансы нельзя читать, перемещать или повторно использовать.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Основа из открытого ПО

Основа намеренно невелика: Playwright управляет видимым браузером, SQLite хранит устойчивое локальное состояние, а поддерживаемая учётной записью модель Codex выполняет структурированный отбор и подготовку черновиков. Postiz используется только для проверенного человеком планирования собственных материалов. Подключения MCP необязательны и закреплены по версиям; дочерний процесс модели не получает доступа к браузеру, планировщику, учётным данным или платежам. См. [полное сравнение](../docs/open-source-evaluation.md).

Слой портфолио превращает открытые проекты в явные контракты возможностей вместо одновременной рекламы всех репозиториев. Основной маршрут — MCP Server Pre-Deployment Review за 500 долларов; девять смежных маршрутов охватывают проверку пригодности локальной коллекции, редактуру рукописи с redline, двуязычную подготовку лекций, сюжетные клипы, книжные образцы, оценку плагинов KiCad, воспроизведение OpenHI, аудит топологии LazyRemote и мини-уроки произношения. Сборка роликов с ИИ остаётся на паузе, пока более убедительное доказательство не пройдёт проверку человеком. Воспроизводимый [пример оценки плагина KiCad](../examples/kicad-plugin-evaluation/) поддерживает новый ограниченный маршрут. Компактное [учебное задание с ограниченными источниками](../examples/source-bounded-educational-prompt/) показывает ту же дисциплину входных данных, ограничений, доказательств и оценки в работе для учащихся. Импорт лексических данных — повторно используемая специализация LKT, а не утверждение, что закрытое предложение на торговой площадке всё ещё доступно.

## Проверка

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
git diff --check
```

Эти команды проверяют локальные контракты, но не доступность сторонних сервисов, уместность ответа в сообществе, качество перевода, результаты клиента или полученный доход.

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

Это ранняя версия, ориентированная прежде всего на Linux. Селекторы сторонних сайтов, правила платформ и возможности учётных записей могут меняться. Обнаружение и черновик лишь помогают работе и не доказывают, что ответ следует публиковать. Оператор отвечает за точность, права на материалы, раскрытие своей связи, уместность в сообществе, соблюдение условий платформы, проверку платежа и окончательную отправку.
