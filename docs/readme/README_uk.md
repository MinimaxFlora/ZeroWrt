<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · **Українська** · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Власна прошивка на базі LEDE з оновленням в один клік із вебінтерфейсу.

**Зробіть коміт — отримайте прошивку. Відкрийте LuCI і натисніть «Оновити».**

[![Збирання](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Ядро](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Платформа](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Сторінка завантаження](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Журнали збирання](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Система → Оновлення мережею → Перевірити оновлення</code>

</div>

> [!IMPORTANT]
> **Лише офіційні джерела.** Прошивка публікується виключно в
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) цього репозиторію та
> на [ota.kejizero.xyz](https://ota.kejizero.xyz/). Схожа назва репозиторію або
> скопійований README не роблять збірку офіційною.

---

ZeroWrt — невелика власна прошивка для роутерів класу OpenWrt. Вона збирається з
приватного дерева LEDE через GitHub Actions. Кожна збірка створюється з вихідного коду,
публікується разом із `SHA256SUMS` та `BUILD_INFO.txt` і потрапляє до індексу оновлень,
тому пристрій може оновити себе просто з LuCI.

Цікавий тут не черговий список пакетів, а цикл: коміт запускає збирання, збирання
публікує образ та індекс, а роутер під час наступної перевірки бачить нову версію.

## Можливості

- **Оновлення в один клік** — LuCI читає індекс, завантажує з докачуванням і прогресом, перевіряє SHA256 та образ через `sysupgrade -T`, потім записує його й перезавантажується.
- **Чесна перевірка версій** — «новіше» визначає позначка часу збирання, інакше порівнюються рядки версій; невідому дату показуємо як невідому, не вигадуємо.
- **Налаштування з workflow** — IP у LAN, ім'я хоста та три SSID із паролями Wi-Fi задаються параметрами збирання, а не правляться у файлах.
- **Брендинг Argon 3** — тло, логотип входу, favicon і палітра (`#2E9D72` / `#4CAF86`) підмінюються під час збирання.
- **Проксі-стек у комплекті** — PassWall (лише Xray) і OpenClash, синхронізуються скриптами збирання.
- **Перевірюваний конвеєр** — `ruff` і 18 юніт-тестів на кожному pull request.

## Підтримувані пристрої

| Пристрій | Платформа | Образи |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI та застарілий BIOS |

Тег release — це ім'я пристрою (`ruijie_rg-x60-new`, `x86_64`). Кожен пристрій має власний
release, тому індекс і сторінка завантаження показують їх поряд.

## Завантаження

- **Сторінка завантаження** — <https://ota.kejizero.xyz/> показує поточну збірку, журнал змін і SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> зберігає образи та `SHA256SUMS`.
- **На пристрої** — *Система → Оновлення мережею* робить те саме без завантаження в браузері.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Прошивання

**A. З OpenWrt або ImmortalWrt**
*Система → Резервна копія / Прошити*, завантажте `-squashfs-sysupgrade.bin` і не
зберігайте конфігурацію під час переходу на іншу мажорну версію.

**B. Із заводської прошивки**
Спершу встановіть завантажувач із відновленням (на цій платі це вебсторінка U-Boot), потім
завантажте той самий образ там. Не прошивайте через заводську вебпанель.

**C. Відновлення**
Завантажте `-initramfs-kernel.bin` із завантажувача, отримайте тимчасову систему і
прошийте sysupgrade-образ уже з неї.

Адреса за замовчуванням `10.0.0.1`, користувач `root`, пароль `password`. Змініть його при першому вході.

## Оновлення мережею

До прошивки входить `luci-app-ota`:

- індекс за замовчуванням — `https://ota.kejizero.xyz/ota.json`, змінюється в *Система → Оновлення мережею → Налаштування*;
- SHA256 обов'язковий: запис без нього відхиляється, а при розбіжності завантаження видаляється;
- відкритий `http` заборонено, доки не ввімкнено «дозволити небезпечні з'єднання»;
- ключ пристрою визначається з `/etc/ota/build.json`, моделі з device tree, `board_name` та архітектури, і приймаються обидва написання (`vendor,device` і `vendor_device`).

## Збирання

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Пуш у `main` також запускає збирання. Секрети, параметри, ccache і кожен крок описані в
[docs/BUILD.md](../BUILD.md).

## FAQ

**Де вихідний код?** Дерево LEDE приватне. Тут лежить конвеєр, матеріали брендингу та тести.

**Чому немає образу `factory`?** Ці плати прошиваються зі сторінки відновлення завантажувача, яка приймає sysupgrade-образ напряму.

**Чи можна вказати власний індекс?** Так — спрямуйте `api_url` на сумісний JSON і розмістіть його будь-де.

## Подяки

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Ліцензія

Скрипти, матеріали брендингу й документація в цьому репозиторії поширюються за **GPL-2.0** — див. [LICENSE](../../LICENSE).

Сама прошивка містить OpenWrt, LEDE і багато вищестоящих компонентів, кожен під своєю ліцензією. Під час розповсюдження образу ці ліцензії також діють; GPL-2.0 зокрема вимагає надати відповідний вихідний код.

## Відмова від відповідальності

Прошивання може перетворити пристрій на цеглину. Зробіть резервну копію заводської прошивки
та своєї конфігурації і заздалегідь розберіться зі шляхом відновлення. Прошивка надається
як є, без гарантій.

---

Для супровідників: [docs/BUILD.md](../BUILD.md) · Інші мови: [docs/readme](.)
