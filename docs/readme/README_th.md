<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · **ไทย** · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### เฟิร์มแวร์กำหนดเองบนฐาน LEDE อัปเดตออนไลน์ได้ในคลิกเดียว

**พุชคอมมิตแล้วได้เฟิร์มแวร์ เปิด LuCI แล้วกดอัปเดต**

[![บิลด์](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![เคอร์เนล](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![แพลตฟอร์ม](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[หน้าดาวน์โหลด](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [บันทึกการบิลด์](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>ระบบ → อัปเกรดออนไลน์ → ตรวจหาการอัปเดต</code>

</div>

> [!IMPORTANT]
> **ดาวน์โหลดจากแหล่งทางการเท่านั้น** เฟิร์มแวร์เผยแพร่เฉพาะใน
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) ของรีโปนี้ และที่
> [ota.kejizero.xyz](https://ota.kejizero.xyz/) ชื่อรีโปที่คล้ายกันหรือ README ที่ถูกคัดลอก
> ไม่ได้ทำให้บิลด์นั้นเป็นทางการ

---

ZeroWrt คือเฟิร์มแวร์กำหนดเองขนาดเล็กสำหรับเราเตอร์ตระกูล OpenWrt บิลด์จากต้นไม้ LEDE
ส่วนตัวผ่าน GitHub Actions ทุกบิลด์สร้างจากซอร์สโค้ด เผยแพร่พร้อม `SHA256SUMS` และ
`BUILD_INFO.txt` และถูกบันทึกในดัชนีอัปเดต อุปกรณ์จึงอัปเกรดตัวเองได้จาก LuCI

จุดที่น่าสนใจไม่ใช่รายการแพ็กเกจอีกชุด แต่เป็นวงจรนี้: คอมมิตเริ่มบิลด์ บิลด์เผยแพร่ image
และดัชนี แล้วเราเตอร์เห็นเวอร์ชันใหม่ในการตรวจครั้งถัดไป

## คุณสมบัติ

- **อัปเดตในคลิกเดียว** — LuCI อ่านดัชนี ดาวน์โหลดแบบต่อเนื่องพร้อมแถบความคืบหน้า ตรวจ SHA256 และตรวจ image ด้วย `sysupgrade -T` แล้วเขียนและรีบูต
- **ตัดสินเวอร์ชันอย่างซื่อตรง** — ใช้เวลาบิลด์ตัดสินว่าใหม่กว่า ถ้าไม่มีจึงเทียบสตริงเวอร์ชัน และวันที่ที่ไม่ทราบจะแสดงว่าไม่ทราบ ไม่แต่งขึ้นมา
- **กำหนดค่าจาก workflow** — IP ของ LAN ชื่อโฮสต์ และ SSID/รหัสผ่าน Wi-Fi สามชุดเป็นพารามิเตอร์บิลด์ ไม่ใช่ไฟล์ที่แก้มือ
- **แบรนด์ Argon 3** — พื้นหลัง โลโก้หน้าเข้าสู่ระบบ favicon และชุดสี (`#2E9D72` / `#4CAF86`) ถูกแทนตอนบิลด์
- **มาพร้อมพร็อกซี** — PassWall (เฉพาะ Xray) และ OpenClash ซิงก์โดยสคริปต์บิลด์
- **ไปป์ไลน์มีด่านตรวจ** — `ruff` และยูนิตเทสต์ 18 ตัวในทุก pull request

## อุปกรณ์ที่รองรับ

| อุปกรณ์ | แพลตฟอร์ม | อิมเมจ |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI และ BIOS แบบเก่า |

แท็ก release คือชื่ออุปกรณ์ (`ruijie_rg-x60-new`, `x86_64`) อุปกรณ์แต่ละตัวมี release ของ
ตัวเอง ดัชนีและหน้าดาวน์โหลดจึงแสดงร่วมกันได้

## ดาวน์โหลด

- **หน้าดาวน์โหลด** — <https://ota.kejizero.xyz/> แสดงบิลด์ปัจจุบัน changelog และ SHA256
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> เก็บอิมเมจและ `SHA256SUMS`
- **บนตัวเครื่อง** — *ระบบ → อัปเกรดออนไลน์* ทำแบบเดียวกันโดยไม่ต้องดาวน์โหลดในเบราว์เซอร์

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## การแฟลช

**A. จาก OpenWrt หรือ ImmortalWrt**
*ระบบ → สำรองข้อมูล / แฟลชเฟิร์มแวร์* อัปโหลด `-squashfs-sysupgrade.bin` และอย่าเก็บ
ค่าคอนฟิกเมื่อข้ามเวอร์ชันหลัก

**B. จากเฟิร์มแวร์จากโรงงาน**
ติดตั้งหน้าผู้ช่วยกู้คืนของ bootloader ก่อน (บอร์ดนี้มักเป็นหน้าเว็บ U-Boot) แล้วอัปโหลด
อิมเมจเดียวกันที่นั่น อย่าแฟลชจากหน้าเว็บของผู้ผลิต

**C. กู้เครื่อง**
บูต `-initramfs-kernel.bin` จาก bootloader เพื่อได้ระบบชั่วคราว แล้วแฟลชอิมเมจ sysupgrade
จากในนั้น

ที่อยู่เริ่มต้น `10.0.0.1` ผู้ใช้ `root` รหัสผ่าน `password` ควรเปลี่ยนทันทีที่เข้าครั้งแรก

## อัปเกรดออนไลน์

เฟิร์มแวร์มี `luci-app-ota` มาด้วย:

- ดัชนีเริ่มต้นคือ `https://ota.kejizero.xyz/ota.json` เปลี่ยนได้ที่ *ระบบ → อัปเกรดออนไลน์ → ตั้งค่า*
- SHA256 จำเป็น: รายการที่ไม่มีจะถูกปฏิเสธ และถ้าไม่ตรงจะลบไฟล์ที่ดาวน์โหลด
- `http` แบบไม่เข้ารหัสจะถูกปฏิเสธ เว้นแต่เปิด *อนุญาตการเชื่อมต่อที่ไม่ปลอดภัย*
- คีย์อุปกรณ์หาได้จาก `/etc/ota/build.json`, model ใน device tree, `board_name` และสถาปัตยกรรม ตามลำดับ และรับทั้ง `vendor,device` กับ `vendor_device`

## การบิลด์

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

พุชขึ้น `main` ก็บิลด์เช่นกัน Secrets พารามิเตอร์ ccache และทุกขั้นตอนอยู่ใน
[docs/BUILD.md](../BUILD.md)

## คำถามที่พบบ่อย

**ซอร์สอยู่ที่ไหน?** ต้นไม้ LEDE เป็นส่วนตัว รีโปนี้เก็บไปป์ไลน์ วัสดุแบรนด์ และเทสต์

**ทำไมไม่มีอิมเมจ `factory`?** บอร์ดเหล่านี้แฟลชผ่านหน้าผู้ช่วยกู้คืนของ bootloader ซึ่งรับอิมเมจ sysupgrade ได้โดยตรง

**ใช้ดัชนีของตัวเองได้ไหม?** ได้ ตั้ง `api_url` ไปที่ JSON ที่เข้ากันได้ แล้วโฮสต์ที่ไหนก็ได้

## กิตติกรรมประกาศ

- **[OpenWrt](https://github.com/openwrt/openwrt)** — ระบบบิลด์ LuCI และแพ็กเกจพื้นฐานส่วนใหญ่ ทุกอย่างที่นี่ตั้งอยู่บนนั้น
- **[LEDE](https://github.com/coolsnowwolf/lede)** — ซอร์สทรีและค่าตั้งต้นที่ ZeroWrt สร้างต่อ
- **[Yuzhii0718](https://github.com/Yuzhii0718)** — การพอร์ต Ruijie RG-X60 New ไปยัง MT7986 (immortalwrt-mt798x)

และผู้เขียนแพ็กเกจต้นทางจำนวนมากที่ไม่ได้ระบุชื่อที่นี่ โค้ดของพวกเขาทำงานในทุกบิลด์

## สัญญาอนุญาต

สคริปต์ วัสดุแบรนด์ และเอกสารในรีโปนี้เผยแพร่ภายใต้ **GPL-2.0** ดู [LICENSE](../../LICENSE)

ตัวเฟิร์มแวร์มี OpenWrt, LEDE และคอมโพเนนต์ต้นทางอื่น ๆ ซึ่งแต่ละตัวมีสัญญาอนุญาตของตัวเอง การเผยแพร่อิมเมจต่อก็ต้องปฏิบัติตามสัญญาเหล่านั้นด้วย และ GPL-2.0 กำหนดให้ต้องเปิดซอร์สที่เกี่ยวข้อง

## ข้อจำกัดความรับผิด

การแฟลชอาจทำให้เครื่องใช้ไม่ได้ สำรองเฟิร์มแวร์จากโรงงานและค่าคอนฟิกของคุณ และทำความเข้าใจ
เส้นทางกู้คืนก่อนเริ่ม เฟิร์มแวร์ให้ตามสภาพ ไม่มีการรับประกัน

---

สำหรับผู้ดูแล: [docs/BUILD.md](../BUILD.md) · ภาษาอื่น: [docs/readme](.)
