<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · **Русский** · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Собственная прошивка на базе LEDE с обновлением в один клик из веб-интерфейса.

**Одна команда собирает, один клик обновляет.**

[![Сборка](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Ядро](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Платформа](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Страница загрузки](https://ota.tatalvpai.vip/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Журналы сборки](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Система → Обновление по сети → Проверить обновления</code>

</div>

> [!IMPORTANT]
> **Только официальные источники.** Прошивка публикуется исключительно в
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) этого репозитория и
> на [ota.tatalvpai.vip](https://ota.tatalvpai.vip/). Похожее имя репозитория или
> скопированный README не делают сборку официальной.

---

ZeroWrt — небольшая собственная прошивка для роутеров класса OpenWrt. Она собирается из
приватного дерева LEDE через GitHub Actions. Каждая сборка создаётся из исходников,
публикуется вместе с `SHA256SUMS` и `BUILD_INFO.txt` и попадает в индекс обновлений,
поэтому устройство может обновить себя прямо из LuCI.

Интересен здесь не очередной список пакетов, а цикл: сборка
публикует образ и индекс, а роутер при следующей проверке видит новую версию.

## Возможности

- **Обновление в один клик** — LuCI читает индекс, скачивает с докачкой и прогрессом, проверяет SHA256 и образ через `sysupgrade -T`, затем записывает его и перезагружается.
- **Честная проверка версий** — «новее» решает метка времени сборки, иначе сравниваются строки версий; неизвестную дату так и показываем, не выдумываем.
- **Настройки из workflow** — IP в LAN, имя хоста и три SSID с паролями Wi-Fi задаются входными параметрами, а не правятся в файлах.
- **Брендинг Argon 3** — фон, логотип входа, favicon и палитра (`#2E9D72` / `#4CAF86`) подменяются при сборке.
- **Прокси-стек включён** — PassWall (только Sing-Box) и OpenClash, синхронизируются скриптами сборки.
- **Проверяемый конвейер** — `ruff` и 18 юнит-тестов на каждом pull request.

## Поддерживаемые устройства

| Устройство | Платформа | Образы |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI и устаревший BIOS |

Тег release — это имя устройства (`ruijie_rg-x60-new`, `x86_64`). У каждого устройства
свой release, поэтому индекс и страница загрузки показывают их рядом.

## Загрузка

- **Страница загрузки** — <https://ota.tatalvpai.vip/> показывает текущую сборку, журнал изменений и SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> хранит образы и `SHA256SUMS`.
- **На устройстве** — *Система → Обновление по сети* делает то же самое без загрузки в браузере.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Прошивка

**A. Из OpenWrt или ImmortalWrt**
*Система → Резервная копия / Прошить*, загрузите `-squashfs-sysupgrade.bin` и не
сохраняйте конфигурацию при переходе на другую мажорную версию.

**B. С заводской прошивки**
Сначала установите загрузчик с восстановлением (на этой плате это веб-страница U-Boot),
затем загрузите тот же образ там. Не прошивайте через заводскую веб-панель.

**C. Восстановление**
Загрузите `-initramfs-kernel.bin` из загрузчика, получите временную систему и прошейте
sysupgrade-образ уже из неё.

Адрес по умолчанию `10.0.0.1`, пользователь `root`, пароль `password`. Смените его при первом входе.

## Обновление по сети

В прошивку входит `luci-app-ota`:

- индекс по умолчанию — `https://ota.tatalvpai.vip/ota.json`, меняется в *Система → Обновление по сети → Настройки*;
- SHA256 обязателен: запись без него отклоняется, а при несовпадении загрузка удаляется;
- открытый `http` запрещён, пока не включено «разрешить небезопасные соединения»;
- ключ устройства определяется по `/etc/ota/build.json`, модели из device tree, `board_name` и архитектуре, и принимаются оба написания (`vendor,device` и `vendor_device`).

## Сборка

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Сборка запускается вручную: *Actions → Build ZeroWrt → Run workflow*. Триггера `push` нет, поэтому слияние кода не запускает шестичасовую компиляцию. Секреты, параметры, ccache и каждый шаг описаны в [docs/BUILD.md](../BUILD.md).

## FAQ

**Где исходники?** Дерево LEDE приватное. Здесь лежит конвейер, материалы брендинга и тесты.

**Почему нет образа `factory`?** Эти платы прошиваются со страницы восстановления загрузчика, которая принимает sysupgrade-образ напрямую.

**Можно указать свой индекс?** Да — направьте `api_url` на совместимый JSON и разместите его где угодно.

## Благодарности

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Лицензия

Скрипты, материалы брендинга и документация в этом репозитории распространяются по **GPL-2.0** — см. [LICENSE](../../LICENSE).

Сама прошивка включает OpenWrt, LEDE и множество вышестоящих компонентов, каждый под своей лицензией. При распространении образа эти лицензии тоже действуют; GPL-2.0, в частности, требует предоставить соответствующий исходный код.

## Отказ от ответственности

Прошивка может превратить устройство в кирпич. Сделайте резервную копию заводской прошивки
и своей конфигурации и заранее разберитесь с путём восстановления. Прошивка
предоставляется как есть, без гарантий.

---

Для сопровождающих: [docs/BUILD.md](../BUILD.md) · Другие языки: [docs/readme](.)
