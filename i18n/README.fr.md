[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Repérer un besoin réel, rédiger une réponse utile, déclarer son lien avec le projet et laisser une personne décider de l’envoi.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion est un assistant local de veille sociale avec révision préalable. Dans un unique profil Chrome visible, il parcourt les véritables interfaces web de Reddit, X, Instagram et Hacker News, consigne les rapprochements possibles dans SQLite, puis utilise le modèle Codex recommandé pour le compte, avec un effort de raisonnement faible, afin de rédiger une réponse étayée. Il s’arrête toujours avant l’envoi public. Il s’adresse aux personnes qui maintiennent des projets open source utiles et veulent aider sans transformer les communautés en listes de prospects.

Le dépôt tient aussi l’inventaire public de 108 dépôts sources `lachlanchen` non archivés. Il les combine en occasions vérifiables, formulées du point de vue d’un acheteur, dans les domaines du code, des livres, des graphes de connaissances, de la recherche, des médias, de l’apprentissage des langues et de l’IA locale. Neuf prestations au périmètre fixe servent l’objectif des premiers USD 1 000 vérifiés. Les clics, étoiles, candidatures, réponses et publications en attente ne sont jamais comptés comme du chiffre d’affaires.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Contrat de fonctionnement

- Aider d’abord : la réponse traite le besoin concret avant de citer un projet.
- Affiliation transparente : un lien personnel est accompagné de « je maintiens… » ou « j’ai créé… ».
- Besoin précis, pas simple mot-clé : les messages anciens, l’intention vague, l’autopromotion, les demandes citées et les expressions ambiguës sont écartés avant le tri par le modèle.
- Contexte actuel : les candidatures ordinaires d’aide publique expirent après sept jours ; les occasions explicitement rémunérées restent examinables pendant 30 jours et nécessitent encore une vérification en direct de leur disponibilité avant tout contact.
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
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | Audit privé et en lecture seule de l’attention sur tous les dépôts sources publics actuels ; le trafic GitHub ne compte jamais comme prospect ni chiffre d’affaires |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Combinaisons de code, livres, systèmes de connaissances et médias adaptées aux acheteurs |
| [`bounties.py`](../bounties.py) | Rapproche les primes publiques de l’état GitHub en direct et rejette les travaux dangereux ou déjà disputés |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | Interroge en lecture seule le flux Bounty du projet et ne transforme que les nouveaux identifiants ou versions en alertes de révision privées |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Carte complète des travaux publics, regroupés par problème réel |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Contrats d’opportunité classés, avec preuves et conditions de livraison |
| [`docs/first-1000.md`](../docs/first-1000.md) | Neuf prestations bornées à USD 250, USD 400 ou USD 500 et calcul honnête de l’objectif |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | Décision actuelle de conversion du portefeuille en revenus, conditions d’inscription et preuves d’occasions externes |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | Analyse mondiale récente des voies rémunérées pour l’infrastructure, l’audit de code, le multilingue et les conditions d’admission |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | Besoins acheteurs actuels classés pour la vérification, la conception de tâches d’agent, la prononciation et les connaissances locales |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | Analyse actuelle des voies directes, lacunes de preuve et conditions de soumission |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) et [`signals.py`](../signals.py) | Entonnoir fondé sur des preuves, graphe public et signaux de demande propriétaires |
| [`owned_monitor.py`](../owned_monitor.py), [`threads_inbound_monitor.py`](../threads_inbound_monitor.py), [`github_inbound_monitor.py`](../github_inbound_monitor.py) et [`lkt_inbox.py`](../lkt_inbox.py) | Suivi des publications en lecture seule, alertes de réponses Threads et de tickets publics, et réception privée des demandes d’adéquation |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | Détection en lecture seule des paiements réels avec état privé agrégé ; ne crée jamais d’objet Stripe et ne comptabilise aucun revenu automatiquement |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Bureau de révision unique Xvfb/x11vnc/noVNC/Chrome appartenant au projet |
| [`application_watch.py`](../application_watch.py) et [`application_inbox_monitor.py`](../application_inbox_monitor.py) | Calendrier de révision des candidatures directes et groupées, plus rapprochement agrégé en lecture seule des fils connus ; le moniteur actif n’intègre que le résumé d’échéance limité pour la confidentialité, sans ouvrir les courriels ni relancer |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | Surveille les offres Freelancer soumises au moyen d’un onglet réutilisé, pour un badge agrégé ou un changement d’état, sans ouvrir les messages ni répondre |
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

Si le fil en direct est déjà résolu ou ne correspond plus, fermez localement le candidat avec la preuve publique exacte au lieu de rédiger une autre réponse :

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

Uniquement après vérification du texte et de la destination exacts :

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

