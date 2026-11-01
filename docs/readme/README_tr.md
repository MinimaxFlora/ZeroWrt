<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · **Türkçe** · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### ImmortalWrt / LEDE tabanlı özel yazılım, web arayüzünden tek tıkla güncelleme.

**Tek komut derler, tek tık günceller.**

[![Derleme](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Çekirdek](https://img.shields.io/badge/kernel-6.6%20%2F%206.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Hedef](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[İndirme sayfası](https://ota.tatalvpai.vip/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Derleme kayıtları](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Sistem → Çevrimiçi güncelleme → Güncellemeleri denetle</code>

</div>

> [!IMPORTANT]
> **Yalnızca resmî kaynaklar.** Yazılım sadece bu deponun
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) bölümünde ve
> [ota.tatalvpai.vip](https://ota.tatalvpai.vip/) adresinde yayınlanır. Benzer bir depo
> adı veya kopyalanmış README, bir derlemeyi resmî yapmaz.

---

ZeroWrt, OpenWrt sınıfı yönlendiriciler için küçük bir özel yazılımdır ve GitHub Actions ile
iki genel ağaçtan derlenir: MT7986 kartı için [ImmortalWrt
24.10](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly), x86_64 için
[LEDE](https://github.com/coolsnowwolf/lede). Her derleme kaynaktan üretilir, `SHA256SUMS` ve
`BUILD_INFO.txt` ile yayınlanır ve güncelleme dizinine yazılır; böylece cihaz kendini
LuCI'den güncelleyebilir.

İlginç olan başka bir paket listesi değil, döngü: derleme
imajı ve dizini yayınlar, yönlendirici bir sonraki denetimde yeni sürümü görür.

## Özellikler

- **Tek tıkla güncelleme** — LuCI dizini okur, devam ettirme ve ilerleme ile indirir, SHA256 ve imajı `sysupgrade -T` ile doğrular, sonra yazıp yeniden başlatır.
- **Dürüst sürüm karşılaştırması** — "daha yeni" kararını derleme zaman damgası verir, yoksa sürüm dizesi karşılaştırılır; bilinmeyen tarih uydurulmaz, bilinmiyor olarak gösterilir.
- **Yapılandırma workflow'dan** — LAN IP'si, ana makine adı ve üç Wi-Fi SSID/parolası derleme girdisidir, elle düzenlenen dosyalar değildir.
- **Argon 3 markası** — arka plan, giriş logosu, favicon ve palet (`#2E9D72` / `#4CAF86`) derleme sırasında değiştirilir.
- **Proxy yığını dahil** — PassWall (sing-box çekirdeği, Xray ve SmartDNS yok) ve OpenClash, derleme betikleriyle eşitlenir.
- **Kontrollü hat** — her pull request'te `ruff` ve 44 birim testi çalışır.

## Desteklenen cihazlar

| Cihaz | Kaynak | Düzen | İmajlar |
| --- | --- | --- | --- |
| Ruijie RG-X60 New | ImmortalWrt 24.10 (`openwrt-24.10-6.6`) | OpenWrt U-Boot (ubootmod) | `-squashfs-sysupgrade.itb`, `preloader.bin`, `bl31-uboot.fip` |
| x86_64 | LEDE (`master`) | EFI ve eski BIOS | `-squashfs-combined*.img.gz`, `-generic-ext4-combined*.img.gz` |

> **LEDE derlemelerinden geçiş:** RG-X60 New imajı fabrika bölümlemesinden **ubootmod**'a
> geçti. U-Boot kurtarma sayfasından yaz ve yapılandırmayı koruma; eski imaj ile bu imaj
> birbirinin yerine geçmez.

Release etiketleri cihaz adıdır (`ruijie_rg-x60-new`, `x86_64`). Her cihaz kendi release'ini
korur; dizin ve indirme sayfası ikisini yan yana listeleyebilir.

## İndirme

- **İndirme sayfası** — <https://ota.tatalvpai.vip/> güncel derlemeyi, değişiklik günlüğünü ve SHA256'yı gösterir.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> imajları ve `SHA256SUMS` dosyasını barındırır.
- **Cihaz üzerinde** — *Sistem → Çevrimiçi güncelleme* tarayıcıdan indirmeden aynısını yapar.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-squashfs-sysupgrade.itb
```

## Yükleme

**A. OpenWrt veya ImmortalWrt üzerinden**
*Sistem → Yedek / Yazılım yükle*, `-squashfs-sysupgrade.itb` dosyasını yükle ve ana sürüm
atlıyorsan yapılandırmayı koruma.

**B. Üretici yazılımından**
Önce önyükleyici kurtarma sayfasını kur (bu kartta genellikle U-Boot web sayfası), sonra aynı
imajı oradan yükle. Üretici arayüzünden doğrudan yazma.

**C. Kurtarma**
Önyükleyiciden `-initramfs-recovery.itb` başlatıp geçici bir sistem al, sonra sysupgrade imajını
oradan yaz.

Varsayılan adres `10.0.0.1`, kullanıcı `root`, parola `password`. İlk girişte değiştir.

## Çevrimiçi güncelleme

Yazılımda `luci-app-ota` var:

- dizin varsayılan olarak `https://ota.tatalvpai.vip/ota.json` ve *Sistem → Çevrimiçi güncelleme → Yapılandırma* altında değiştirilir;
- SHA256 zorunludur: olmayan kayıt reddedilir, uyuşmazsa indirme silinir;
- *güvenli olmayan bağlantılara izin ver* açık değilse düz `http` reddedilir;
- cihaz anahtarı `/etc/ota/build.json`, cihaz ağacı modeli, `board_name` ve mimari sırasıyla bulunur; `vendor,device` ve `vendor_device` yazımlarının ikisi de kabul edilir.

## Derleme

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Derlemeler elle başlatılır: *Actions → Build ZeroWrt → Run workflow*. `push` tetikleyicisi yok, bu yüzden kod birleştirmek altı saatlik derlemeyi başlatmaz. Sırlar, girdiler, ccache ve her adım [docs/BUILD.md](../BUILD.md) içinde.

## SSS

**Kaynak nerede?** RG-X60 New [Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly) deposundan, x86_64 ise [coolsnowwolf/lede](https://github.com/coolsnowwolf/lede) deposundan derlenir. Bu depoda hat, marka varlıkları ve testler var.

**Neden `factory` imajı yok?** Bu kartlar önyükleyicinin web kurtarma sayfasından yüklenir ve o sayfa sysupgrade imajını doğrudan kabul eder.

**Kendi dizinimi kullanabilir miyim?** Evet — `api_url` değerini uyumlu bir JSON'a yönlendir ve istediğin yerde barındır.

## Teşekkürler

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Lisans

Bu depodaki betikler, marka varlıkları ve belgeler **GPL-2.0** ile yayımlanır — bkz. [LICENSE](../../LICENSE).

Yazılımın kendisi OpenWrt, LEDE ve daha birçok üst kaynak bileşeni içerir; her biri kendi lisansına tabidir. Bir imajı yeniden dağıtırken bu lisanslar da geçerlidir; GPL-2.0 özellikle ilgili kaynak kodun sunulmasını şart koşar.

## Yasal uyarı

Yazılım yüklemek cihazı tuğlaya çevirebilir. Üretici yazılımını ve yapılandırmanı yedekle,
kurtarma yolunu önceden öğren. Yazılım olduğu gibi, garantisiz sunulur.

---

Bakımcılar için: [docs/BUILD.md](../BUILD.md) · Diğer diller: [docs/readme](.)
