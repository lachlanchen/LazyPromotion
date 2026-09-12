[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Einen echten Bedarf finden, hilfreich antworten, die eigene Verbindung offenlegen und einen Menschen über das Senden entscheiden lassen.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion ist ein lokaler Social-Discovery-Assistent mit Review-Pflicht. Er durchsucht die echten Weboberflächen von Reddit, X, Instagram und Hacker News in einem sichtbaren Chrome-Profil, speichert mögliche Treffer in SQLite, erstellt mit dem für das angemeldete Konto empfohlenen Codex-Modell bei niedriger Reasoning-Stufe belegbare Antwortentwürfe und hält vor dem öffentlichen Senden an. Das Werkzeug richtet sich an Maintainer, die Menschen mit passender Open-Source-Arbeit helfen wollen, ohne Communities in eine Vertriebsliste zu verwandeln.

Das Repository enthält außerdem ein öffentliches Inventar von 108 nicht archivierten `lachlanchen`-Quellcode-Repositories. Daraus entstehen käuferbezogene, nachweisgebundene Angebote aus Code, Büchern, Wissensgraphen, Forschung, Medien, Sprachlernen und lokaler KI. Neun klar begrenzte Servicewege dienen dem Ziel der ersten verifizierten 1.000 USD Umsatz. Klicks, Sterne, Bewerbungen und eingeplante Beiträge zählen niemals als Umsatz.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Arbeitsvertrag

- Zuerst helfen: Die konkrete Frage wird beantwortet, bevor ein Projekt genannt wird.
- Ehrliche Zugehörigkeit: Eigene Links werden mit „Ich pflege…“ oder „Ich habe… gebaut“ offengelegt.
- Exakter Bedarf statt Stichworttreffer: Veraltete Beiträge, vage Absichten, Eigenwerbung, zitierte Anfragen und mehrdeutige Formulierungen werden vor der Modellprüfung gefiltert.
- Zeitnaher Kontext: Gewöhnliche Kandidaten für öffentliche Hilfe verfallen nach sieben Tagen; ausdrücklich bezahlte Gelegenheiten bleiben 30 Tage lang prüfbar und erfordern vor jeder Kontaktaufnahme weiterhin eine Live-Prüfung ihrer Verfügbarkeit.
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
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | Private, rein lesende Aufmerksamkeitsprüfung aller aktuellen öffentlichen Quell-Repositories; GitHub-Traffic zählt niemals als Lead oder Umsatz |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Käuferbezogene Kombinationen aus Code, Büchern, Wissenssystemen und Medien |
| [`bounties.py`](../bounties.py) | Gleicht öffentliche Bounty-Angebote mit dem Live-Zustand auf GitHub ab und verwirft unsichere oder bereits umkämpfte Aufgaben |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | Fragt den projekteigenen Bounty-Agent-Feed nur lesend ab und erzeugt private Review-Hinweise ausschließlich für neue IDs oder Versionen |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Vollständige öffentliche Arbeitsübersicht nach realen Problembereichen |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Priorisierte Angebotsverträge mit Nachweis- und Lieferbedingungen |
| [`docs/first-1000.md`](../docs/first-1000.md) | Neun begrenzte Services für 250, 400 beziehungsweise 500 USD und ehrliche Zielrechnung |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | Aktuelle Portfolio-Umsatz-Entscheidung, Registrierungshürden und Belege zu externen Gelegenheiten |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | Neue weltweite Prüfung bezahlter Wege für Infrastruktur, Code-Audits, mehrsprachige Arbeit und Qualifikationshürden |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | Rangliste aktueller Käuferbedürfnisse für Verifikation, Agenten-Aufgabenentwicklung, Aussprache und lokales Wissensmanagement |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | Aktuelle Prüfung direkter Wege, Nachweislücken und Einreichungshürden |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) und [`signals.py`](../signals.py) | Nachweisgebundener Funnel, öffentlicher Graph und Signale aus eigenen Kanälen |
| [`owned_monitor.py`](../owned_monitor.py), [`threads_inbound_monitor.py`](../threads_inbound_monitor.py), [`github_inbound_monitor.py`](../github_inbound_monitor.py) und [`lkt_inbox.py`](../lkt_inbox.py) | Nur lesende Veröffentlichungsüberwachung, Hinweise auf Threads-Antworten und öffentliche Issues sowie private Erfassung von Eignungsanfragen |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | Nur lesende Erkennung echter Zahlungen mit aggregiertem privatem Zustand; erstellt keine Stripe-Objekte und verbucht nie automatisch Umsatz |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Ein projekteigener Xvfb/x11vnc/noVNC/Chrome-Desktop für Reviews |
| [`application_watch.py`](../application_watch.py) und [`application_inbox_monitor.py`](../application_inbox_monitor.py) | Fälligkeitsplan für direkte und gruppierte Bewerbungen sowie rein lesender Aggregatabgleich bekannter Bewerbungs-Threads; der laufende Monitor zeigt nur die datensparsame Fälligkeitsübersicht und öffnet weder E-Mails noch fasst er nach |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | Beobachtet eingereichte Freelancer-Gebote über einen wiederverwendeten Tab auf aggregierte Nachrichtenhinweise oder Zustandsänderungen, ohne Nachrichten zu öffnen oder zu antworten |
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

Wenn der Live-Thread bereits gelöst oder nicht mehr passend ist, schließe den Kandidaten lokal mit dem genauen öffentlichen Beleg, statt einen weiteren Antwortentwurf zu erstellen:

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

Erst nachdem Ziel und Wortlaut exakt geprüft wurden:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

