<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · **Deutsch** · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Eigene Firmware auf LEDE-Basis, mit Online-Update per Klick.

**Commit pushen, Firmware bekommen. LuCI öffnen, Update anklicken.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Ziel](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Downloadseite](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Build-Logs](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>System → Online-Aktualisierung → Nach Updates suchen</code>

</div>

> [!IMPORTANT]
> **Nur aus offiziellen Quellen.** Die Firmware erscheint ausschließlich in den
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) dieses Repositories
> und auf [ota.kejizero.xyz](https://ota.kejizero.xyz/). Ein ähnlicher
> Repository-Name oder eine kopierte README macht einen Build nicht offiziell.

---

ZeroWrt ist eine kleine eigene Firmware für Router der OpenWrt-Klasse, gebaut aus einem
privaten LEDE-Baum über GitHub Actions. Jeder Build entsteht aus dem Quellcode, wird mit
`SHA256SUMS` und `BUILD_INFO.txt` veröffentlicht und in einen Update-Index eingetragen,
sodass das Gerät sich selbst über LuCI aktualisieren kann.

Das Interessante ist nicht eine weitere Paketliste, sondern der Kreislauf: ein Commit
startet einen Build, der Build veröffentlicht Image und Index, und der Router sieht die
neue Version bei der nächsten Prüfung.

## Funktionen

- **Update per Klick** — LuCI liest den Index, lädt mit Fortsetzung und Fortschritt, prüft SHA256 und das Image mit `sysupgrade -T` und schreibt es dann.
- **Ehrliche Versionsprüfung** — der Build-Zeitstempel entscheidet, sonst die Versionszeichenkette; ein unbekanntes Datum wird als unbekannt angezeigt und nicht erfunden.
- **Konfiguration aus dem Workflow** — LAN-IP, Hostname sowie drei WLAN-SSIDs und -Passwörter sind Eingaben, keine handgepflegten Dateien.
- **Argon-3-Branding** — Hintergrund, Login-Logo, Favicon und Palette (`#2E9D72` / `#4CAF86`) werden beim Build ersetzt.
- **Proxy-Stack enthalten** — PassWall (nur Xray) und OpenClash, vom Build synchron gehalten.
- **Geprüfte Pipeline** — `ruff` und 18 Unit-Tests laufen bei jedem Pull Request.

## Unterstützte Geräte

| Gerät | Ziel | Images |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI und klassisches BIOS |

Release-Tags sind die Gerätenamen (`ruijie_rg-x60-new`, `x86_64`). Jedes Gerät behält
sein eigenes Release, daher können Index und Downloadseite beide nebeneinander listen.

## Download

- **Downloadseite** — <https://ota.kejizero.xyz/> zeigt aktuellen Build, Changelog und SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> enthält Images und `SHA256SUMS`.
- **Auf dem Gerät** — *System → Online-Aktualisierung* erledigt dasselbe ohne Browser-Download.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flashen

**A. Aus OpenWrt oder ImmortalWrt**
*System → Backup / Firmware flashen*, die `-squashfs-sysupgrade.bin` hochladen und bei
einem Hauptversionswechsel die Konfiguration nicht behalten.

**B. Aus der Werksfirmware**
Zuerst die Bootloader-Recovery einrichten (bei dieser Platine die übliche U-Boot-Webseite),
dann dort dasselbe Image hochladen. Nicht über die Werksoberfläche flashen.

**C. Wiederherstellung**
`-initramfs-kernel.bin` aus dem Bootloader starten, um ein temporäres System zu erhalten,
und daraus das Sysupgrade-Image schreiben.

Standardadresse `10.0.0.1`, Benutzer `root`, Passwort `password`. Beim ersten Login ändern.

## Online-Aktualisierung

`luci-app-ota` ist enthalten:

- der Index steht standardmäßig auf `https://ota.kejizero.xyz/ota.json` und lässt sich unter *System → Online-Aktualisierung → Konfiguration* ändern;
- SHA256 ist Pflicht: Einträge ohne Prüfsumme werden abgelehnt, bei Abweichung wird der Download gelöscht;
- reines `http` wird abgelehnt, solange nicht *unsichere Verbindungen erlauben* aktiv ist;
- der Geräteschlüssel wird aus `/etc/ota/build.json`, dem Device-Tree-Model, `board_name` und der Architektur ermittelt; beide Schreibweisen (`vendor,device` und `vendor_device`) werden akzeptiert.

## Bauen

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Ein Push auf `main` baut ebenfalls. Secrets, Eingaben, ccache und jeder Schritt stehen in
[docs/BUILD.md](../BUILD.md).

## FAQ

**Wo ist der Quellcode?** Der LEDE-Baum ist privat. Dieses Repository enthält Pipeline, Branding-Assets und Tests.

**Warum gibt es kein `factory`-Image?** Diese Platinen werden über ihre Bootloader-Webseite geflasht, die das Sysupgrade-Image direkt annimmt.

**Kann ich meinen eigenen Index verwenden?** Ja — `api_url` auf ein kompatibles JSON zeigen und selbst hosten.

## Danksagung

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Lizenz

Skripte, Branding-Assets und Dokumentation in diesem Repository stehen unter **GPL-2.0** — siehe [LICENSE](../../LICENSE).

Das Firmware-Image selbst enthält OpenWrt, LEDE und viele weitere Upstream-Komponenten, jede unter ihrer eigenen Lizenz. Wer ein Image weitergibt, muss diese Lizenzen ebenfalls einhalten; GPL-2.0 verlangt insbesondere die Bereitstellung des zugehörigen Quellcodes.

## Haftungsausschluss

Flashen kann ein Gerät unbrauchbar machen. Sichere Werksfirmware und Konfiguration und
verstehe den Wiederherstellungsweg, bevor du beginnst. Die Firmware wird ohne Gewähr
bereitgestellt.

---

Für Maintainer: [docs/BUILD.md](../BUILD.md) · Andere Sprachen: [docs/readme](.)
