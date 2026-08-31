[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*اعثر على حاجة حقيقية، واكتب إجابة مفيدة، ووضّح صلتك بالمشروع، ثم دع إنسانًا يقرر ما إذا كان سيرسلها.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion مساعد محلي لاكتشاف الاحتياجات الاجتماعية يعتمد المراجعة قبل النشر. يبحث في واجهة Reddit أو X أو Instagram الحقيقية عبر ملف Chrome دائم ومرئي، ويحفظ النتائج المحتملة في SQLite، ويكتب مسودة موثقة باستخدام `gpt-5.6-sol` بجهد استدلال منخفض، ثم يتوقف قبل الإرسال العلني. صُمم لمساعدة الناس بمشروعات مفتوحة المصدر ذات صلة، لا للتسويق الجماعي.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## عقد التشغيل

- المساعدة أولًا: تجيب الرسالة عن الحاجة المحددة قبل ذكر أي مشروع.
- صلة واضحة: يتضمن رابط المشروع تصريحًا صريحًا مثل «أنا أحافظ على…» أو «أنا بنيت…».
- شخص واحد وقرار واحد: لا ردود جماعية ولا رسائل خاصة غير مطلوبة ولا تصويت أو متابعة أو حلقات تفاعل آلية.
- وعي بالنشر المتقاطع: تُجمع النسخ الطويلة المتطابقة للكاتب نفسه تحت مرشح أساسي واحد، مع تفضيل النسخة التي تلقت ردًا بالفعل.
- محتوى حديث افتراضيًا: تُسجل أوقات المصدر وعدد التعليقات، وتُعلّم المشاركات الأقدم من 30 يومًا كقديمة ويرفضها منشئ المسودات.
- موافقة دقيقة: يؤدي تغيير المسودة إلى إبطال الموافقة المؤقتة المرتبطة ببصمة المحتوى.
- تشغيل مرئي: يعمل Chrome داخل noVNC وتبقى لقطات الإثبات المحلية خارج Git.
- الجلسات خاصة: لا تدخل بيانات الدخول أو ملفات الارتباط أو ملفات المتصفح أو المرشحون أو المسودات أو الموافقات في المستودع.

## المحتويات الحالية

| المسار | الغرض |
| --- | --- |
| [`promotion.py`](../promotion.py) | سجل SQLite والمطابقة وصياغة Codex والموافقات |
| [`browser.py`](../browser.py) | الاكتشاف والفحص والتحضير والإرسال المحمي عبر Playwright/CDP |
| [`catalog.json`](../catalog.json) | ربط الاحتياجات الحقيقية بالمشروعات التي تتم صيانتها |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | سطح مكتب واحد دائم من Xvfb/x11vnc/noVNC/Chrome |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | تقييم البدائل مفتوحة المصدر |
| [`tests/`](../tests/) | اختبارات المطابقة والتكرار والموافقة الدقيقة |

## بداية سريعة

يتطلب Linux وPython 3.10+ وChrome وPlaywright لـ Python وXvfb وx11vnc وnoVNC/websockify و`tmux` وواجهة Codex CLI مسجّلًا دخولها.

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
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

لا ترسل إلا بعد أن يراجع إنسان الوجهة والنص كاملًا:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

## عزل بيئة التشغيل

الإعداد الافتراضي هو الشاشة `:116` وVNC على `127.0.0.1:5936` وnoVNC على `127.0.0.1:6136` وCDP على `127.0.0.1:9436` وجلسة `lazypromotion-browser`. ترتبط الخدمات بالواجهة المحلية فقط، ويرفض المشغل المنافذ المجهولة المشغولة ولا يزيل إلا قفل شاشة قديم يثبت أنه يخصه.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## أساس مفتوح المصدر

يستخدم الإصدار الأول Playwright وSQLite بدلًا من مجدول كبير أو إطار مضاد للكشف. يناسب Postiz وMixpost الحملات المخططة، بينما لا تنتمي ميزات المراوغة أو التفاعل الآلي إلى هذا المسار القائم على المراجعة. راجع [التقييم الكامل](../docs/open-source-evaluation.md).

## التحقق

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

هذا إصدار مبكر موجّه إلى Linux. قد تتغير محددات مواقع الجهات الخارجية. يبقى المشغّل البشري مسؤولًا عن الدقة وقواعد المجتمع وشروط المنصة والإفصاح والإرسال النهائي.
