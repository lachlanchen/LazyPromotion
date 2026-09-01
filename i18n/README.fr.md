[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Repérer un besoin réel, rédiger une réponse utile, déclarer son lien avec le projet et laisser une personne décider de l’envoi.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion est un assistant local de découverte sociale avec révision préalable. Il parcourt l’interface web réelle de Reddit, X ou Instagram dans un profil Chrome persistant et visible, consigne les correspondances possibles dans SQLite, rédige une réponse factuelle avec `gpt-5.6-sol` en effort faible, puis s’arrête avant l’envoi public. Son but est d’aider grâce à un projet open source pertinent, pas d’automatiser une campagne de masse.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Contrat de fonctionnement

- Aider d’abord : la réponse traite le besoin concret avant de citer un projet.
- Affiliation transparente : un lien personnel est accompagné de « je maintiens… » ou « j’ai créé… ».
- Une personne, une décision : aucun envoi massif, message privé non sollicité, vote, abonnement ou boucle d’engagement automatique.
- Conscient des publications croisées : les copies longues identiques d’un même auteur sont regroupées derrière un candidat canonique, en privilégiant celle qui a déjà reçu une réponse.
- Récent par défaut : l’horodatage source et le volume de discussion sont consignés ; tout message de plus de 30 jours devient périmé et ne peut pas être rédigé.
- Approbation exacte : toute modification du brouillon invalide l’approbation temporaire liée à son empreinte.
- Opération visible : Chrome tourne dans noVNC et les captures locales sont ignorées par Git.
- Sessions privées : identifiants, cookies, profils, candidats, brouillons et approbations ne sont jamais versionnés.

## Contenu actuel

| Chemin | Rôle |
| --- | --- |
| [`promotion.py`](../promotion.py) | Registre SQLite, rapprochement, rédaction Codex et approbations |
| [`browser.py`](../browser.py) | Découverte Playwright/CDP, inspection, préparation et envoi protégé |
| [`catalog.json`](../catalog.json) | Correspondance fondée entre besoins et projets maintenus |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Bureau persistant unique Xvfb/x11vnc/noVNC/Chrome |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Évaluation des solutions open source |
| [`tests/`](../tests/) | Tests de correspondance, d’idempotence et d’approbation exacte |

## Démarrage rapide

Prérequis : Linux, Python 3.10+, Chrome, Playwright pour Python, Xvfb, x11vnc, noVNC/websockify, `tmux` et une CLI Codex authentifiée.

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

## Isolation de l’exécution

La configuration par défaut utilise un écran 3840×1080 (`:116`) avec deux zones Chrome indépendantes de 1920×1080 partageant un seul profil persistant. noVNC publie la zone campagnes sur `6138`, la zone affiliation sur `6137` et la vue complète sur `6136` ; CDP reste sur `127.0.0.1:9436` et la session est `lazypromotion-browser`. Tous les services restent sur loopback. Le lanceur refuse les ports occupés inconnus et ne nettoie qu’un verrou obsolète qui lui appartient.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Base open source

La première version choisit Playwright et SQLite plutôt qu’un planificateur lourd ou un cadre d’antidétection. Postiz et Mixpost peuvent être utiles pour des campagnes planifiées ; les fonctions d’évasion et d’engagement automatique d’autres projets ne conviennent pas à ce flux avec révision humaine. Voir l’[évaluation complète](../docs/open-source-evaluation.md).

## Validation

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

Il s’agit d’une première version orientée Linux. Les sélecteurs des sites tiers peuvent changer. L’opérateur humain reste responsable de l’exactitude, des règles communautaires, des conditions des plateformes, de la déclaration d’affiliation et de l’envoi final.
