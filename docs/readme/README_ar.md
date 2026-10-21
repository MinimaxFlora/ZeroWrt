<div align="center" dir="rtl">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · **العربية** · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### نظام ثابت (firmware) مخصص مبني على LEDE، مع تحديث عبر الإنترنت بنقرة واحدة.

**ادفع التغيير فيحصل البناء، ثم افتح LuCI واضغط تحديث.**

[![البناء](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![النواة](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![المنصة](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[صفحة التنزيل](https://ota.kejizero.xyz/) · [الإصدارات](https://github.com/MinimaxFlora/ZeroWrt/releases) · [سجلات البناء](https://github.com/MinimaxFlora/ZeroWrt/actions) · [المشكلات](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>النظام ← التحديث عبر الإنترنت ← التحقق من التحديثات</code>

</div>

> [!IMPORTANT]
> **من المصادر الرسمية فقط.** يُنشر النظام الثابت حصريًا في
> [الإصدارات](https://github.com/MinimaxFlora/ZeroWrt/releases) لهذا المستودع وعلى
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). اسم مستودع مشابه أو نسخة منقولة من
> README لا تجعل البناء رسميًا.

---

ZeroWrt نظام ثابت مخصص صغير لمجموعة راوترات OpenWrt، يُبنى من شجرة LEDE خاصة عبر GitHub
Actions. كل بناء يُنتج من الكود المصدري، ويُنشر مع `SHA256SUMS` و`BUILD_INFO.txt`،
ويُسجَّل في فهرس التحديثات كي يستطيع الجهاز تحديث نفسه من LuCI.

المثير ليس قائمة حزم أخرى، بل الحلقة: التغيير يبدأ البناء، والبناء ينشر الصورة والفهرس، ثم
يرى الراوتر النسخة الجديدة عند التحقق التالي.

## الميزات

- **تحديث بنقرة واحدة** — يقرأ LuCI الفهرس، ويُنزّل مع الاستكمال وشريط التقدم، ويتحقق من SHA256 ومن الصورة عبر `sysupgrade -T`، ثم يكتبها ويعيد التشغيل.
- **مقارنة إصدارات صادقة** — يحدد طابع وقت البناء الأحدث، وإن لم يوجد تُقارن سلاسل الإصدار؛ التاريخ المجهول يظهر مجهولًا ولا يُختلق.
- **الإعداد من سير العمل** — عنوان LAN واسم المضيف وثلاث شبكات Wi-Fi وكلمات مرورها مدخلات بناء، لا ملفات تُحرَّر يدويًا.
- **هوية Argon 3** — الخلفية وشعار الدخول وأيقونة الموقع ولوحة الألوان (`#2E9D72` / `#4CAF86`) تُستبدل أثناء البناء.
- **حزمة وسيط مدمجة** — PassWall (Xray فقط) وOpenClash، تُزامنهما سكربتات البناء.
- **خط أنابيب محكوم** — `ruff` و18 اختبار وحدة في كل طلب دمج.

## الأجهزة المدعومة

| الجهاز | المنصة | الصور |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin` و`-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI وBIOS القديم |

وسوم الإصدارات هي أسماء الأجهزة (`ruijie_rg-x60-new` و`x86_64`). لكل جهاز إصداره الخاص،
لذا يمكن للفهرس وصفحة التنزيل عرضها جنبًا إلى جنب.

## التنزيل

- **صفحة التنزيل** — <https://ota.kejizero.xyz/> تعرض البناء الحالي وسجل التغييرات وSHA256.
- **إصدارات GitHub** — <https://github.com/MinimaxFlora/ZeroWrt/releases> تحفظ الصور و`SHA256SUMS`.
- **على الجهاز** — *النظام ← التحديث عبر الإنترنت* يفعل الشيء نفسه دون تنزيل من المتصفح.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## التثبيت

**أ. من OpenWrt أو ImmortalWrt**
*النظام ← نسخ احتياطي / تثبيت نظام ثابت*، وارفع ملف `-squashfs-sysupgrade.bin`، ولا تحتفظ
بالإعدادات عند الانتقال بين إصدارات رئيسية.

**ب. من نظام المصنع**
ثبّت صفحة الاستعادة الخاصة بالمُقلع أولًا (وهي عادة صفحة U-Boot على هذه اللوحة)، ثم ارفع
الصورة نفسها هناك. لا تثبّت من واجهة المصنع مباشرة.

**ج. الاستعادة**
أقلع `-initramfs-kernel.bin` من المُقلع للحصول على نظام مؤقت، ثم ثبّت صورة sysupgrade منه.

العنوان الافتراضي `10.0.0.1`، المستخدم `root`، كلمة المرور `password`. غيّرها عند أول دخول.

## التحديث عبر الإنترنت

يشمل النظام الثابت `luci-app-ota`:

- الفهرس الافتراضي `https://ota.kejizero.xyz/ota.json` ويمكن تغييره من *النظام ← التحديث عبر الإنترنت ← الإعدادات*؛
- SHA256 إلزامي: يُرفض أي مدخل بدونه، وعند عدم التطابق يُحذف التنزيل؛
- يُرفض `http` غير المشفّر ما لم يُفعَّل خيار السماح بالاتصالات غير الآمنة؛
- يُستنتج مفتاح الجهاز من `/etc/ota/build.json` ثم model في شجرة الأجهزة ثم `board_name` ثم المعمارية، ويُقبل الوجهان `vendor,device` و`vendor_device`.

## البناء

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

الدفع إلى `main` يبني أيضًا. الأسرار والمدخلات وccache وكل خطوة موثّقة في
[docs/BUILD.md](../BUILD.md).

## الأسئلة الشائعة

**أين الكود المصدري؟** شجرة LEDE خاصة. هذا المستودع يضم خط الأنابيب وأصول الهوية والاختبارات.

**لماذا لا توجد صورة `factory`؟** هذه اللوحات تُثبَّت عبر صفحة استعادة المُقلع التي تقبل صورة sysupgrade مباشرة.

**هل أستطيع استخدام فهرس خاص بي؟** نعم، وجّه `api_url` إلى JSON متوافق واستضفه حيث تشاء.

## شكر وتقدير

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## الترخيص

تُنشر سكربتات هذا المستودع وأصول الهوية والتوثيق بموجب **GPL-2.0** — انظر [LICENSE](../../LICENSE).

النظام الثابت نفسه يضم OpenWrt وLEDE وكثيرًا من المكوّنات المنبع، ولكل منها ترخيصه. وعند إعادة توزيع الصورة تسري تلك التراخيص أيضًا؛ وGPL-2.0 على وجه الخصوص يشترط إتاحة الشيفرة المصدرية المقابلة.

## إخلاء المسؤولية

تثبيت النظام الثابت قد يُعطّل الجهاز. خُذ نسخة احتياطية من نظام المصنع وإعداداتك، وافهم
مسار الاستعادة قبل البدء. يُقدَّم النظام الثابت كما هو، دون أي ضمان.

---

ملاحظات المشرفين: [docs/BUILD.md](../BUILD.md) · لغات أخرى: [docs/readme](.)
