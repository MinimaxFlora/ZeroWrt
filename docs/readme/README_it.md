<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · **Italiano** · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware personalizzato basato su LEDE, con aggiornamento online in un clic.

**Fai il push, ottieni un firmware. Apri LuCI e premi aggiorna.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Target](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)

[Pagina di download](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Log di build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Sistema → Aggiornamento online → Verifica aggiornamenti</code>

</div>

> [!IMPORTANT]
> **Solo fonti ufficiali.** Il firmware è pubblicato esclusivamente nelle
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) di questo repository e su
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). Un nome di repository simile o un
> README copiato non rendono ufficiale una build.

---

ZeroWrt è un firmware personalizzato per router della classe OpenWrt, compilato da un albero
LEDE privato tramite GitHub Actions. Ogni build nasce dal codice sorgente, viene pubblicata
con `SHA256SUMS` e `BUILD_INFO.txt` e inserita in un indice di aggiornamento, così il
dispositivo può aggiornarsi da solo da LuCI.

La parte interessante non è l'ennesima lista di pacchetti, ma il ciclo: un commit avvia una
build, la build pubblica immagine e indice, e il router vede la nuova versione al controllo
successivo.

## Funzionalità

- **Aggiornamento in un clic** — LuCI legge l'indice, scarica con ripresa e avanzamento, verifica SHA256 e immagine con `sysupgrade -T`, poi la scrive e riavvia.
- **Confronto versioni onesto** — decide il timestamp di build, altrimenti la stringa di versione; una data sconosciuta resta sconosciuta, non viene inventata.
- **Configurazione dal workflow** — IP LAN, hostname e tre SSID e password Wi-Fi sono input di build, non file modificati a mano.
- **Branding Argon 3** — sfondo, logo di accesso, favicon e palette (`#2E9D72` / `#4CAF86`) sostituiti in fase di build.
- **Stack proxy incluso** — PassWall (solo Xray) e OpenClash, sincronizzati dagli script di build.
- **Pipeline controllata** — `ruff` e 18 test unitari su ogni pull request.

## Dispositivi supportati

| Dispositivo | Target | Immagini |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI e BIOS legacy |

I tag di release sono il nome del dispositivo (`ruijie_rg-x60-new`, `x86_64`). Ogni
dispositivo mantiene la propria release, così indice e pagina di download li elencano
affiancati.

## Download

- **Pagina di download** — <https://ota.kejizero.xyz/> mostra build corrente, changelog e SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> ospita immagini e `SHA256SUMS`.
- **Sul dispositivo** — *Sistema → Aggiornamento online* fa lo stesso senza scaricare nel browser.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flash

**A. Da OpenWrt o ImmortalWrt**
*Sistema → Backup / Flash firmware*, carica il `-squashfs-sysupgrade.bin` e non conservare
la configurazione quando cambi versione maggiore.

**B. Dal firmware di fabbrica**
Installa prima il recovery del bootloader (la pagina web U-Boot tipica di questa scheda), poi
carica lì la stessa immagine. Non flashare dalla interfaccia di fabbrica.

**C. Recupero**
Avvia il `-initramfs-kernel.bin` dal bootloader per avere un sistema temporaneo, poi scrivi
l'immagine sysupgrade da lì.

Indirizzo predefinito `10.0.0.1`, utente `root`, password `password`. Cambiali al primo accesso.

## Aggiornamento online

Il firmware include `luci-app-ota`:

- l'indice predefinito è `https://ota.kejizero.xyz/ota.json` e si cambia in *Sistema → Aggiornamento online → Configurazione*;
- lo SHA256 è obbligatorio: una voce senza hash viene rifiutata e una mancata corrispondenza cancella il download;
- l'`http` in chiaro è rifiutato finché non abiliti *consenti connessioni non sicure*;
- la chiave del dispositivo viene ricavata da `/etc/ota/build.json`, dal model del device tree, da `board_name` e dall'architettura, accettando entrambe le grafie (`vendor,device` e `vendor_device`).

## Compilazione

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Anche un push su `main` compila. Segreti, input, ccache e ogni passo sono in
[docs/BUILD.md](../BUILD.md).

## FAQ

**Dove è il codice?** L'albero LEDE è privato. Questo repository contiene pipeline, asset di branding e test.

**Perché non c'è un'immagine `factory`?** Queste schede si flashano dalla pagina di recovery del bootloader, che accetta direttamente l'immagine sysupgrade.

**Posso usare il mio indice?** Sì: punta `api_url` a un JSON compatibile e ospitalo dove vuoi.

## Avvertenza

Flasherare può rendere inutilizzabile il dispositivo. Salva il firmware di fabbrica e la tua
configurazione e comprendi il percorso di ripristino prima di iniziare. Il firmware è fornito
così com'è, senza garanzie.

---

Note per i manutentori: [docs/BUILD.md](../BUILD.md) · Altre lingue: [docs/readme](.)