Der gleiche Suchzyklus unterstützt Reddit, X, Instagram und Hacker News. Hacker News dient jedoch ausschließlich der Recherche: LazyPromotion kann dort Kommentare weder entwerfen noch freigeben, vorbereiten oder senden. Geprüfte Veröffentlichungen auf eigenen Kanälen über Postiz bleiben strikt von Community-Antworten getrennt. Ausführliche Abläufe für Worker, Zahlungen, Affiliates, Lieferung, Postiz und Browser stehen unter [`docs/`](../docs/).

Öffentliche GitHub-Bounties lassen sich prüfen, ohne ein Issue zu beanspruchen oder zu verändern:

```bash
python bounties.py
```

Das Board dient nur der Suche. Der Auditor prüft den aktuellen Issue-Zustand und vorhandene Lösungs-Pull-Requests, weist unsichere Anweisungen zurück und schreibt seinen privaten Bericht nach `.local/`.

Auch der projekteigene Bounty-Agent-Feed kann beobachtet werden, ohne zu kommentieren, Aufgaben zu beanspruchen, Nachrichten zu senden, Anhänge herunterzuladen oder Arbeit einzureichen:

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

Der erste Durchlauf legt still eine private Ausgangsbasis an. Spätere Durchläufe melden nur neue verfügbare Bounty-IDs oder höhere Versionen; das Fünf-Minuten-Minimum verhindert aggressives Abfragen. Siehe [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md).

Neue öffentliche Issues und Pull-Request-Aktivitäten in den fünfzehn aktuellen aufmerksamkeits- oder angebotsstarken Repositories lassen sich beobachten, ohne Inhaltskörper zu lesen oder auf GitHub zu schreiben:

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

Der erste Durchlauf erstellt nur eine private Ausgangsbasis. Spätere Durchläufe melden ausschließlich Issue-Schlüssel, die noch nicht im gespeicherten Zustand liegen. Das Schleifenintervall darf nicht kürzer als 15 Minuten sein. Siehe [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md) für die feste Positivliste und den Sicherheitsvertrag.

Echte Stripe-Eingänge können beobachtet werden, ohne einen Checkout zu erzeugen oder Kunden- beziehungsweise Zahlungsdetails aufzubewahren:

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

Der Beobachter erzeugt nur einen privaten Review-Hinweis. Eine Zahlung wird erst gezählt, wenn sie einem akzeptierten Umfang, einer Produktbestellung oder einem Spendenkontext zugeordnet wurde. Siehe [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md).

Eingereichte Freelancer-Gebote lassen sich nacheinander über einen authentifizierten Projekt-Tab im dedizierten Browser prüfen:

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

Der Monitor speichert nur Kampagnen-IDs, aggregierte Badge-Anzahl, Gebotsstatus, Rang und Anzahl der Angebote. Er öffnet nie ein Gespräch und sendet keine Antwort. Siehe [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md).

## Laufzeit-Isolation

Der Launcher verwaltet genau ein 1920×1080-Display (`:116`), VNC-Port `5936`, noVNC-Port `6136` und den nur lokal erreichbaren CDP-Port `9436`. Er verwendet ein dauerhaftes Chrome-Profil, verweigert den Start bei unbekannt belegten Ports, führt genau eine private Laufzeitübergabe und entfernt nur veraltete Ressourcen, die ihm nachweislich gehören. Der Viewer bleibt innerhalb des GNOME-Arbeitsbereichs maximiert, aber niemals im Vollbild. Ist kein sichtbares Review ausstehend, wird der Stack beendet. Persönliches Firefox wird weder geöffnet noch berührt.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Open-Source-Basis

Der Kern bleibt bewusst klein: Playwright steuert den sichtbaren Browser, SQLite speichert den dauerhaften lokalen Zustand und das vom Konto unterstützte Codex-Modell übernimmt strukturierte Prüfung und Entwürfe. Postiz wird ausschließlich für geprüfte Veröffentlichungsplanung auf eigenen Kanälen eingesetzt. MCP-Anbindungen sind optional und versionsgebunden; Modell-Unterprozesse erhalten weder Browser- oder Scheduler-Zugriff noch Zugangsdaten oder Zahlungsbefugnisse.

Die Portfolio-Ebene macht aus öffentlichen Projekten klar abgegrenzte Angebotsverträge, statt alle Repositories gleichzeitig zu bewerben. Die neun aktuellen Wege umfassen Eignungsanalysen lokaler Sammlungen, Manuskript-Redlines, zweisprachige Vorlesungsunterlagen, Story-Clips, Buchmuster, KiCad-Plugin-Prüfungen, OpenHI-Reproduktionen, LazyRemote-Topologieprüfungen und Aussprache-Mikrolektionen. Die Montage von KI-Clips bleibt pausiert, bis stärkere Nachweise eine menschliche Prüfung bestehen. Das reproduzierbare [KiCad-Plugin-Prüfbeispiel](../examples/kicad-plugin-evaluation/) stützt die neue begrenzte Route. Ein kompaktes [quellengebundenes Lern-Prompt](../examples/source-bounded-educational-prompt/) zeigt dieselbe Disziplin für Eingaben, Einschränkungen, Belege und Auswertung in lernorientierter Arbeit. Lexikalische Datenübernahme ist eine wiederverwendbare LKT-Spezialisierung, aber keine Behauptung, dass ein geschlossenes Marketplace-Angebot weiterhin offen sei. Einzelheiten stehen in der [vollständigen Open-Source- und MCP-Bewertung](../docs/open-source-evaluation.md).

## Validierung

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
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
