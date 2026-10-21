<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · **Polski** · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Własny firmware oparty na LEDE, z aktualizacją online jednym kliknięciem.

**Zrób commit, dostań firmware. Otwórz LuCI i kliknij aktualizuj.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Jądro](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Platforma](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Strona pobierania](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Logi budowania](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>System → Aktualizacja online → Sprawdź aktualizacje</code>

</div>

> [!IMPORTANT]
> **Tylko oficjalne źródła.** Firmware publikujemy wyłącznie w
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) tego repozytorium oraz na
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). Podobna nazwa repozytorium lub
> skopiowany README nie czynią builda oficjalnym.

---

ZeroWrt to niewielki własny firmware dla routerów klasy OpenWrt, budowany z prywatnego
drzewa LEDE przez GitHub Actions. Każdy build powstaje ze źródeł, jest publikowany razem z
`SHA256SUMS` i `BUILD_INFO.txt` i trafia do indeksu aktualizacji, dzięki czemu urządzenie
może zaktualizować się samo z LuCI.

Ciekawe nie jest kolejna lista pakietów, tylko pętla: commit uruchamia build, build
publikuje obraz i indeks, a router przy następnym sprawdzeniu widzi nową wersję.

## Funkcje

- **Aktualizacja jednym kliknięciem** — LuCI czyta indeks, pobiera z wznawianiem i postępem, weryfikuje SHA256 oraz obraz przez `sysupgrade -T`, a potem zapisuje go i restartuje.
- **Uczciwe porównywanie wersji** — o „nowszy” decyduje znacznik czasu builda, w razie braku porównywane są ciągi wersji; nieznanej daty nie wymyślamy, pokazujemy „nieznana”.
- **Konfiguracja z workflow** — adres LAN, nazwa hosta oraz trzy SSID i hasła Wi-Fi to parametry builda, a nie ręcznie edytowane pliki.
- **Branding Argon 3** — tło, logo logowania, favicon i paleta (`#2E9D72` / `#4CAF86`) są podmieniane podczas budowania.
- **Zestaw proxy w komplecie** — PassWall (tylko Xray) i OpenClash, synchronizowane przez skrypty budujące.
- **Kontrolowany potok** — `ruff` i 18 testów jednostkowych przy każdym pull requeście.

## Obsługiwane urządzenia

| Urządzenie | Platforma | Obrazy |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI oraz klasyczny BIOS |

Tagi release to nazwy urządzeń (`ruijie_rg-x60-new`, `x86_64`). Każde urządzenie ma własny
release, więc indeks i strona pobierania mogą pokazywać je obok siebie.

## Pobieranie

- **Strona pobierania** — <https://ota.kejizero.xyz/> pokazuje bieżący build, changelog i SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> przechowuje obrazy i `SHA256SUMS`.
- **Na urządzeniu** — *System → Aktualizacja online* robi to samo bez pobierania w przeglądarce.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Wgrywanie

**A. Z OpenWrt lub ImmortalWrt**
*System → Kopia zapasowa / Wgraj firmware*, wyślij `-squashfs-sysupgrade.bin` i przy
zmianie wersji głównej nie zachowuj konfiguracji.

**B. Z firmware producenta**
Najpierw zainstaluj recovery bootloadera (na tej płytce to zwykle strona U-Boot), a potem
wgraj tam ten sam obraz. Nie wgrywaj przez fabryczny panel.

**C. Odzyskiwanie**
Uruchom `-initramfs-kernel.bin` z bootloadera, aby dostać system tymczasowy, i z niego wgraj
obraz sysupgrade.

Domyślny adres `10.0.0.1`, użytkownik `root`, hasło `password`. Zmień je przy pierwszym logowaniu.

## Aktualizacja online

Firmware zawiera `luci-app-ota`:

- indeks domyślnie to `https://ota.kejizero.xyz/ota.json` i można go zmienić w *System → Aktualizacja online → Konfiguracja*;
- SHA256 jest obowiązkowy: wpis bez niego jest odrzucany, a niezgodność usuwa pobrany plik;
- czysty `http` jest odrzucany, dopóki nie włączysz *zezwalaj na niezabezpieczone połączenia*;
- klucz urządzenia ustalany jest z `/etc/ota/build.json`, modelu z device tree, `board_name` i architektury, a oba zapisy (`vendor,device` i `vendor_device`) są akceptowane.

## Budowanie

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Push do `main` też buduje. Sekrety, parametry, ccache i każdy krok opisano w
[docs/BUILD.md](../BUILD.md).

## FAQ

**Gdzie są źródła?** Drzewo LEDE jest prywatne. To repozytorium zawiera potok, materiały brandingowe i testy.

**Dlaczego nie ma obrazu `factory`?** Te płytki wgrywa się ze strony recovery bootloadera, która przyjmuje obraz sysupgrade bezpośrednio.

**Czy mogę użyć własnego indeksu?** Tak — ustaw `api_url` na dowolny zgodny JSON i hostuj go gdzie chcesz.

## Podziękowania

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Licencja

Skrypty, materiały brandingowe i dokumentacja w tym repozytorium są udostępniane na licencji **GPL-2.0** — zobacz [LICENSE](../../LICENSE).

Samo firmware zawiera OpenWrt, LEDE i wiele komponentów nadrzędnych, każdy na własnej licencji. Redystrybuując obraz, trzeba tych licencji przestrzegać; GPL-2.0 wymaga w szczególności udostępnienia odpowiadającego kodu źródłowego.

## Zastrzeżenia

Wgrywanie firmware może uszkodzić urządzenie. Zrób kopię firmware producenta i swojej
konfiguracji oraz poznaj drogę odzyskiwania, zanim zaczniesz. Firmware jest dostarczany
tak jak jest, bez gwarancji.

---

Dla opiekunów: [docs/BUILD.md](../BUILD.md) · Inne języki: [docs/readme](.)
