[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Einen echten Bedarf finden, hilfreich antworten, die eigene Verbindung offenlegen und einen Menschen über das Senden entscheiden lassen.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion ist ein lokaler Social-Discovery-Assistent mit Review-Pflicht. Er durchsucht die echte Weboberfläche von Reddit, X oder Instagram in einem sichtbaren, dauerhaften Chrome-Profil, speichert mögliche Treffer in SQLite, erstellt mit `gpt-5.6-sol` bei niedriger Reasoning-Stufe einen belegbaren Antwortentwurf und hält vor dem öffentlichen Senden an. Das Werkzeug soll mit passender Open-Source-Arbeit helfen, nicht Massenwerbung automatisieren.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Arbeitsvertrag

- Zuerst helfen: Die konkrete Frage wird beantwortet, bevor ein Projekt genannt wird.
- Ehrliche Zugehörigkeit: Eigene Links werden mit „Ich pflege…“ oder „Ich habe… gebaut“ offengelegt.
- Eine Person, eine Entscheidung: keine Massenantworten, unerbetenen Direktnachrichten, automatischen Stimmen, Follows oder Engagement-Schleifen.
- Crosspost-bewusst: identische Langfassungen desselben Autors werden einem kanonischen Kandidaten zugeordnet; eine bereits beantwortete Kopie hat Vorrang.
- Standardmäßig aktuell: Quellzeit und Diskussionsumfang werden gespeichert; Beiträge über 30 Tage werden als veraltet markiert und vom Entwurf ausgeschlossen.
- Exakte Freigabe: Jede Änderung am Entwurf macht die kurzlebige, hashgebundene Freigabe ungültig.
- Sichtbarer Betrieb: Chrome läuft in noVNC; lokale Screenshots werden von Git ignoriert.
- Private Sitzungen bleiben privat: Zugangsdaten, Cookies, Profile, Kandidaten, Entwürfe und Freigaben werden nie eingecheckt.

## Aktueller Inhalt

| Pfad | Zweck |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite-Ledger, Zuordnung, Codex-Entwürfe und Freigaben |
| [`browser.py`](../browser.py) | Playwright/CDP-Suche, Prüfung, Vorbereitung und geschütztes Senden |
| [`catalog.json`](../catalog.json) | Belegbare Zuordnung echter Bedürfnisse zu gepflegten Projekten |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Ein dauerhafter Xvfb/x11vnc/noVNC/Chrome-Desktop |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Bewertung von Open-Source-Alternativen |
| [`tests/`](../tests/) | Tests für Zuordnung, Idempotenz und exakte Freigaben |

## Schnellstart

Benötigt werden Linux, Python 3.10+, Chrome, Playwright für Python, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux` und eine authentifizierte Codex-CLI.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Melde dich manuell über noVNC an und starte eine enge, bedarfsorientierte Suche:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Erst nachdem Ziel und Wortlaut exakt geprüft wurden:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## Laufzeit-Isolation

Standardmäßig werden ein 1920×1080-Display (`:116`), ein VNC-Port `5936` und ein einzelner noVNC-Port `6136` verwendet. Alle Kampagnen- und Affiliate-Tabs bleiben im selben dauerhaften Chrome-Profil; jedes wiederhergestellte Chrome-Fenster füllt den Desktop und lässt sich normal auswählen, ohne störende Ausschnittbereiche. CDP bleibt auf `127.0.0.1:9436` und die Sitzung heißt `lazypromotion-browser`. Alle Dienste binden nur an Loopback. Der Launcher verweigert unbekannte belegte Ports und entfernt ausschließlich eigene, nachweislich veraltete Display-Sperren.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Open-Source-Basis

Die erste Version setzt bewusst auf Playwright und SQLite statt auf einen großen Scheduler oder ein Anti-Detection-Framework. Postiz und Mixpost können für geplante Kampagnen nützlich sein; Umgehungs- und automatische Engagement-Funktionen anderer Projekte passen nicht in diesen Review-First-Ablauf. Siehe die [vollständige Bewertung](../docs/open-source-evaluation.md).

## Validierung

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

## Zitieren

Wenn du LazyPromotion in der Forschung verwendest, zitiere das Repository. GitHub liest [`CITATION.cff`](../CITATION.cff) und zeigt **Cite this repository** an.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## Status und Umfang

Dies ist eine frühe, Linux-orientierte Version. Selektoren fremder Websites können sich ändern. Der menschliche Bediener bleibt für Richtigkeit, Community-Regeln, Plattformbedingungen, Offenlegung und das endgültige Senden verantwortlich.
