[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Encuentra una necesidad real, escribe una respuesta útil, declara tu relación y deja que una persona decida si debe enviarse.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion es un asistente local de descubrimiento social con revisión previa. Busca en la interfaz web real de Reddit, X o Instagram mediante un perfil persistente y visible de Chrome, guarda posibles coincidencias en SQLite, redacta una respuesta fundamentada con el modelo Codex recomendado para la cuenta y esfuerzo bajo, y se detiene antes del envío público. Está pensado para ayudar con proyectos de código abierto pertinentes, no para hacer marketing masivo.

El repositorio también mantiene un inventario público de 108 repositorios fuente no archivados y convierte código, libros, grafos de conocimiento, investigación, medios, aprendizaje de idiomas e IA local en oportunidades concretas y sujetas a evidencia. Nueve servicios de alcance fijo apoyan la meta de los primeros USD 1.000 verificados; clics, estrellas, solicitudes y publicaciones en cola nunca cuentan como ingresos.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Contrato operativo

- Primero ayudar: la respuesta atiende la necesidad concreta antes de mencionar un proyecto.
- Afiliación honesta: todo enlace propio incluye una declaración como «mantengo…» o «construí…».
- Una persona, una decisión: no hay respuestas masivas, mensajes privados no solicitados, votos, seguimientos ni bucles de interacción automáticos.
- Consciente de publicaciones cruzadas: las copias extensas idénticas del mismo autor se agrupan bajo un candidato canónico, dando prioridad a la copia ya respondida.
- Contexto oportuno: los candidatos normales de ayuda pública caducan tras siete días; las oportunidades de pago explícitas conservan una ventana de revisión de 30 días y aun así exigen comprobar en vivo su disponibilidad antes de contactar.
- Aprobación exacta: cambiar el borrador invalida la aprobación temporal vinculada a su hash.
- Evidencia antes de la oferta: una ruta necesita prueba pública inspeccionable, alcance, exclusiones y control de ajuste antes de venderse.
- Medición estricta: atención, consulta, alcance aceptado, pago confirmado, entrega, reembolso e ingreso recibido son estados distintos.
- Operación visible: Chrome funciona en noVNC y las capturas locales quedan ignoradas por Git.
- Firefox personal queda fuera de alcance; solo se usa el perfil Chrome dedicado al proyecto.
- Las sesiones siguen privadas: credenciales, cookies, perfiles, candidatos, borradores y aprobaciones nunca entran en el repositorio.

## Contenido actual

| Ruta | Función |
| --- | --- |
| [`promotion.py`](../promotion.py) | Registro SQLite, emparejamiento, redacción con Codex y aprobaciones |
| [`browser.py`](../browser.py) | Descubrimiento Playwright/CDP, inspección, preparación y envío protegido |
| [`worker.py`](../worker.py) | Descubrimiento acotado y cola privada de revisión; nunca envía |
| [`catalog.json`](../catalog.json) y [`github-repos.json`](../github-repos.json) | Mapa fundamentado de necesidades e inventario público de repositorios |
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | Auditoría privada y de solo lectura de la atención en todos los repositorios fuente públicos actuales; el tráfico de GitHub nunca se cuenta como contacto ni ingreso |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Combinaciones de código, libros, conocimiento y medios orientadas al comprador |
| [`bounties.py`](../bounties.py) | Concilia recompensas públicas con el estado en vivo de GitHub y rechaza tareas inseguras o ya disputadas |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | Consulta en modo lectura el feed de Bounty del proyecto y convierte solo ID o versiones nuevas en alertas privadas de revisión |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Mapa completo del trabajo público por área de problema |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Contratos de oportunidad priorizados con puertas de prueba y entrega |
| [`docs/first-1000.md`](../docs/first-1000.md) | Nueve servicios acotados de USD 250/400/500 y cálculo honesto de la meta |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | Decisión vigente de cartera a ingresos, puertas de registro y evidencia de oportunidades externas |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | Revisión mundial reciente de rutas pagadas para infraestructura, auditoría de código, trabajo multilingüe y requisitos de acceso |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | Necesidades vivas priorizadas de verificación, diseño de tareas para agentes, pronunciación y conocimiento local |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | Revisión vigente de rutas directas, carencias de prueba y puertas de presentación |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) y [`signals.py`](../signals.py) | Solicitudes y embudo de ingresos sujetos a evidencia, grafo público y señales de demanda propias |
| [`owned_monitor.py`](../owned_monitor.py), [`threads_inbound_monitor.py`](../threads_inbound_monitor.py), [`github_inbound_monitor.py`](../github_inbound_monitor.py) y [`lkt_inbox.py`](../lkt_inbox.py) | Seguimiento de publicaciones en modo lectura, alertas de respuestas en Threads y de incidencias públicas, y entrada privada para comprobar ajuste |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | Detecta cobros reales en modo lectura con estado privado agregado; nunca crea objetos de Stripe ni registra ingresos automáticamente |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Un único escritorio Xvfb/x11vnc/noVNC/Chrome persistente |
| [`application_watch.py`](../application_watch.py) y [`application_inbox_monitor.py`](../application_inbox_monitor.py) | Calendario de revisiones para solicitudes directas y agrupadas, y cotejo agregado de solo lectura para hilos conocidos; el monitor activo solo incorpora el resumen limitado por privacidad, sin abrir correo ni insistir |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | Vigila ofertas enviadas en Freelancer mediante una pestaña reutilizada, atendiendo solo al indicador agregado o a cambios de estado, sin abrir mensajes ni responder |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Evaluación de alternativas de código abierto |

