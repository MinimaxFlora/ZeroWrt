<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · **Français** · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware personnalisé basé sur LEDE, avec mise à jour en ligne en un clic.

**Une commande le construit, un clic le met à jour.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Noyau](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Cible](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Page de téléchargement](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Journaux de build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Système → Mise à jour en ligne → Rechercher des mises à jour</code>

</div>

> [!IMPORTANT]
> **Uniquement les sources officielles.** Le firmware n'est publié que dans les
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) de ce dépôt et sur
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). Un nom de dépôt similaire ou un
> README copié ne rend pas une compilation officielle.

---

ZeroWrt est un firmware personnalisé pour routeurs de la famille OpenWrt, compilé depuis
un arbre LEDE privé via GitHub Actions. Chaque build est produit depuis les sources,
publié avec `SHA256SUMS` et `BUILD_INFO.txt`, et inscrit dans un index de mise à jour afin
que l'appareil puisse se mettre à jour depuis LuCI.

L'intérêt n'est pas une liste de paquets supplémentaire, mais la boucle : le build publie l'image et l'index, et le routeur voit la nouvelle
version au contrôle suivant.

## Fonctionnalités

- **Mise à jour en un clic** — LuCI lit l'index, télécharge avec reprise et progression, vérifie le SHA256 et l'image avec `sysupgrade -T`, puis flashe et redémarre.
- **Comparaison honnête des versions** — l'horodatage de build décide, sinon la chaîne de version ; une date inconnue est affichée comme inconnue, sans invention.
- **Configuration depuis le workflow** — IP du LAN, nom d'hôte et trois SSID/mots de passe Wi-Fi sont des entrées de build, pas des fichiers édités à la main.
- **Image de marque Argon 3** — fond, logo de connexion, favicon et palette (`#2E9D72` / `#4CAF86`) remplacés à la compilation.
- **Pile proxy incluse** — PassWall (Xray uniquement) et OpenClash, synchronisés par les scripts de build.
- **Pipeline contrôlé** — `ruff` et 18 tests unitaires à chaque pull request.

## Appareils pris en charge

| Appareil | Cible | Images |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI et BIOS hérité |

Les tags de release sont le nom de l'appareil (`ruijie_rg-x60-new`, `x86_64`). Chaque
appareil garde sa propre release, l'index et la page de téléchargement peuvent donc les
afficher côte à côte.

## Téléchargement

- **Page de téléchargement** — <https://ota.kejizero.xyz/> affiche le build courant, le changelog et le SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> héberge les images et `SHA256SUMS`.
- **Sur l'appareil** — *Système → Mise à jour en ligne* fait la même chose sans téléchargement navigateur.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flashage

**A. Depuis OpenWrt ou ImmortalWrt**
*Système → Sauvegarde / Flasher le firmware*, envoyez le `-squashfs-sysupgrade.bin` et ne
conservez pas la configuration lors d'un changement de version majeure.

**B. Depuis le firmware d'origine**
Installez d'abord la récupération du chargeur d'amorçage (la page web U-Boot habituelle sur
cette carte), puis envoyez-y la même image. Ne flashez pas depuis l'interface d'origine.

**C. Récupération**
Démarrez le `-initramfs-kernel.bin` depuis le chargeur pour obtenir un système temporaire,
puis flashez l'image sysupgrade depuis celui-ci.

Adresse par défaut `10.0.0.1`, utilisateur `root`, mot de passe `password`. À changer dès la première connexion.

## Mise à jour en ligne

`luci-app-ota` est inclus :

- l'index vaut par défaut `https://ota.kejizero.xyz/ota.json` et se change dans *Système → Mise à jour en ligne → Configuration* ;
- le SHA256 est obligatoire : une entrée sans empreinte est refusée, et une empreinte incorrecte supprime le téléchargement ;
- le `http` en clair est refusé sauf si *autoriser les connexions non sécurisées* est activé ;
- la clé de l'appareil est résolue depuis `/etc/ota/build.json`, le modèle de l'arbre de périphériques, `board_name` puis l'architecture, et les deux écritures (`vendor,device` et `vendor_device`) sont acceptées.

## Compilation

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Les builds se lancent à la main : *Actions → Build ZeroWrt → Run workflow*. Il n'y a pas de déclencheur `push`, fusionner du code ne lance donc pas six heures de compilation. Secrets, entrées, ccache et chaque étape sont décrits dans [docs/BUILD.md](../BUILD.md).

## FAQ

**Où est le code source ?** L'arbre LEDE est privé. Ce dépôt contient le pipeline, les ressources de marque et les tests.

**Pourquoi pas d'image `factory` ?** Ces cartes se flashent via la page de récupération du chargeur, qui accepte directement l'image sysupgrade.

**Puis-je utiliser mon propre index ?** Oui : pointez `api_url` vers un JSON compatible et hébergez-le où vous voulez.

## Remerciements

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Licence

Les scripts, les ressources de marque et la documentation de ce dépôt sont publiés sous **GPL-2.0** — voir [LICENSE](../../LICENSE).

Le firmware embarque OpenWrt, LEDE et de nombreux composants amont, chacun sous sa propre licence. Redistribuer une image implique de respecter ces licences ; la GPL-2.0 exige notamment de fournir le code source correspondant.

## Avertissement

Le flashage peut rendre un appareil inutilisable. Sauvegardez le firmware d'origine et votre
configuration, et comprenez la procédure de récupération avant de commencer. Le firmware est
fourni tel quel, sans garantie.

---

Notes pour les mainteneurs : [docs/BUILD.md](../BUILD.md) · Autres langues : [docs/readme](.)
