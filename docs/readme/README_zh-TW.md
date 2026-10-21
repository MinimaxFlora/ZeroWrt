<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · **繁體中文** · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### 基於 LEDE 的客製韌體，內建網頁一鍵線上更新。

**一條命令出韌體，點一下完成升級。**

[![建置](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![核心](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![平台](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[下載頁](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [建置記錄](https://github.com/MinimaxFlora/ZeroWrt/actions) · [問題回報](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>系統 → 線上更新 → 檢查更新</code>

</div>

> [!IMPORTANT]
> **只從官方來源下載。** 韌體只發布在本倉庫的
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) 與
> [ota.kejizero.xyz](https://ota.kejizero.xyz/)。相似的倉庫名稱或被複製的 README
> 都不能證明那份韌體來自這裡。

---

ZeroWrt 是給 OpenWrt 類路由器的客製韌體，由 GitHub Actions 從一份私有的 LEDE
原始碼樹自動編譯。每次建置都從原始碼產出，連同 `SHA256SUMS` 與 `BUILD_INFO.txt`
一起發布，並寫入更新索引，裝置可以自己從 LuCI 升級。

有意思的不是又一份套件清單，而是這條流程：建置產出映像與索引，
路由器下次檢查時就看到新版本。

## 特色

- **網頁一鍵升級** — LuCI 讀取索引，支援續傳與進度下載，驗證 SHA256 並用 `sysupgrade -T` 預檢映像，然後寫入並重開機。
- **不馬虎的版本判斷** — 以建置時間戳判斷新舊，沒有時間戳才退回比版本號；無法確定的日期顯示為「未知」，不會憑空捏造。
- **設定由工作流程注入** — 管理 IP、主機名稱與三組 Wi-Fi 名稱/密碼都是建置參數，不是手改檔案。
- **Argon 3 品牌化** — 登入背景、登入 Logo、網站圖示與配色（`#2E9D72` / `#4CAF86`）在建置時替換。
- **內建代理套件** — PassWall（僅 Xray）與 OpenClash，由建置腳本自動同步。
- **有門檻的流程** — 每個 PR 都要通過 `ruff` 與 18 個單元測試。

## 支援的裝置

| 裝置 | 平台 | 映像 |
| --- | --- | --- |
| 銳捷 RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`、`-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI 與傳統 BIOS 兩種 |

Release 的 tag 就是裝置名稱（`ruijie_rg-x60-new`、`x86_64`）。每台裝置保留自己的
release，索引與下載頁可以並排列出。

## 下載

- **下載頁** — <https://ota.kejizero.xyz/> 顯示目前版本、更新日誌與 SHA256。
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> 存放映像與 `SHA256SUMS`。
- **在裝置上** — *系統 → 線上更新* 可直接升級，不必先在電腦下載。

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## 刷機

**A. 已經是 OpenWrt / ImmortalWrt**
*系統 → 備份/刷寫韌體*，上傳 `-squashfs-sysupgrade.bin`；跨大版本時不要保留設定。

**B. 原廠韌體**
先裝好引導的不死 U-Boot（這塊板子通常是網頁救援頁），再在那裡上傳同一個映像。
不要用原廠後台直接刷。

**C. 救磚**
從引導啟動 `-initramfs-kernel.bin` 取得臨時系統，再從裡面刷 sysupgrade 映像。

預設位址 `10.0.0.1`，使用者 `root`，密碼 `password`，第一次登入請立刻修改。

## 線上更新

韌體內建 `luci-app-ota`：

- 索引預設為 `https://ota.kejizero.xyz/ota.json`，可在 *系統 → 線上更新 → 設定* 變更；
- SHA256 為必填，沒有就拒絕下載，驗證失敗直接刪除；
- 預設拒絕明文 `http`，除非開啟「允許不安全的連線」；
- 裝置識別依序從 `/etc/ota/build.json`、裝置樹 model、`board_name` 與架構推導，並同時接受 `vendor,device` 與 `vendor_device` 兩種寫法。

## 建置

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

建置只能手動觸發：*Actions → Build ZeroWrt → Run workflow*，沒有 `push` 觸發器，合併程式碼不會順帶跑一次六小時的編譯。完整流程（Secrets、參數、ccache、每一步在做什麼）見 [docs/BUILD.md](../BUILD.md)。

## 常見問題

**原始碼在哪？** LEDE 原始碼樹是私有的。本倉庫放的是流程、品牌素材與測試。

**為什麼沒有 `factory` 映像？** 這塊板子透過引導的網頁救援頁刷機，它直接接受 sysupgrade 映像。

**能換成自己的索引嗎？** 可以，把 `api_url` 指向任何相容格式的 JSON，自己找地方託管即可。

## 鳴謝

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## 授權條款

本倉庫的腳本、品牌素材與文件以 **GPL-2.0** 發布，見 [LICENSE](../../LICENSE)。

韌體本身包含 OpenWrt、LEDE 以及大量上游元件，各自遵循原有授權。散布韌體映像時同樣要遵守這些授權；特別是 GPL-2.0 要求提供對應的原始碼。

## 免責聲明

刷機有變磚風險。動手前請備份原廠韌體與自己的設定，並先搞清楚救磚路徑。韌體按現狀
提供，不附帶任何擔保。

---

維護者文件：[docs/BUILD.md](../BUILD.md) · 其他語言：[docs/readme](.)
