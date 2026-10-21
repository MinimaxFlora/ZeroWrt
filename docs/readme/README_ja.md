<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · **日本語** · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### LEDE ベースのカスタムファームウェア。LuCI からワンクリック更新。

**コミットすればビルドされ、LuCI を開いて更新を押すだけ。**

[![ビルド](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![カーネル](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![ターゲット](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[ダウンロードページ](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [ビルドログ](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>システム → オンラインアップグレード → 更新を確認</code>

</div>

> [!IMPORTANT]
> **公式の配布元からのみ入手してください。** ファームウェアはこのリポジトリの
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) と
> [ota.kejizero.xyz](https://ota.kejizero.xyz/) でのみ公開しています。
> よく似たリポジトリ名や README のコピーは、公式ビルドであることの証明になりません。

---

ZeroWrt は OpenWrt 系ルーター向けの小さなカスタムファームウェアです。プライベートな
LEDE ツリーから GitHub Actions でビルドしています。すべてのビルドはソースから生成され、
`SHA256SUMS` と `BUILD_INFO.txt` を添えて公開され、更新インデックスに登録されるため、
端末は LuCI から自分でアップグレードできます。

面白いのはパッケージ一覧の長さではなく、このループです。コミットがビルドを起こし、
ビルドがイメージとインデックスを公開し、次回の確認時にルーターが新しい版を見つけます。

## 特長

- **ワンクリック更新** — LuCI がインデックスを読み、レジュームと進捗表示つきでダウンロードし、SHA256 と `sysupgrade -T` で検証してから書き込み・再起動します。
- **誠実なバージョン判定** — ビルド時刻で新旧を判断し、無い場合だけバージョン文字列で比較します。判定できない日付は「不明」と表示し、捏造しません。
- **設定はワークフローから注入** — LAN IP、ホスト名、3 つの Wi-Fi SSID とパスワードはビルド入力で、手編集のファイルではありません。
- **Argon 3 のブランディング** — 背景、ログインロゴ、favicon、配色（`#2E9D72` / `#4CAF86`）をビルド時に差し替えます。
- **プロキシ一式を同梱** — PassWall（Xray のみ）と OpenClash をビルドスクリプトが同期します。
- **関門のあるパイプライン** — すべての PR で `ruff` と 18 個のユニットテストを実行します。

## 対応デバイス

| デバイス | ターゲット | イメージ |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`、`-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI とレガシー BIOS |

Release のタグはデバイス名（`ruijie_rg-x60-new`、`x86_64`）です。デバイスごとに
release を分けているので、インデックスとダウンロードページに並べて表示できます。

## ダウンロード

- **ダウンロードページ** — <https://ota.kejizero.xyz/> に現在のビルド、変更履歴、SHA256 があります。
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> にイメージと `SHA256SUMS` があります。
- **端末上で** — *システム → オンラインアップグレード* から、ブラウザでダウンロードせずに更新できます。

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## 書き込み

**A. OpenWrt / ImmortalWrt から**
*システム → バックアップ/ファームウェア書き込み* で `-squashfs-sysupgrade.bin` を
アップロードします。メジャーバージョンをまたぐときは設定を引き継がないでください。

**B. 純正ファームウェアから**
先にブートローダーのリカバリ（この基板では通常 U-Boot の Web ページ）を導入し、
そこで同じイメージを書き込みます。純正の管理画面から直接書き込まないでください。

**C. 復旧**
ブートローダーから `-initramfs-kernel.bin` を起動して一時システムを立て、そこから
sysupgrade イメージを書き込みます。

既定のアドレスは `10.0.0.1`、ユーザー `root`、パスワード `password`。初回ログインで変更してください。

## オンラインアップグレード

`luci-app-ota` を同梱しています。

- インデックスの既定値は `https://ota.kejizero.xyz/ota.json`。*システム → オンラインアップグレード → 設定* で変更できます。
- SHA256 は必須です。無い項目は拒否し、不一致ならダウンロードを削除します。
- 平文 `http` は「安全でない接続を許可」を有効にしない限り拒否します。
- デバイスキーは `/etc/ota/build.json`、デバイスツリーの model、`board_name`、アーキテクチャの順に解決し、`vendor,device` と `vendor_device` の両方の表記を受け付けます。

## ビルド

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

`main` へのプッシュでもビルドされます。Secrets、入力、ccache、各ステップの内容は
[docs/BUILD.md](../BUILD.md) にまとめています。

## FAQ

**ソースはどこに？** LEDE ツリーは非公開です。このリポジトリにはパイプライン、ブランド素材、テストがあります。

**`factory` イメージが無いのはなぜ？** この基板はブートローダーの Web リカバリから書き込む前提で、そこに sysupgrade イメージをそのまま渡せます。

**自分のインデックスは使えますか？** 使えます。`api_url` を互換 JSON に向けて、好きな場所でホストしてください。

## 謝辞

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## ライセンス

このリポジトリのスクリプト、ブランド素材、ドキュメントは **GPL-2.0** で公開しています（[LICENSE](../../LICENSE)）。

ファームウェア本体は OpenWrt、LEDE、その他多数の上流コンポーネントを含み、それぞれのライセンスに従います。イメージを再配布する場合も同じで、GPL-2.0 では対応するソースの提供が求められます。

## 免責事項

書き込みには文鎮化の危険があります。純正ファームウェアと設定をバックアップし、復旧手順を
確認してから作業してください。本ファームウェアは現状のまま提供され、保証はありません。

---

メンテナ向け: [docs/BUILD.md](../BUILD.md) · 他の言語: [docs/readme](.)
