[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Repérer un besoin réel, rédiger une réponse utile, déclarer son lien avec le projet et laisser une personne décider de l’envoi.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion est un assistant local de veille sociale avec révision préalable. Dans un unique profil Chrome visible, il parcourt les véritables interfaces web de Reddit, X, Instagram et Hacker News, consigne les rapprochements possibles dans SQLite, puis utilise le modèle Codex recommandé pour le compte, avec un effort de raisonnement faible, afin de rédiger une réponse étayée. Il s’arrête toujours avant l’envoi public. Il s’adresse aux personnes qui maintiennent des projets open source utiles et veulent aider sans transformer les communautés en listes de prospects.

Le dépôt tient aussi l’inventaire public de 108 dépôts sources `lachlanchen` non archivés. Il les combine en occasions vérifiables, formulées du point de vue d’un acheteur, dans les domaines du code, des livres, des graphes de connaissances, de la recherche, des médias, de l’apprentissage des langues et de l’IA locale. Six prestations au périmètre fixe servent l’objectif des premiers USD 1 000 vérifiés. Les clics, étoiles, candidatures, réponses et publications en attente ne sont jamais comptés comme du chiffre d’affaires.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Contrat de fonctionnement

- Aider d’abord : la réponse traite le besoin concret avant de citer un projet.
- Affiliation transparente : un lien personnel est accompagné de « je maintiens… » ou « j’ai créé… ».
- Besoin précis, pas simple mot-clé : les messages anciens, l’intention vague, l’autopromotion, les demandes citées et les expressions ambiguës sont écartés avant le tri par le modèle.
- Preuve avant l’offre : une prestation doit disposer d’un élément public vérifiable, d’un périmètre écrit, d’exclusions claires et d’un contrôle d’adéquation avant de devenir commerciale.
- Une personne, une décision : aucun envoi massif, message privé non sollicité, vote, abonnement ou boucle d’engagement automatique.
- Approbation exacte : toute modification du brouillon invalide l’approbation temporaire liée à son empreinte ; l’envoi doit correspondre exactement au contenu et à la destination examinés.
- Opération visible : le travail dans le navigateur passe uniquement par le profil Chrome noVNC réservé au projet. Les fenêtres Firefox personnelles sont hors périmètre et ne sont jamais manipulées.
- Privé par défaut : identifiants, cookies, documents client, candidats, brouillons, approbations, données de paiement et preuves d’exécution ne sont jamais versionnés.
- Mesure stricte : attention, demande d’adéquation, prospect qualifié, périmètre accepté, paiement confirmé, livraison, remboursement et revenu reçu restent des états distincts. Aucun passage n’est déduit d’un simple signal d’intérêt.

## Contenu actuel

| Chemin | Rôle |
| --- | --- |
| [`promotion.py`](../promotion.py) | Registre SQLite, rapprochement, tri et rédaction Codex, approbation liée à l’empreinte |
| [`browser.py`](../browser.py) | Découverte Playwright/CDP, inspection, préparation du composeur et envoi protégé |
| [`worker.py`](../worker.py) | Découverte finie avec délais de reprise et file privée de révision ; n’envoie jamais |
| [`catalog.json`](../catalog.json) et [`github-repos.json`](../github-repos.json) | Correspondances sélectionnées avec les besoins et inventaire des dépôts publics |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Combinaisons de code, livres, systèmes de connaissances et médias adaptées aux acheteurs |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Carte complète des travaux publics, regroupés par problème réel |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Contrats d’opportunité classés, avec preuves et conditions de livraison |
| [`docs/first-1000.md`](../docs/first-1000.md) | Six prestations bornées à USD 250 ou USD 500 et calcul honnête de l’objectif |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) et [`signals.py`](../signals.py) | Entonnoir fondé sur des preuves, graphe public et signaux de demande propriétaires |
| [`owned_monitor.py`](../owned_monitor.py) et [`lkt_inbox.py`](../lkt_inbox.py) | Suivi en lecture seule des publications et réception privée des demandes d’adéquation |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Bureau de révision unique Xvfb/x11vnc/noVNC/Chrome appartenant au projet |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Choix auditables des outils open source et MCP |

