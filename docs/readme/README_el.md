<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · **Ελληνικά** · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Προσαρμοσμένο firmware βασισμένο στο LEDE, με ενημέρωση online με ένα κλικ.

**Μία εντολή το χτίζει, ένα κλικ το ενημερώνει.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Πυρήνας](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Πλατφόρμα](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Σελίδα λήψης](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Αρχεία build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Σύστημα → Ενημέρωση online → Έλεγχος για ενημερώσεις</code>

</div>

> [!IMPORTANT]
> **Μόνο από επίσημες πηγές.** Το firmware δημοσιεύεται αποκλειστικά στα
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) αυτού του αποθετηρίου και
> στο [ota.kejizero.xyz](https://ota.kejizero.xyz/). Παρόμοιο όνομα αποθετηρίου ή
> αντιγραμμένο README δεν κάνει ένα build επίσημο.

---

Το ZeroWrt είναι ένα μικρό προσαρμοσμένο firmware για ρούτερ κλάσης OpenWrt, χτισμένο από
ένα ιδιωτικό δέντρο LEDE μέσω GitHub Actions. Κάθε build παράγεται από τον πηγαίο κώδικα,
δημοσιεύεται μαζί με `SHA256SUMS` και `BUILD_INFO.txt` και καταχωρείται σε ευρετήριο
ενημερώσεων, ώστε η συσκευή να ενημερώνεται μόνη της από το LuCI.

Το ενδιαφέρον δεν είναι άλλη μια λίστα πακέτων, αλλά ο κύκλος: το
build δημοσιεύει image και ευρετήριο, και το ρούτερ βλέπει τη νέα έκδοση στον επόμενο έλεγχο.

## Χαρακτηριστικά

- **Ενημέρωση με ένα κλικ** — το LuCI διαβάζει το ευρετήριο, κατεβάζει με συνέχιση και πρόοδο, επαληθεύει SHA256 και image με `sysupgrade -T` και μετά γράφει και επανεκκινεί.
- **Έντιμη σύγκριση εκδόσεων** — η χρονική σήμανση του build κρίνει το «νεότερο», αλλιώς συγκρίνονται συμβολοσειρές έκδοσης· άγνωστη ημερομηνία εμφανίζεται ως άγνωστη, δεν επινοείται.
- **Ρυθμίσεις από το workflow** — διεύθυνση LAN, hostname και τρία SSID/κωδικοί Wi-Fi είναι είσοδοι build, όχι αρχεία με χειροκίνητες αλλαγές.
- **Branding Argon 3** — φόντο, λογότυπο σύνδεσης, favicon και παλέτα (`#2E9D72` / `#4CAF86`) αντικαθίστανται κατά το build.
- **Πλήρες proxy stack** — PassWall (μόνο Xray) και OpenClash, συγχρονισμένα από τα scripts build.
- **Ελεγχόμενη ροή** — `ruff` και 18 unit tests σε κάθε pull request.

## Υποστηριζόμενες συσκευές

| Συσκευή | Πλατφόρμα | Images |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI και παλαιό BIOS |

Τα tags των release είναι το όνομα της συσκευής (`ruijie_rg-x60-new`, `x86_64`). Κάθε
συσκευή κρατά δικό της release, οπότε το ευρετήριο και η σελίδα λήψης τα δείχνουν δίπλα δίπλα.

## Λήψη

- **Σελίδα λήψης** — <https://ota.kejizero.xyz/> δείχνει το τρέχον build, το changelog και το SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> φιλοξενεί τα images και το `SHA256SUMS`.
- **Στη συσκευή** — *Σύστημα → Ενημέρωση online* κάνει το ίδιο χωρίς λήψη από τον browser.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Εγκατάσταση

**Α. Από OpenWrt ή ImmortalWrt**
*Σύστημα → Αντίγραφο ασφαλείας / Εγκατάσταση firmware*, ανέβασε το
`-squashfs-sysupgrade.bin` και μη διατηρήσεις τις ρυθμίσεις όταν αλλάζεις κύρια έκδοση.

**Β. Από το firmware του κατασκευαστή**
Εγκατέστησε πρώτα τη σελίδα ανάκτησης του bootloader (συνήθως η web σελίδα U-Boot σε αυτή
την πλακέτα) και ανέβασε εκεί το ίδιο image. Μην κάνεις flash από το περιβάλλον του κατασκευαστή.

**Γ. Ανάκτηση**
Εκκίνησε το `-initramfs-kernel.bin` από τον bootloader για προσωρινό σύστημα και γράψε από
εκεί το image sysupgrade.

Προεπιλεγμένη διεύθυνση `10.0.0.1`, χρήστης `root`, κωδικός `password`. Άλλαξέ τα στην πρώτη σύνδεση.

## Ενημέρωση online

Το firmware περιλαμβάνει το `luci-app-ota`:

- το ευρετήριο είναι εξ ορισμού `https://ota.kejizero.xyz/ota.json` και αλλάζει από *Σύστημα → Ενημέρωση online → Ρυθμίσεις*·
- το SHA256 είναι υποχρεωτικό: καταχώρηση χωρίς αυτό απορρίπτεται και, αν δεν ταιριάζει, η λήψη διαγράφεται·
- το απλό `http` απορρίπτεται εκτός αν ενεργοποιηθεί το *να επιτρέπονται μη ασφαλείς συνδέσεις*·
- το κλειδί συσκευής προκύπτει από `/etc/ota/build.json`, το model του device tree, το `board_name` και την αρχιτεκτονική, και γίνονται δεκτές και οι δύο γραφές (`vendor,device` και `vendor_device`).

## Κατασκευή

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Τα builds ξεκινούν χειροκίνητα από *Actions → Build ZeroWrt → Run workflow*. Δεν υπάρχει trigger `push`, οπότε ένα merge δεν ξεκινά εξάωρη μεταγλώττιση. Secrets, είσοδοι, ccache και κάθε βήμα βρίσκονται στο [docs/BUILD.md](../BUILD.md).

## Συχνές ερωτήσεις

**Πού είναι ο κώδικας;** Το δέντρο LEDE είναι ιδιωτικό. Αυτό το αποθετήριο έχει τη ροή, τα υλικά branding και τα tests.

**Γιατί δεν υπάρχει image `factory`;** Αυτές οι πλακέτες κάνουν flash από τη σελίδα ανάκτησης του bootloader, που δέχεται απευθείας το image sysupgrade.

**Μπορώ να χρησιμοποιήσω δικό μου ευρετήριο;** Ναι — όρισε το `api_url` σε ένα συμβατό JSON και φιλοξένησέ το όπου θέλεις.

## Ευχαριστίες

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Άδεια

Τα scripts, τα υλικά branding και η τεκμηρίωση αυτού του αποθετηρίου διανέμονται με **GPL-2.0** — βλ. [LICENSE](../../LICENSE).

Το ίδιο το firmware περιλαμβάνει OpenWrt, LEDE και πολλά άλλα upstream στοιχεία, καθένα με τη δική του άδεια. Κατά την αναδιανομή ενός image ισχύουν κι αυτές· η GPL-2.0 ειδικότερα απαιτεί τη διάθεση του αντίστοιχου πηγαίου κώδικα.

## Αποποίηση ευθυνών

Το flashing μπορεί να αχρηστεύσει τη συσκευή. Πάρε αντίγραφο του firmware του κατασκευαστή και
των ρυθμίσεών σου και κατανόησε τη διαδικασία ανάκτησης πριν ξεκινήσεις. Το firmware
παρέχεται ως έχει, χωρίς εγγύηση.

---

Για συντηρητές: [docs/BUILD.md](../BUILD.md) · Άλλες γλώσσες: [docs/readme](.)
