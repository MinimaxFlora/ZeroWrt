<div align="center" dir="rtl">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · **فارسی** · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### فریمور سفارشی مبتنی بر LEDE، با به‌روزرسانی آنلاین با یک کلیک.

**کامیت را پوش کن، فریمور بگیر. LuCI را باز کن و به‌روزرسانی را بزن.**

[![ساخت](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![هسته](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![پلتفرم](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[صفحه دانلود](https://ota.kejizero.xyz/) · [انتشارها](https://github.com/MinimaxFlora/ZeroWrt/releases) · [گزارش ساخت](https://github.com/MinimaxFlora/ZeroWrt/actions) · [مسائل](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>سیستم ← به‌روزرسانی آنلاین ← بررسی به‌روزرسانی‌ها</code>

</div>

> [!IMPORTANT]
> **فقط از منابع رسمی.** فریمور تنها در
> [انتشارهای](https://github.com/MinimaxFlora/ZeroWrt/releases) همین مخزن و روی
> [ota.kejizero.xyz](https://ota.kejizero.xyz/) منتشر می‌شود. نام مخزن مشابه یا README
> کپی‌شده یک ساخت را رسمی نمی‌کند.

---

ZeroWrt یک فریمور سفارشی کوچک برای روترهای خانواده OpenWrt است که با GitHub Actions از یک
درخت خصوصی LEDE ساخته می‌شود. هر ساخت از کد منبع تولید، همراه با `SHA256SUMS` و
`BUILD_INFO.txt` منتشر و در فهرست به‌روزرسانی ثبت می‌شود تا دستگاه خودش را از LuCI به‌روز کند.

نکتهٔ جالب فهرست دیگری از بسته‌ها نیست، بلکه این چرخه است: یک کامیت ساخت را آغاز می‌کند، ساخت
تصویر و فهرست را منتشر می‌کند و روتر در بررسی بعدی نسخهٔ تازه را می‌بیند.

## ویژگی‌ها

- **به‌روزرسانی با یک کلیک** — LuCI فهرست را می‌خواند، با ادامهٔ دانلود و نمایش پیشرفت دریافت می‌کند، SHA256 و تصویر را با `sysupgrade -T` بررسی می‌کند و سپس می‌نویسد و ری‌استارت می‌شود.
- **مقایسهٔ صادقانهٔ نسخه** — مهر زمان ساخت تعیین می‌کند «تازه‌تر» کدام است، وگرنه رشتهٔ نسخه مقایسه می‌شود؛ تاریخ نامعلوم همان نامعلوم نمایش داده می‌شود و از خودمان نمی‌سازیم.
- **پیکربندی از سوی workflow** — نشانی LAN، نام میزبان و سه SSID و گذرواژهٔ وای‌فای ورودی ساخت هستند، نه فایل دست‌کاری‌شده.
- **هویت Argon 3** — پس‌زمینه، لوگوی ورود، favicon و پالت (`#2E9D72` / `#4CAF86`) هنگام ساخت جایگزین می‌شوند.
- **پشتهٔ پروکسی همراه** — PassWall (فقط Xray) و OpenClash که اسکریپت‌های ساخت هم‌گام نگه می‌دارند.
- **خط تولید دارای دروازه** — `ruff` و ۱۸ آزمون واحد روی هر pull request.

## دستگاه‌های پشتیبانی‌شده

| دستگاه | پلتفرم | تصاویر |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin` و `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI و BIOS قدیمی |

برچسب انتشار همان نام دستگاه است (`ruijie_rg-x60-new` و `x86_64`). هر دستگاه انتشار خودش
را دارد، بنابراین فهرست و صفحهٔ دانلود می‌توانند کنار هم نمایششان دهند.

## دانلود

- **صفحهٔ دانلود** — <https://ota.kejizero.xyz/> ساخت جاری، تغییرات و SHA256 را نشان می‌دهد.
- **انتشارهای GitHub** — <https://github.com/MinimaxFlora/ZeroWrt/releases> تصاویر و `SHA256SUMS` را نگه می‌دارد.
- **روی خود دستگاه** — *سیستم ← به‌روزرسانی آنلاین* همین کار را بدون دانلود در مرورگر انجام می‌دهد.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## نصب

**الف. از OpenWrt یا ImmortalWrt**
*سیستم ← پشتیبان‌گیری / نوشتن فریمور*، فایل `-squashfs-sysupgrade.bin` را بارگذاری کن و
هنگام عبور از نسخهٔ اصلی، پیکربندی را نگه ندار.

**ب. از فریمور کارخانه**
ابتدا صفحهٔ بازیابی بوت‌لودر را نصب کن (روی این برد معمولاً صفحهٔ وب U-Boot) و همان تصویر را
آنجا بارگذاری کن. از رابط کارخانه مستقیم ننویس.

**ج. بازیابی**
`-initramfs-kernel.bin` را از بوت‌لودر بالا بیاور تا یک سیستم موقت داشته باشی، بعد از همان‌جا
تصویر sysupgrade را بنویس.

نشانی پیش‌فرض `10.0.0.1`، کاربر `root`، گذرواژه `password`. در نخستین ورود تغییرش بده.

## به‌روزرسانی آنلاین

فریمور شامل `luci-app-ota` است:

- فهرست پیش‌فرض `https://ota.kejizero.xyz/ota.json` است و از *سیستم ← به‌روزرسانی آنلاین ← پیکربندی* تغییر می‌کند؛
- SHA256 اجباری است: مدخل بدون آن رد می‌شود و در صورت ناسازگاری، فایل دانلودشده حذف می‌شود؛
- `http` بدون رمزنگاری رد می‌شود مگر آنکه گزینهٔ اجازهٔ اتصال ناامن را روشن کنی؛
- کلید دستگاه به‌ترتیب از `/etc/ota/build.json`، model درخت دستگاه، `board_name` و معماری استخراج می‌شود و هر دو نوشتار (`vendor,device` و `vendor_device`) پذیرفته می‌شود.

## ساخت

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

پوش به `main` هم ساخت را راه می‌اندازد. اسرار، ورودی‌ها، ccache و هر مرحله در
[docs/BUILD.md](../BUILD.md) آمده است.

## پرسش‌های متداول

**کد منبع کجاست؟** درخت LEDE خصوصی است. این مخزن خط تولید، دارایی‌های برند و آزمون‌ها را دارد.

**چرا تصویر `factory` نیست؟** این بردها از صفحهٔ بازیابی بوت‌لودر نصب می‌شوند که تصویر sysupgrade را مستقیم می‌پذیرد.

**می‌توانم فهرست خودم را بگذارم؟** بله — `api_url` را به یک JSON سازگار بده و هرجا خواستی میزبانی کن.

## سپاسگزاری

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## پروانه

اسکریپت‌ها، دارایی‌های برند و مستندات این مخزن با **GPL-2.0** منتشر می‌شوند — [LICENSE](../../LICENSE).

خود فریمور شامل OpenWrt، LEDE و بسیاری از اجزای بالادست است و هرکدام پروانهٔ خود را دارد. هنگام بازتوزیع تصویر، آن پروانه‌ها هم اعمال می‌شوند؛ به‌ویژه GPL-2.0 دسترسی به کد منبع متناظر را الزامی می‌کند.

## سلب مسئولیت

نوشتن فریمور می‌تواند دستگاه را از کار بیندازد. از فریمور کارخانه و پیکربندی خودت نسخهٔ
پشتیبان بگیر و مسیر بازیابی را پیش از شروع بدان. فریمور همان‌گونه که هست ارائه می‌شود،
بدون ضمانت.

---

یادداشت نگه‌داران: [docs/BUILD.md](../BUILD.md) · زبان‌های دیگر: [docs/readme](.)
