<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · **한국어** · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### LEDE 기반 커스텀 펌웨어, 웹에서 원클릭 온라인 업데이트.

**커밋을 올리면 빌드되고, LuCI 를 열어 업데이트만 누르면 됩니다.**

[![빌드](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![커널](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![타깃](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[다운로드 페이지](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [빌드 로그](https://github.com/MinimaxFlora/ZeroWrt/actions) · [이슈](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>시스템 → 온라인 업그레이드 → 업데이트 확인</code>

</div>

> [!IMPORTANT]
> **공식 배포처에서만 받으세요.** 펌웨어는 이 저장소의
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) 와
> [ota.kejizero.xyz](https://ota.kejizero.xyz/) 에서만 공개됩니다.
> 비슷한 저장소 이름이나 복사된 README 는 공식 빌드라는 증거가 아닙니다.

---

ZeroWrt 는 OpenWrt 계열 공유기용 커스텀 펌웨어입니다. 비공개 LEDE 트리에서 GitHub
Actions 로 빌드하며, 모든 빌드는 소스에서 생성되어 `SHA256SUMS` 와 `BUILD_INFO.txt`
와 함께 공개되고 업데이트 인덱스에 등록되므로 기기가 LuCI 에서 직접 업그레이드할 수 있습니다.

핵심은 패키지 목록이 아니라 이 순환입니다. 커밋이 빌드를 시작하고, 빌드가 이미지와
인덱스를 공개하며, 다음 확인 때 공유기가 새 버전을 발견합니다.

## 기능

- **원클릭 업데이트** — LuCI 가 인덱스를 읽고, 이어받기와 진행률로 다운로드하며, SHA256 과 `sysupgrade -T` 로 검증한 뒤 기록하고 재부팅합니다.
- **정직한 버전 판정** — 빌드 시각으로 최신 여부를 판단하고, 없을 때만 버전 문자열을 비교합니다. 알 수 없는 날짜는 지어내지 않고 "알 수 없음"으로 표시합니다.
- **워크플로에서 설정 주입** — LAN IP, 호스트 이름, 세 개의 Wi-Fi SSID 와 비밀번호가 빌드 입력입니다.
- **Argon 3 브랜딩** — 배경, 로그인 로고, 파비콘, 색상(`#2E9D72` / `#4CAF86`)을 빌드 시 교체합니다.
- **프록시 구성 포함** — PassWall(Xray 전용)과 OpenClash 를 빌드 스크립트가 동기화합니다.
- **검증된 파이프라인** — 모든 PR 에서 `ruff` 와 18 개 단위 테스트를 실행합니다.

## 지원 기기

| 기기 | 타깃 | 이미지 |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI 및 레거시 BIOS |

Release 태그는 기기 이름입니다(`ruijie_rg-x60-new`, `x86_64`). 기기마다 release 를
따로 두므로 인덱스와 다운로드 페이지에 나란히 표시할 수 있습니다.

## 다운로드

- **다운로드 페이지** — <https://ota.kejizero.xyz/> 에 현재 빌드, 변경 기록, SHA256 이 있습니다.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> 에 이미지와 `SHA256SUMS` 가 있습니다.
- **기기에서** — *시스템 → 온라인 업그레이드* 로 브라우저 다운로드 없이 업그레이드합니다.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## 플래싱

**A. OpenWrt / ImmortalWrt 에서**
*시스템 → 백업/펌웨어 기록* 에서 `-squashfs-sysupgrade.bin` 을 업로드합니다. 메이저
버전을 넘을 때는 설정을 유지하지 마세요.

**B. 정품 펌웨어에서**
먼저 부트로더 복구 페이지(이 보드에서는 보통 U-Boot 웹 페이지)를 설치하고, 거기서
같은 이미지를 올립니다. 정품 관리 화면에서 직접 플래싱하지 마세요.

**C. 복구**
부트로더에서 `-initramfs-kernel.bin` 을 부팅해 임시 시스템을 만든 뒤, 그 안에서
sysupgrade 이미지를 기록합니다.

기본 주소 `10.0.0.1`, 사용자 `root`, 비밀번호 `password`. 첫 로그인에서 변경하세요.

## 온라인 업그레이드

`luci-app-ota` 가 포함되어 있습니다.

- 인덱스 기본값은 `https://ota.kejizero.xyz/ota.json` 이며 *시스템 → 온라인 업그레이드 → 설정* 에서 바꿀 수 있습니다.
- SHA256 은 필수입니다. 없으면 거부하고, 불일치하면 다운로드를 삭제합니다.
- "안전하지 않은 연결 허용"을 켜지 않으면 평문 `http` 는 거부합니다.
- 기기 키는 `/etc/ota/build.json`, 디바이스 트리 model, `board_name`, 아키텍처 순으로 찾으며 `vendor,device` 와 `vendor_device` 두 표기를 모두 받아들입니다.

## 빌드

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

`main` 에 푸시해도 빌드됩니다. Secrets, 입력, ccache, 각 단계는
[docs/BUILD.md](../BUILD.md) 에 정리되어 있습니다.

## FAQ

**소스는 어디에 있나요?** LEDE 트리는 비공개입니다. 이 저장소에는 파이프라인, 브랜딩 자산, 테스트가 있습니다.

**`factory` 이미지는 왜 없나요?** 이 보드는 부트로더의 웹 복구 페이지로 플래싱하며, sysupgrade 이미지를 그대로 받습니다.

**내 인덱스를 쓸 수 있나요?** 네. `api_url` 을 호환되는 JSON 으로 지정하고 원하는 곳에 호스팅하면 됩니다.

## 감사의 말

- **[OpenWrt](https://github.com/openwrt/openwrt)** — 빌드 시스템, LuCI, 그리고 대부분의 기본 패키지. 여기 있는 모든 것이 그 위에 서 있습니다.
- **[LEDE](https://github.com/coolsnowwolf/lede)** — ZeroWrt가 기반으로 삼는 소스 트리와 기본 설정.
- **[Yuzhii0718](https://github.com/Yuzhii0718)** — Ruijie RG-X60 New의 MT7986 포팅(immortalwrt-mt798x).

여기 이름을 올리지 못한 수많은 업스트림 패키지 작성자들에게도. 모든 빌드에서 그들의 코드가 돌아갑니다.

## 라이선스

이 저장소의 스크립트, 브랜딩 자산, 문서는 **GPL-2.0**으로 배포됩니다([LICENSE](../../LICENSE)).

펌웨어 자체에는 OpenWrt, LEDE 및 다수의 업스트림 구성 요소가 포함되며 각자의 라이선스를 따릅니다. 이미지를 재배포할 때도 마찬가지이며, GPL-2.0은 해당 소스 제공을 요구합니다.

## 면책

플래싱은 기기를 벽돌로 만들 수 있습니다. 정품 펌웨어와 설정을 백업하고 복구 경로를
확인한 뒤 진행하세요. 이 펌웨어는 있는 그대로 제공되며 보증이 없습니다.

---

관리자 문서: [docs/BUILD.md](../BUILD.md) · 다른 언어: [docs/readme](.)