## Démarrage rapide

Prérequis : Linux, Python 3.10+, Chrome, Playwright pour Python, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux` et une CLI Codex authentifiée.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Connectez-vous manuellement dans noVNC puis lancez une recherche étroite centrée sur un besoin :

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Uniquement après vérification du texte et de la destination exacts :

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

Le même cycle de découverte couvre Reddit, X, Instagram et Hacker News. Hacker News reste toutefois réservé à la recherche : LazyPromotion ne peut ni y rédiger, ni y approuver, ni y préparer, ni y envoyer un commentaire. La planification de contenus propriétaires relus dans Postiz demeure séparée des réponses adressées aux communautés. Les procédures détaillées concernant le worker, le paiement, l’affiliation, la livraison, Postiz et le navigateur se trouvent dans [`docs/`](../docs/).

## Isolation de l’exécution

Le lanceur possède un seul écran 1920×1080 (`:116`), le port VNC `5936`, le port noVNC `6136` et le port CDP local `9436`. Il réutilise un unique profil Chrome persistant, refuse les ports occupés par un processus inconnu, conserve un seul relevé d’exécution privé et ne supprime que les ressources périmées dont il a confirmé la propriété. La visionneuse hôte doit être maximisée dans l’espace de travail GNOME, jamais en plein écran. La pile est arrêtée lorsqu’aucune révision visible n’est attendue. Elle ne se connecte ni à Firefox personnel, ni aux sessions de navigateur d’un autre projet.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Base open source

Le socle reste volontairement réduit : Playwright pour le navigateur visible, SQLite pour l’état local durable, et le modèle Codex pris en charge par le compte pour le tri structuré et la rédaction. Postiz sert uniquement à planifier des contenus propriétaires déjà relus. Les connexions MCP sont facultatives et épinglées à une version ; les sous-processus du modèle n’accèdent ni au navigateur, ni au planificateur, ni aux identifiants, ni aux paiements. Le contournement de détection, l’engagement automatique non sollicité et la diffusion indiscriminée sont exclus.

La couche portefeuille transforme les projets publics en contrats d’opportunité explicites au lieu de promouvoir les 108 dépôts en bloc. Les six parcours actuels sont l’audit d’adéquation d’une collection locale, l’annotation éditoriale d’un manuscrit, la livraison bilingue d’un cours, la création de clips narratifs, la réalisation de spécimens de livres et l’assemblage de clips par IA. Chacun possède un périmètre, des preuves, des exclusions et une condition de livraison. L’ingestion lexicale est une spécialisation LKT réutilisable, et non l’affirmation qu’une ancienne annonce fermée serait encore disponible. Voir l’[évaluation complète](../docs/open-source-evaluation.md).

## Validation

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

Ces contrôles valident les contrats locaux, pas la disponibilité de services tiers, l’adéquation à une communauté, la qualité des traductions, les résultats client ou le chiffre d’affaires. Le parcours financier suit strictement `attention → helpful interaction → fit inquiry → qualified lead → scope accepted → payment confirmed → delivered → received revenue` ; chaque transition exige sa propre preuve.

## Citation

Si vous utilisez LazyPromotion dans un travail de recherche, citez le dépôt. GitHub lit [`CITATION.cff`](../CITATION.cff) et affiche le panneau **Cite this repository**.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## État et périmètre

Il s’agit d’une première version orientée Linux. Les sélecteurs, les règles des plateformes et les capacités des comptes tiers peuvent changer. La découverte et la rédaction sont une assistance, pas la preuve qu’un commentaire doit être publié. L’opérateur reste responsable de l’exactitude, des droits sur les contenus, de la déclaration d’affiliation, de l’adéquation aux communautés, des conditions des plateformes, de la vérification des paiements et de l’envoi final. Le prix d’une prestation correspond à un travail borné ; il ne promet ni résultat commercial, ni audience, ni revenu futur.
