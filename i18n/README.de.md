[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Einen echten Bedarf finden, hilfreich antworten, die eigene Verbindung offenlegen und einen Menschen über das Senden entscheiden lassen.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion ist ein lokaler Social-Discovery-Assistent mit Review-Pflicht. Er durchsucht die echten Weboberflächen von Reddit, X, Instagram und Hacker News in einem sichtbaren Chrome-Profil, speichert mögliche Treffer in SQLite, erstellt mit dem für das angemeldete Konto empfohlenen Codex-Modell bei niedriger Reasoning-Stufe belegbare Antwortentwürfe und hält vor dem öffentlichen Senden an. Das Werkzeug richtet sich an Maintainer, die Menschen mit passender Open-Source-Arbeit helfen wollen, ohne Communities in eine Vertriebsliste zu verwandeln.

Das Repository enthält außerdem ein öffentliches Inventar von 108 nicht archivierten `lachlanchen`-Quellcode-Repositories. Daraus entstehen käuferbezogene, nachweisgebundene Angebote aus Code, Büchern, Wissensgraphen, Forschung, Medien, Sprachlernen und lokaler KI. Sechs klar begrenzte Servicewege dienen dem Ziel der ersten verifizierten 1.000 USD Umsatz. Klicks, Sterne, Bewerbungen und eingeplante Beiträge zählen niemals als Umsatz.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Arbeitsvertrag

- Zuerst helfen: Die konkrete Frage wird beantwortet, bevor ein Projekt genannt wird.
- Ehrliche Zugehörigkeit: Eigene Links werden mit „Ich pflege…“ oder „Ich habe… gebaut“ offengelegt.
- Exakter Bedarf statt Stichworttreffer: Veraltete Beiträge, vage Absichten, Eigenwerbung, zitierte Anfragen und mehrdeutige Formulierungen werden vor der Modellprüfung gefiltert.
- Belege vor Angebot: Ein Service braucht prüfbare öffentliche Nachweise, einen schriftlichen Umfang, Ausschlüsse und eine Eignungsprüfung, bevor er kommerziell angeboten werden darf.
- Eine Person, eine Entscheidung: keine Massenantworten, unerbetenen Direktnachrichten, automatischen Stimmen oder Follows, wiederholten Kontaktversuche oder Engagement-Schleifen.
- Exakte Freigabe: Jede Änderung am Entwurf macht die kurzlebige, hashgebundene Freigabe ungültig. Gesendet werden dürfen nur das geprüfte Ziel und der vollständig geprüfte Wortlaut.
- Sichtbarer Betrieb: Browserarbeit verwendet ausschließlich das dedizierte noVNC-Chrome-Profil. Persönliche Firefox-Fenster liegen außerhalb des Arbeitsbereichs.
- Standardmäßig privat: Zugangsdaten, Cookies, Kundenmaterial, Kandidaten, Entwürfe, Freigaben, Zahlungsdaten und Laufzeitnachweise gelangen nie in Git.
- Strenge Messung: `Aufmerksamkeit → hilfreiche Interaktion → Eignungsanfrage → qualifizierter Lead → Umfang angenommen → Zahlung bestätigt → geliefert → erhaltener Umsatz` sind getrennte Zustände. Kein Übergang wird aus Besuchen oder Optimismus abgeleitet.

## Aktueller Inhalt

| Pfad | Zweck |
| --- | --- |
| [`promotion.py`](../promotion.py) | SQLite-Ledger, Zuordnung, Codex-Prüfung und -Entwurf sowie hashgebundene Freigabe |
| [`browser.py`](../browser.py) | Playwright/CDP-Suche, Prüfung, Vorbereitung des Eingabefelds und geschütztes Senden |
| [`worker.py`](../worker.py) | Endliche Suche mit Wartezeiten und privater Review-Warteschlange; sendet niemals |
| [`catalog.json`](../catalog.json) und [`github-repos.json`](../github-repos.json) | Kuratierte Bedarfszuordnung und öffentliches Repository-Inventar |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Käuferbezogene Kombinationen aus Code, Büchern, Wissenssystemen und Medien |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Vollständige öffentliche Arbeitsübersicht nach realen Problembereichen |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Priorisierte Angebotsverträge mit Nachweis- und Lieferbedingungen |
| [`docs/first-1000.md`](../docs/first-1000.md) | Sechs begrenzte Services für 250 beziehungsweise 500 USD und ehrliche Zielrechnung |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) und [`signals.py`](../signals.py) | Nachweisgebundener Funnel, öffentlicher Graph und Signale aus eigenen Kanälen |
| [`owned_monitor.py`](../owned_monitor.py) und [`lkt_inbox.py`](../lkt_inbox.py) | Nur lesende Überwachung veröffentlichter Beiträge und private Erfassung von Eignungsanfragen |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Ein projekteigener Xvfb/x11vnc/noVNC/Chrome-Desktop für Reviews |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Nachprüfbare Auswahl von Open-Source- und MCP-Werkzeugen |

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

