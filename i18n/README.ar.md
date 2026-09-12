[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*اعثر على حاجة حقيقية، واكتب إجابة مفيدة، ووضّح صلتك بالمشروع، ثم دع إنسانًا يقرر ما إذا كان سيرسلها.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion مساعد محلي لاكتشاف الاحتياجات الاجتماعية يعتمد المراجعة قبل النشر. يبحث في واجهة Reddit أو X أو Instagram الحقيقية عبر ملف Chrome دائم ومرئي، ويحفظ النتائج المحتملة في SQLite، ويكتب مسودة موثقة باستخدام نموذج Codex الموصى به للحساب وبجهد استدلال منخفض، ثم يتوقف قبل الإرسال العلني. صُمم لمساعدة الناس بمشروعات مفتوحة المصدر ذات صلة، لا للتسويق الجماعي.

يحافظ المستودع أيضًا على فهرس عام لـ 108 مستودعات مصدر غير مؤرشفة، ويحوّل البرمجيات والكتب والرسوم المعرفية والبحث والوسائط وتعلّم اللغات والذكاء الاصطناعي المحلي إلى فرص محددة للمشتري ومقيّدة بالدليل. تدعم تسع خدمات ثابتة النطاق هدف أول 1000 دولار موثّقة؛ ولا تُحسب النقرات أو النجوم أو الطلبات أو المنشورات المجدولة إيرادًا.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## عقد التشغيل

- المساعدة أولًا: تجيب الرسالة عن الحاجة المحددة قبل ذكر أي مشروع.
- صلة واضحة: يتضمن رابط المشروع تصريحًا صريحًا مثل «أنا أحافظ على…» أو «أنا بنيت…».
- شخص واحد وقرار واحد: لا ردود جماعية ولا رسائل خاصة غير مطلوبة ولا تصويت أو متابعة أو حلقات تفاعل آلية.
- وعي بالنشر المتقاطع: تُجمع النسخ الطويلة المتطابقة للكاتب نفسه تحت مرشح أساسي واحد، مع تفضيل النسخة التي تلقت ردًا بالفعل.
- سياق حديث: تنتهي صلاحية مرشحي المساعدة العامة العاديين بعد سبعة أيام؛ وتبقى الفرص المدفوعة الصريحة ضمن نافذة مراجعة مدتها 30 يومًا، مع وجوب التحقق المباشر من استمرار توافرها قبل التواصل.
- موافقة دقيقة: يؤدي تغيير المسودة إلى إبطال الموافقة المؤقتة المرتبطة ببصمة المحتوى.
- الدليل قبل العرض: يجب أن يملك المسار إثباتًا عامًا قابلًا للفحص ونطاقًا واستثناءات وفحص ملاءمة قبل البيع.
- القياس الصارم: يبقى الانتباه والاستفسار وقبول النطاق والدفع المؤكد والتسليم والاسترداد والإيراد المستلم حالات منفصلة.
- تشغيل مرئي: يعمل Chrome داخل noVNC وتبقى لقطات الإثبات المحلية خارج Git.
- نافذة Firefox الشخصية خارج النطاق؛ يُستخدم ملف Chrome المخصص للمشروع فقط.
- الجلسات خاصة: لا تدخل بيانات الدخول أو ملفات الارتباط أو ملفات المتصفح أو المرشحون أو المسودات أو الموافقات في المستودع.

## المحتويات الحالية

| المسار | الغرض |
| --- | --- |
| [`promotion.py`](../promotion.py) | سجل SQLite والمطابقة وصياغة Codex والموافقات |
| [`browser.py`](../browser.py) | الاكتشاف والفحص والتحضير والإرسال المحمي عبر Playwright/CDP |
| [`worker.py`](../worker.py) | اكتشاف محدود وطابور مراجعة خاص؛ لا يرسل أبدًا |
| [`catalog.json`](../catalog.json) و[`github-repos.json`](../github-repos.json) | ربط منسق للاحتياجات مع فهرس المستودعات العامة |
| [`github_portfolio_audit.py`](../github_portfolio_audit.py) | تدقيق خاص للانتباه بوضع القراءة فقط عبر جميع مستودعات المصدر العامة الحالية؛ ولا تُعد حركة GitHub عميلًا محتملًا أو إيرادًا |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | فرص تجمع البرمجيات والكتب وأنظمة المعرفة والوسائط حسب حاجة المشتري |
| [`bounties.py`](../bounties.py) | يطابق المكافآت العامة مع حالة GitHub المباشرة ويرفض العمل غير الآمن أو الذي يجري التنافس عليه بالفعل |
| [`bounty_marketplace_monitor.py`](../bounty_marketplace_monitor.py) | يستطلع موجز Bounty المملوك للمشروع للقراءة فقط، ويحوّل المعرّفات أو الإصدارات الجديدة وحدها إلى تنبيهات مراجعة خاصة |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | خريطة الأعمال العامة الكاملة حسب مجال المشكلة |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | عقود فرص مرتبة ببوابات للإثبات والتسليم |
| [`docs/first-1000.md`](../docs/first-1000.md) | تسع خدمات محدودة بسعر 250 أو 400 أو 500 دولار وحساب الهدف بصدق |
| [`docs/portfolio-paid-opportunity-research-2026-09-10.md`](../docs/portfolio-paid-opportunity-research-2026-09-10.md) | قرار التحويل الحالي من معرض الأعمال إلى الإيراد، وبوابات التسجيل، وأدلة الفرص الخارجية |
| [`docs/paid-need-decision-2026-09-12.md`](../docs/paid-need-decision-2026-09-12.md) | فحص عالمي حديث لمسارات مدفوعة في البنية التحتية وتدقيق الشفرة والعمل متعدد اللغات وبوابات التأهل |
| [`docs/paid-need-decision-2026-09-11.md`](../docs/paid-need-decision-2026-09-11.md) | احتياجات مشترين مباشرة ومرتبة للتحقق وهندسة مهام الوكلاء والنطق والعمل المعرفي المحلي |
| [`docs/paid-need-decision-2026-09-09.md`](../docs/paid-need-decision-2026-09-09.md) | فحص المسارات المباشرة الحالي وفجوات الإثبات وبوابات التقديم |
| [`metrics.py`](../metrics.py) و[`network.py`](../network.py) و[`signals.py`](../signals.py) | طلبات ومسار إيراد ببوابات دليل، ورسم عام، وإشارات طلب من قنوات مملوكة |
| [`owned_monitor.py`](../owned_monitor.py) و[`threads_inbound_monitor.py`](../threads_inbound_monitor.py) و[`github_inbound_monitor.py`](../github_inbound_monitor.py) و[`lkt_inbox.py`](../lkt_inbox.py) | مراقبة نشر للقراءة فقط، وتنبيهات ردود Threads والمسائل العامة، واستقبال خاص لفحص الملاءمة |
| [`stripe_revenue_monitor.py`](../stripe_revenue_monitor.py) | كشف للدفعات الحقيقية بالقراءة فقط وحالة خاصة مجمعة؛ لا ينشئ عناصر Stripe ولا يسجل الإيراد تلقائيًا |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | سطح مكتب واحد دائم من Xvfb/x11vnc/noVNC/Chrome |
| [`application_watch.py`](../application_watch.py) و[`application_inbox_monitor.py`](../application_inbox_monitor.py) | جدول مراجعة مستحقة للتقديمات المباشرة والمجمعة مع مطابقة مجمعة للقراءة فقط للمحادثات المعروفة؛ ولا يضم المراقب الجاري إلا ملخص الاستحقاق المحدود للخصوصية من دون فتح البريد أو المتابعة |
| [`freelancer_inbound_monitor.py`](../freelancer_inbound_monitor.py) | يراقب عروض Freelancer المقدمة عبر علامة تبويب واحدة معاد استخدامها بحثًا عن شارة رسائل مجمعة أو تغير حالة، من دون فتح الرسائل أو الرد |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | تقييم البدائل مفتوحة المصدر |

## بداية سريعة

يتطلب Linux وPython 3.10+ وChrome وPlaywright لـ Python وXvfb وx11vnc و`wmctrl` وnoVNC/websockify و`tmux` وواجهة Codex CLI مسجّلًا دخولها.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

سجّل الدخول يدويًا من noVNC، ثم نفّذ بحثًا صغيرًا موجّهًا إلى حاجة محددة:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

إذا كانت المحادثة المباشرة قد حُلّت بالفعل أو لم تعد مناسبة، فأغلق المرشح محليًا مع الدليل العام الدقيق بدلًا من صياغة رد آخر:

```bash
python promotion.py dismiss-candidate CANDIDATE_ID \
  --reason "An existing reply already provides the exact fix." \
  --evidence "https://example.com/existing-answer" \
  --confirm-reviewed-live-context
```

لا ترسل إلا بعد أن يراجع إنسان الوجهة والنص كاملًا:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

تدعم دورة الاكتشاف Reddit وX وInstagram وHacker News، لكن Hacker News للبحث فقط ولا يمكن إنشاء تعليق أو إرساله إليه. تبقى جدولة Postiz لمحتوى الطرف الأول منفصلة عن ردود المجتمع. توجد إجراءات العامل والدفع والشركاء والتسليم وPostiz والمتصفح في مجلد [`docs/`](../docs/).

يمكن فحص مكافآت GitHub العامة من دون المطالبة بمسألة أو تغييرها:

```bash
python bounties.py
```

اللوحة للاكتشاف فقط. يتحقق المدقق من حالة المسألة المباشرة وطلبات السحب التي تقدم حلولًا قائمة، ويرفض طلبات التعليمات غير الآمنة، ويكتب تقريره الخاص تحت `.local/`.

يمكن أيضًا مراقبة موجز Bounty المملوك للمشروع من دون تعليق أو مطالبة أو مراسلة أو تنزيل مرفقات أو تسليم عمل:

```bash
python bounty_marketplace_monitor.py once
scripts/bounty-marketplace-monitor.sh start
scripts/bounty-marketplace-monitor.sh status
scripts/bounty-marketplace-monitor.sh stop
```

تنشئ الجولة الأولى خط أساس خاصًا بهدوء. ولا تنبه الجولات اللاحقة إلا إلى معرّف Bounty جديد متاح أو إصدار أعلى، ويمنع الحد الأدنى البالغ خمس دقائق الاستطلاع المكثف. راجع [`docs/bounty-marketplace-monitor.md`](../docs/bounty-marketplace-monitor.md).

يمكن رصد المسائل العامة الجديدة ونشاط طلبات السحب في المستودعات الخمسة عشر الحالية ذات الانتباه أو العروض المرتفعة، من دون قراءة المحتوى أو الكتابة إلى GitHub:

```bash
python github_inbound_monitor.py once
scripts/github-inbound-monitor.sh start
scripts/github-inbound-monitor.sh status
scripts/github-inbound-monitor.sh stop
```

تنشئ الجولة الأولى خط أساس خاصًا فقط. ولا تنبه الجولات اللاحقة إلا إلى مفاتيح مسائل غير موجودة في الحالة المحتفظ بها. ولا يجوز أن يقل فاصل الحلقة عن 15 دقيقة. راجع [`docs/github-inbound-monitor.md`](../docs/github-inbound-monitor.md) للقائمة الثابتة المسموح بها وعقد الأمان.

يمكن مراقبة إيصالات Stripe الحقيقية من دون إنشاء صفحة دفع أو الاحتفاظ بتفاصيل العميل أو الدفع:

```bash
python stripe_revenue_monitor.py once --confirm-private-financial-read
scripts/stripe-revenue-monitor.sh start
scripts/stripe-revenue-monitor.sh status
scripts/stripe-revenue-monitor.sh stop
```

لا يرفع المراقب سوى تنبيه مراجعة خاص. ولا تُحسب الدفعة إلا بعد مطابقتها بنطاق مقبول أو طلب منتج أو سياق تبرع. راجع [`docs/stripe-revenue-monitor.md`](../docs/stripe-revenue-monitor.md).

يمكن فحص عروض Freelancer المقدمة بالتتابع عبر علامة تبويب مشروع موثقة في المتصفح المخصص:

```bash
python freelancer_inbound_monitor.py once
python freelancer_inbound_monitor.py status
```

لا يسجل المراقب سوى معرّفات الحملات وعدد الشارات المجمع وحالة العرض وترتيبه وعدد المقترحات. ولا يفتح محادثة ولا يرسل ردًا. راجع [`docs/freelancer-inbound-monitor.md`](../docs/freelancer-inbound-monitor.md).

## عزل بيئة التشغيل

يستخدم الإعداد الافتراضي شاشة واحدة بحجم 1920×1080 (`:116`) ومنفذ VNC واحدًا `5936` ومنفذ noVNC واحدًا `6136`. تبقى جميع علامات تبويب الحملات والشركاء في ملف Chrome الدائم نفسه؛ وتملأ كل نافذة مستعادة سطح المكتب كاملًا ويمكن التبديل بينها بصورة طبيعية من دون مناطق مقتصة متداخلة. يبقى CDP على `127.0.0.1:9436` والجلسة `lazypromotion-browser`. ترتبط الخدمات بالواجهة المحلية فقط، ويرفض المشغل المنافذ المجهولة المشغولة ولا يزيل إلا قفل شاشة قديم يثبت أنه يخصه. يُوقف المكدس عندما لا توجد مراجعة مرئية منتظرة، ولا يلمس المتصفح الشخصي.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## أساس مفتوح المصدر

يستخدم الإصدار الأول Playwright وSQLite بدلًا من مجدول كبير أو إطار مضاد للكشف. يناسب Postiz وMixpost الحملات المخططة، بينما لا تنتمي ميزات المراوغة أو التفاعل الآلي إلى هذا المسار القائم على المراجعة. راجع [التقييم الكامل](../docs/open-source-evaluation.md).

تُستخدم إضافات MCP الاختيارية بإصدارات مثبتة ومن دون منح عمليات النموذج وصولًا إلى المتصفح أو المجدول أو بيانات الاعتماد أو الدفع. تشمل المسارات التسعة الحالية فحص المجموعات المحلية، وتنقيح LaTeX، والمحاضرات الثنائية، ومقاطع القصص، ونماذج الكتب، وتقييم إضافات KiCad، وإعادة إنتاج OpenHI، ومراجعة LazyRemote، ودروس النطق المصغرة. يظل تجميع مقاطع الذكاء الاصطناعي متوقفًا حتى يجتاز دليل أقوى مراجعة بشرية. يدعم [نموذج تقييم إضافة KiCad القابل لإعادة الإنتاج](../examples/kicad-plugin-evaluation/) المسار المحدود الجديد، ويعرض [موجّه تعليمي مقيّد بالمصادر](../examples/source-bounded-educational-prompt/) الانضباط نفسه في المدخلات والقيود والأدلة والتقييم ضمن عمل موجه للمتعلمين. أما إدخال المعاجم فهو تخصّص قابل لإعادة الاستخدام وليس ادعاءً بأن إعلانًا مغلقًا ما زال متاحًا.

## التحقق

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py bounties.py bounty_marketplace_monitor.py github_inbound_monitor.py threads_inbound_monitor.py stripe_revenue_monitor.py freelancer_inbound_monitor.py
bash -n scripts/desktop.sh scripts/bounty-marketplace-monitor.sh scripts/github-inbound-monitor.sh scripts/stripe-revenue-monitor.sh
git diff --check
```

تتحقق هذه الأوامر من العقود المحلية فقط، ولا تثبت توافر منصة خارجية أو جودة الترجمة أو نتيجة عميل أو إيرادًا.

## الاقتباس

إذا استخدمت LazyPromotion في بحث، فاستشهد بالمستودع. يقرأ GitHub ملف [`CITATION.cff`](../CITATION.cff) ويعرض لوحة **Cite this repository**.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## الحالة والنطاق

هذا إصدار مبكر موجّه إلى Linux. قد تتغير محددات مواقع الجهات الخارجية. يبقى المشغّل البشري مسؤولًا عن الدقة والحقوق وقواعد المجتمع وشروط المنصة والإفصاح ومراجعة الدفع والإرسال النهائي.
