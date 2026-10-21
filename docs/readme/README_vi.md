<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · **Tiếng Việt** · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware tùy biến dựa trên LEDE, cập nhật trực tuyến chỉ bằng một cú nhấp.

**Push commit là có firmware. Mở LuCI, bấm cập nhật.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Nhân](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Nền tảng](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Trang tải xuống](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Nhật ký build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Hệ thống → Cập nhật trực tuyến → Kiểm tra cập nhật</code>

</div>

> [!IMPORTANT]
> **Chỉ tải từ nguồn chính thức.** Firmware chỉ được phát hành trong
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) của kho này và trên
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). Tên kho tương tự hoặc README bị sao
> chép không làm cho bản build trở thành chính thức.

---

ZeroWrt là firmware tùy biến nhỏ gọn cho các router dòng OpenWrt, được GitHub Actions
biên dịch từ một cây LEDE riêng. Mỗi bản build đều sinh ra từ mã nguồn, phát hành kèm
`SHA256SUMS` và `BUILD_INFO.txt`, đồng thời ghi vào chỉ mục cập nhật để thiết bị có thể tự
nâng cấp ngay trong LuCI.

Điểm đáng nói không phải một danh sách gói khác, mà là vòng lặp: một commit khởi động
build, build phát hành ảnh và chỉ mục, router thấy phiên bản mới ở lần kiểm tra kế tiếp.

## Tính năng

- **Cập nhật một cú nhấp** — LuCI đọc chỉ mục, tải có tiếp tục và tiến trình, kiểm SHA256 và ảnh bằng `sysupgrade -T`, rồi ghi và khởi động lại.
- **So sánh phiên bản trung thực** — mốc thời gian build quyết định "mới hơn", nếu không có thì so chuỗi phiên bản; ngày không xác định được hiển thị là không rõ, không bịa ra.
- **Cấu hình do workflow truyền vào** — IP LAN, tên máy và ba SSID/mật khẩu Wi-Fi là tham số build, không phải sửa tay trong tệp.
- **Thương hiệu Argon 3** — ảnh nền, logo đăng nhập, favicon và bảng màu (`#2E9D72` / `#4CAF86`) được thay khi build.
- **Kèm bộ proxy** — PassWall (chỉ Xray) và OpenClash, được script build đồng bộ.
- **Quy trình có kiểm soát** — `ruff` và 18 bài kiểm thử đơn vị cho mỗi pull request.

## Thiết bị hỗ trợ

| Thiết bị | Nền tảng | Ảnh |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI và BIOS cũ |

Thẻ release chính là tên thiết bị (`ruijie_rg-x60-new`, `x86_64`). Mỗi thiết bị giữ release
riêng nên chỉ mục và trang tải xuống có thể liệt kê song song.

## Tải xuống

- **Trang tải xuống** — <https://ota.kejizero.xyz/> hiển thị bản build hiện tại, changelog và SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> lưu ảnh và `SHA256SUMS`.
- **Ngay trên thiết bị** — *Hệ thống → Cập nhật trực tuyến* làm điều tương tự, không cần tải bằng trình duyệt.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Nạp firmware

**A. Từ OpenWrt hoặc ImmortalWrt**
*Hệ thống → Sao lưu / Nạp firmware*, tải lên `-squashfs-sysupgrade.bin` và đừng giữ cấu
hình khi nhảy phiên bản lớn.

**B. Từ firmware hãng**
Cài trang phục hồi của bootloader trước (bo mạch này thường là trang web U-Boot), rồi tải
cùng ảnh đó lên đó. Đừng nạp trực tiếp từ giao diện của hãng.

**C. Cứu máy**
Khởi động `-initramfs-kernel.bin` từ bootloader để có hệ thống tạm, rồi nạp ảnh sysupgrade
từ trong đó.

Địa chỉ mặc định `10.0.0.1`, người dùng `root`, mật khẩu `password`. Đổi ngay sau lần đăng nhập đầu.

## Cập nhật trực tuyến

Firmware có sẵn `luci-app-ota`:

- chỉ mục mặc định là `https://ota.kejizero.xyz/ota.json`, đổi được ở *Hệ thống → Cập nhật trực tuyến → Cấu hình*;
- SHA256 là bắt buộc: mục thiếu mã sẽ bị từ chối, sai mã thì tệp tải về bị xóa;
- `http` không mã hóa bị từ chối trừ khi bật *cho phép kết nối không an toàn*;
- khóa thiết bị được suy ra từ `/etc/ota/build.json`, model trong device tree, `board_name` và kiến trúc, chấp nhận cả hai cách viết (`vendor,device` và `vendor_device`).

## Biên dịch

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Push lên `main` cũng kích hoạt build. Secrets, tham số, ccache và từng bước được ghi ở
[docs/BUILD.md](../BUILD.md).

## FAQ

**Mã nguồn ở đâu?** Cây LEDE là riêng tư. Kho này chứa quy trình, tài nguyên thương hiệu và kiểm thử.

**Vì sao không có ảnh `factory`?** Bo mạch này được nạp qua trang phục hồi của bootloader, trang đó nhận thẳng ảnh sysupgrade.

**Có dùng chỉ mục riêng được không?** Được — trỏ `api_url` tới một JSON tương thích và tự lưu trữ ở đâu cũng được.

## Ghi công

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Giấy phép

Script, tài nguyên thương hiệu và tài liệu trong kho này được phát hành theo **GPL-2.0** — xem [LICENSE](../../LICENSE).

Bản thân firmware gồm OpenWrt, LEDE và nhiều thành phần thượng nguồn khác, mỗi phần theo giấy phép riêng. Khi phát hành lại ảnh, các giấy phép đó cũng áp dụng; GPL-2.0 đặc biệt yêu cầu cung cấp mã nguồn tương ứng.

## Miễn trừ trách nhiệm

Nạp firmware có thể làm hỏng thiết bị. Hãy sao lưu firmware gốc và cấu hình của bạn, đồng
thời hiểu rõ cách cứu máy trước khi bắt đầu. Firmware được cung cấp nguyên trạng, không bảo hành.

---

Ghi chú cho người bảo trì: [docs/BUILD.md](../BUILD.md) · Ngôn ngữ khác: [docs/readme](.)
