<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · **Bahasa Indonesia** · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware kustom berbasis LEDE, dengan pembaruan online sekali klik.

**Push commit, dapatkan firmware. Buka LuCI, klik perbarui.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Target](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)

[Halaman unduhan](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Log build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Sistem → Pembaruan online → Periksa pembaruan</code>

</div>

> [!IMPORTANT]
> **Hanya sumber resmi.** Firmware hanya diterbitkan di
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) repositori ini dan di
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). Nama repositori yang mirip atau
> README hasil salinan tidak membuat sebuah build menjadi resmi.

---

ZeroWrt adalah firmware kustom kecil untuk router kelas OpenWrt, dibangun dari pohon LEDE
privat lewat GitHub Actions. Setiap build dihasilkan dari kode sumber, diterbitkan bersama
`SHA256SUMS` dan `BUILD_INFO.txt`, lalu dicatat dalam indeks pembaruan sehingga perangkat
dapat memperbarui dirinya sendiri dari LuCI.

Yang menarik bukan daftar paket lain, tetapi siklusnya: satu commit memulai build, build
menerbitkan image dan indeks, dan router melihat versi baru saat pemeriksaan berikutnya.

## Fitur

- **Pembaruan sekali klik** — LuCI membaca indeks, mengunduh dengan lanjut-otomatis dan progres, memverifikasi SHA256 serta image dengan `sysupgrade -T`, lalu menulisnya dan reboot.
- **Perbandingan versi yang jujur** — stempel waktu build menentukan "lebih baru", jika tidak ada baru membandingkan string versi; tanggal yang tidak diketahui ditampilkan sebagai tidak diketahui, bukan dikarang.
- **Konfigurasi dari workflow** — IP LAN, hostname, serta tiga SSID dan sandi Wi-Fi adalah input build, bukan berkas yang diedit manual.
- **Branding Argon 3** — latar, logo login, favicon, dan palet (`#2E9D72` / `#4CAF86`) diganti saat build.
- **Tumpukan proxy disertakan** — PassWall (hanya Xray) dan OpenClash, disinkronkan oleh skrip build.
- **Pipeline berpenjaga** — `ruff` dan 18 unit test pada setiap pull request.

## Perangkat yang didukung

| Perangkat | Target | Image |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI dan BIOS lama |

Tag release adalah nama perangkat (`ruijie_rg-x60-new`, `x86_64`). Setiap perangkat punya
release sendiri, jadi indeks dan halaman unduhan dapat menampilkannya berdampingan.

## Unduhan

- **Halaman unduhan** — <https://ota.kejizero.xyz/> menampilkan build terkini, changelog, dan SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> menyimpan image dan `SHA256SUMS`.
- **Di perangkat** — *Sistem → Pembaruan online* melakukan hal yang sama tanpa unduh di browser.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flash

**A. Dari OpenWrt atau ImmortalWrt**
*Sistem → Cadangan / Flash firmware*, unggah `-squashfs-sysupgrade.bin`, dan jangan
pertahankan konfigurasi saat berpindah versi mayor.

**B. Dari firmware pabrik**
Pasang halaman pemulihan bootloader lebih dulu (di papan ini umumnya halaman web U-Boot),
lalu unggah image yang sama di sana. Jangan flash dari antarmuka pabrik.

**C. Pemulihan**
Boot `-initramfs-kernel.bin` dari bootloader untuk mendapat sistem sementara, lalu tulis
image sysupgrade dari sana.

Alamat bawaan `10.0.0.1`, pengguna `root`, sandi `password`. Ganti saat login pertama.

## Pembaruan online

Firmware menyertakan `luci-app-ota`:

- indeks bawaan `https://ota.kejizero.xyz/ota.json` dan dapat diubah di *Sistem → Pembaruan online → Konfigurasi*;
- SHA256 wajib: entri tanpanya ditolak, dan bila tidak cocok unduhannya dihapus;
- `http` polos ditolak kecuali *izinkan koneksi tidak aman* diaktifkan;
- kunci perangkat diambil dari `/etc/ota/build.json`, model device tree, `board_name`, dan arsitektur, serta menerima kedua penulisan (`vendor,device` dan `vendor_device`).

## Build

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Push ke `main` juga memicu build. Secret, input, ccache, dan setiap langkah dijelaskan di
[docs/BUILD.md](../BUILD.md).

## FAQ

**Di mana kode sumbernya?** Pohon LEDE bersifat privat. Repositori ini berisi pipeline, aset branding, dan tes.

**Mengapa tidak ada image `factory`?** Papan ini di-flash lewat halaman pemulihan bootloader yang menerima image sysupgrade secara langsung.

**Bisakah memakai indeks sendiri?** Bisa — arahkan `api_url` ke JSON yang kompatibel dan hosting di mana saja.

## Penafian

Mem-flash firmware dapat membuat perangkat tidak bisa dipakai. Cadangkan firmware pabrik dan
konfigurasi Anda, serta pahami jalur pemulihannya sebelum mulai. Firmware disediakan apa
adanya, tanpa jaminan.

---

Catatan pemelihara: [docs/BUILD.md](../BUILD.md) · Bahasa lain: [docs/readme](.)