Le même cycle de découverte couvre Reddit, X, Instagram et Hacker News. Hacker News reste toutefois réservé à la recherche : LazyPromotion ne peut ni y rédiger, ni y approuver, ni y préparer, ni y envoyer un commentaire. La planification de contenus propriétaires relus dans Postiz demeure séparée des réponses adressées aux communautés. Les procédures détaillées concernant le worker, le paiement, l’affiliation, la livraison, Postiz et le navigateur se trouvent dans [`docs/`](../docs/).

Les primes GitHub publiques peuvent être examinées sans revendiquer ni modifier un ticket :

```bash
python bounties.py
```

Le tableau sert uniquement à la découverte. L’auditeur vérifie l’état du ticket et les pull requests de solution existantes, rejette les demandes d’instructions dangereuses et écrit son rapport privé sous `.local/`.

Le flux Bounty appartenant au projet peut aussi être surveillé sans commenter, revendiquer, envoyer de message, télécharger de pièce jointe ou soumettre un travail :

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

Le premier passage établit silencieusement une référence privée. Les suivants n’alertent que pour un nouvel identifiant Bounty disponible ou une version supérieure, et le minimum de cinq minutes empêche les interrogations agressives. Voir [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md).

Les nouveaux tickets publics et l’activité des pull requests dans les quinze dépôts actuels à forte attention ou offre peuvent être observés sans lire les corps ni écrire sur GitHub :

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

Le premier passage crée seulement une référence privée. Les suivants n’alertent que pour les clés de tickets absentes de l’état conservé. L’intervalle de boucle ne peut être inférieur à 15 minutes. Voir [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md) pour la liste autorisée fixe et le contrat de sécurité.

Les encaissements Stripe réels peuvent être surveillés sans créer de checkout ni conserver de données client ou de paiement :

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

Le moniteur ne produit qu’une alerte de révision privée. Un paiement n’est compté qu’après rapprochement avec un périmètre accepté, une commande de produit ou un don. Voir [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md).

Les offres Freelancer soumises peuvent être vérifiées l’une après l’autre au moyen d’un onglet de projet authentifié dans le navigateur dédié :

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

Le moniteur ne conserve que les identifiants de campagne, le nombre agrégé du badge, l’état et le rang de l’offre, ainsi que le nombre de propositions. Il n’ouvre jamais de conversation et ne répond pas. Voir [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md).

## Isolation de l’exécution

Le lanceur possède un seul écran 1920×1080 (`:116`), le port VNC `5936`, le port noVNC `6136` et le port CDP local `9436`. Il réutilise un unique profil Chrome persistant, refuse les ports occupés par un processus inconnu, conserve un seul relevé d’exécution privé et ne supprime que les ressources périmées dont il a confirmé la propriété. La visionneuse hôte doit être maximisée dans l’espace de travail GNOME, jamais en plein écran. La pile est arrêtée lorsqu’aucune révision visible n’est attendue. Elle ne se connecte ni à Firefox personnel, ni aux sessions de navigateur d’un autre projet.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Base open source

Le socle reste volontairement réduit : Playwright pour le navigateur visible, SQLite pour l’état local durable, et le modèle Codex pris en charge par le compte pour le tri structuré et la rédaction. Postiz sert uniquement à planifier des contenus propriétaires déjà relus. Les connexions MCP sont facultatives et épinglées à une version ; les sous-processus du modèle n’accèdent ni au navigateur, ni au planificateur, ni aux identifiants, ni aux paiements. Le contournement de détection, l’engagement automatique non sollicité et la diffusion indiscriminée sont exclus.

La couche portefeuille transforme les projets publics en contrats d’opportunité explicites au lieu de promouvoir les 108 dépôts en bloc. Les neuf parcours actuels couvrent l’audit d’une collection locale, la révision avec redline d’un manuscrit, la livraison bilingue d’un cours, les clips narratifs, les spécimens de livres, l’évaluation de plugins KiCad, la reproduction OpenHI, l’audit de topologie LazyRemote et les micro-leçons de prononciation. L’assemblage de clips par IA reste suspendu jusqu’à ce qu’une preuve plus solide passe une revue humaine. Le [spécimen reproductible d’évaluation de plugin KiCad](../examples/kicad-plugin-evaluation/) étaye la nouvelle voie bornée. Une [invite pédagogique limitée par ses sources](../examples/source-bounded-educational-prompt/) applique la même rigueur aux entrées, contraintes, preuves et évaluations dans un travail destiné à l’apprentissage. L’ingestion lexicale est une spécialisation LKT réutilisable, et non l’affirmation qu’une ancienne annonce fermée serait encore disponible. Voir l’[évaluation complète](../docs/open-source-evaluation.md).

## Validation

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
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