Der gleiche Suchzyklus unterstützt Reddit, X, Instagram und Hacker News. Hacker News dient jedoch ausschließlich der Recherche: LazyPromotion kann dort Kommentare weder entwerfen noch freigeben, vorbereiten oder senden. Geprüfte Veröffentlichungen auf eigenen Kanälen über Postiz bleiben strikt von Community-Antworten getrennt. Ausführliche Abläufe für Worker, Zahlungen, Affiliates, Lieferung, Postiz und Browser stehen unter [`docs/`](../docs/).

## Laufzeit-Isolation

Der Launcher verwaltet genau ein 1920×1080-Display (`:116`), VNC-Port `5936`, noVNC-Port `6136` und den nur lokal erreichbaren CDP-Port `9436`. Er verwendet ein dauerhaftes Chrome-Profil, verweigert den Start bei unbekannt belegten Ports, führt genau eine private Laufzeitübergabe und entfernt nur veraltete Ressourcen, die ihm nachweislich gehören. Der Viewer bleibt innerhalb des GNOME-Arbeitsbereichs maximiert, aber niemals im Vollbild. Ist kein sichtbares Review ausstehend, wird der Stack beendet. Persönliches Firefox wird weder geöffnet noch berührt.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Open-Source-Basis

Der Kern bleibt bewusst klein: Playwright steuert den sichtbaren Browser, SQLite speichert den dauerhaften lokalen Zustand und das vom Konto unterstützte Codex-Modell übernimmt strukturierte Prüfung und Entwürfe. Postiz wird ausschließlich für geprüfte Veröffentlichungsplanung auf eigenen Kanälen eingesetzt. MCP-Anbindungen sind optional und versionsgebunden; Modell-Unterprozesse erhalten weder Browser- oder Scheduler-Zugriff noch Zugangsdaten oder Zahlungsbefugnisse.

Die Portfolio-Ebene macht aus öffentlichen Projekten klar abgegrenzte Angebotsverträge, statt alle Repositories gleichzeitig zu bewerben. Die aktuellen Wege umfassen Eignungsanalysen lokaler Sammlungen, Manuskript-Redlines, zweisprachige Vorlesungsunterlagen, Story-Clips, Buchmuster und die Montage von KI-Clips. Lexikalische Datenübernahme ist eine wiederverwendbare LKT-Spezialisierung, aber keine Behauptung, dass ein geschlossenes Marketplace-Angebot weiterhin offen sei. Einzelheiten stehen in der [vollständigen Open-Source- und MCP-Bewertung](../docs/open-source-evaluation.md).

## Validierung

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

Diese Prüfungen validieren lokale Verträge, nicht die Verfügbarkeit externer Dienste, Community-Eignung, Übersetzungsqualität, Kundenergebnisse oder Umsatz.

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

Dies ist eine frühe, Linux-orientierte Version. Selektoren fremder Websites, Plattformregeln und Kontofunktionen können sich ändern. Suche und Entwurf sind Hilfsmittel und kein Nachweis dafür, dass eine Antwort veröffentlicht werden sollte. Der Betreiber bleibt für Richtigkeit, Rechte, Offenlegung, Community-Eignung, Plattformbedingungen, Zahlungsprüfung und das endgültige Senden verantwortlich.