## Inicio rápido

Requiere Linux, Python 3.10+, Chrome, Playwright para Python, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux` y una CLI de Codex autenticada.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Inicia sesión manualmente en noVNC y ejecuta búsquedas pequeñas orientadas a una necesidad:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Si el hilo en vivo ya está resuelto o ha dejado de encajar, cierra el candidato localmente con la evidencia pública exacta en lugar de redactar otra respuesta:

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

Solo después de revisar el destino y el texto exactos:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

El ciclo admite Reddit, X, Instagram y Hacker News. Hacker News es solo investigación: no se pueden redactar, aprobar, preparar ni enviar comentarios allí. La programación propia mediante Postiz permanece separada de las respuestas comunitarias. Los procedimientos detallados están en [`docs/`](../docs/).

Las recompensas públicas de GitHub se pueden examinar sin reclamar ni modificar una incidencia:

```bash
python bounties.py
```

El tablero sirve solo para descubrir. El auditor comprueba el estado en vivo de la incidencia y las solicitudes de cambios que ya ofrecen soluciones, rechaza instrucciones inseguras y escribe su informe privado en `.local/`.

El feed de Bounty propiedad del proyecto también se puede vigilar sin comentar, reclamar, enviar mensajes, descargar adjuntos ni presentar trabajo:

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

La primera pasada crea en silencio una referencia privada. Las siguientes solo alertan de un ID de Bounty disponible nuevo o de una versión superior, y el mínimo de cinco minutos evita consultas agresivas. Consulta [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md).

Se pueden observar incidencias públicas nuevas y actividad de solicitudes de cambios en los quince repositorios actuales de mayor atención u oferta, sin leer cuerpos ni escribir en GitHub:

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

La primera pasada solo crea una referencia privada. Las siguientes alertan únicamente de claves de incidencias ausentes del estado conservado. El intervalo no puede ser inferior a 15 minutos. Consulta [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md) para la lista permitida fija y el contrato de seguridad.

Los cobros reales de Stripe se pueden vigilar sin crear un checkout ni conservar datos de clientes o pagos:

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

El monitor solo genera una alerta privada de revisión. Un pago se cuenta después de asociarlo con un alcance aceptado, un pedido de producto o una donación. Consulta [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md).

Las pujas enviadas en Freelancer pueden revisarse de forma secuencial mediante una pestaña autenticada del proyecto en el navegador dedicado:

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

El monitor guarda solo los ID de campaña, el recuento agregado del distintivo, el estado y rango de la puja y el número de propuestas. Nunca abre una conversación ni responde. Consulta [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md).

## Aislamiento de ejecución

La configuración predeterminada usa una pantalla de 1920×1080 (`:116`), un puerto VNC `5936` y un único noVNC en `6136`. Todas las pestañas de campañas y afiliados permanecen en el mismo perfil persistente de Chrome; cada ventana restaurada ocupa el escritorio completo y se puede alternar normalmente, sin zonas recortadas que interfieran. CDP permanece en `127.0.0.1:9436` y la sesión es `lazypromotion-browser`. Todo se enlaza a loopback; el lanzador rechaza puertos desconocidos ocupados y solo limpia bloqueos obsoletos propios. El entorno se detiene cuando no hay una revisión visible pendiente y nunca toca el navegador personal.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Base de código abierto

La primera versión elige Playwright y SQLite en vez de un programador grande o un marco de antidetección. Postiz y Mixpost pueden servir para campañas planificadas; las funciones de evasión o interacción automática de otros proyectos no pertenecen a este flujo con revisión humana. Consulta la [evaluación completa](../docs/open-source-evaluation.md).

Las conexiones MCP son opcionales y están fijadas; los subprocesos del modelo no reciben acceso al navegador, al programador, a credenciales ni a pagos. Las nueve rutas actuales cubren colecciones locales, redline LaTeX, clases bilingües, clips narrativos, especímenes de libro, evaluación de plugins de KiCad, reproducción de OpenHI, revisión de topologías de LazyRemote y microlecciones de pronunciación. El montaje de clips de IA sigue en pausa hasta que una prueba más sólida supere la revisión humana. El [ejemplo reproducible de evaluación de plugins de KiCad](../examples/kicad-plugin-evaluation/) sustenta la nueva ruta acotada. Un [prompt educativo limitado por fuentes](../examples/source-bounded-educational-prompt/) aplica la misma disciplina de entradas, restricciones, evidencia y evaluación al trabajo para estudiantes. La ingesta léxica es una especialización reutilizable, no la afirmación de que una oferta cerrada sigue abierta.

## Validación

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
git diff --check
```

Estas comprobaciones validan contratos locales; no demuestran disponibilidad externa, calidad de traducción, resultados de clientes ni ingresos.

## Cita

Si usas LazyPromotion en investigación, cita el repositorio. GitHub lee [`CITATION.cff`](../CITATION.cff) y muestra el panel **Cite this repository**.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## Estado y alcance

Es una versión inicial orientada a Linux. Los selectores de sitios externos pueden cambiar. El operador humano sigue siendo responsable de la exactitud, los derechos, las normas comunitarias, las condiciones de cada plataforma, la declaración de afiliación, la revisión del pago y el envío final.
