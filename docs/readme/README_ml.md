<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · **മലയാളം**

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### LEDE അടിസ്ഥാനമാക്കിയുള്ള ഇഷ്ടാനുസൃത ഫേംവെയർ, ഒറ്റ ക്ലിക്കിൽ ഓൺലൈൻ അപ്ഡേറ്റ്.

**കമ്മിറ്റ് പുഷ് ചെയ്യൂ, ഫേംവെയർ കിട്ടും. LuCI തുറന്ന് അപ്ഡേറ്റ് അമർത്തുക.**

[![ബിൽഡ്](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![കേർണൽ](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![പ്ലാറ്റ്ഫോം](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[ഡൗൺലോഡ് പേജ്](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [ബിൽഡ് ലോഗുകൾ](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>സിസ്റ്റം → ഓൺലൈൻ അപ്ഗ്രേഡ് → അപ്ഡേറ്റുകൾ പരിശോധിക്കുക</code>

</div>

> [!IMPORTANT]
> **ഔദ്യോഗിക ഉറവിടങ്ങളിൽ നിന്ന് മാത്രം.** ഫേംവെയർ ഈ റിപ്പോസിറ്ററിയുടെ
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases), [ota.kejizero.xyz](https://ota.kejizero.xyz/)
> എന്നിവയിൽ മാത്രമാണ് പ്രസിദ്ധീകരിക്കുന്നത്. സമാനമായ റിപ്പോ നാമമോ പകർത്തിയ README-യോ
> ഒരു ബിൽഡിനെ ഔദ്യോഗികമാക്കുന്നില്ല.

---

ZeroWrt, OpenWrt കുടുംബത്തിലെ റൂട്ടറുകൾക്കുള്ള ചെറിയ ഇഷ്ടാനുസൃത ഫേംവെയറാണ്; സ്വകാര്യ LEDE
ട്രീയിൽ നിന്ന് GitHub Actions ഉപയോഗിച്ച് ഇത് ബിൽഡ് ചെയ്യുന്നു. ഓരോ ബിൽഡും സോഴ്സിൽ നിന്ന്
നിർമ്മിച്ച് `SHA256SUMS`, `BUILD_INFO.txt` എന്നിവയോടൊപ്പം പ്രസിദ്ധീകരിക്കുകയും അപ്ഡേറ്റ്
ഇൻഡക്സിൽ ചേർക്കുകയും ചെയ്യുന്നു, അതിനാൽ ഉപകരണത്തിന് LuCI-ൽ നിന്ന് തന്നെ അപ്ഗ്രേഡ്
ചെയ്യാം.

പ്രധാനം മറ്റൊരു പാക്കേജ് പട്ടികയല്ല, ഈ ചക്രമാണ്: ഒരു കമ്മിറ്റ് ബിൽഡ് തുടങ്ങുന്നു, ബിൽഡ്
ഇമേജും ഇൻഡക്സും പ്രസിദ്ധീകരിക്കുന്നു, അടുത്ത പരിശോധനയിൽ റൂട്ടർ പുതിയ പതിപ്പ് കാണുന്നു.

## സവിശേഷതകൾ

- **ഒറ്റ ക്ലിക്കിൽ അപ്ഡേറ്റ്** — LuCI ഇൻഡക്സ് വായിച്ച്, തുടർച്ചയും പ്രോഗ്രസും സഹിതം ഡൗൺലോഡ് ചെയ്ത്, SHA256-ഉം ഇമേജും `sysupgrade -T` ഉപയോഗിച്ച് പരിശോധിച്ച്, എഴുതി റീബൂട്ട് ചെയ്യുന്നു.
- **സത്യസന്ധമായ പതിപ്പ് താരതമ്യം** — ബിൽഡ് സമയമാണ് "പുതിയത്" എന്ന് തീരുമാനിക്കുന്നത്, ഇല്ലെങ്കിൽ പതിപ്പ് സ്ട്രിംഗ് താരതമ്യം ചെയ്യുന്നു; അറിയാത്ത തീയതി അറിയില്ല എന്നു തന്നെ കാണിക്കുന്നു, കെട്ടിച്ചമയ്ക്കുന്നില്ല.
- **വർക്ക്ഫ്ലോയിൽ നിന്നുള്ള കോൺഫിഗറേഷൻ** — LAN IP, ഹോസ്റ്റ്നെയിം, മൂന്ന് Wi-Fi SSID/പാസ്വേഡ് എന്നിവ ബിൽഡ് ഇൻപുട്ടുകളാണ്, കൈകൊണ്ട് തിരുത്തുന്ന ഫയലുകളല്ല.
- **Argon 3 ബ്രാൻഡിംഗ്** — പശ്ചാത്തലം, ലോഗിൻ ലോഗോ, favicon, നിറക്കൂട്ട് (`#2E9D72` / `#4CAF86`) എന്നിവ ബിൽഡ് സമയത്ത് മാറ്റുന്നു.
- **പ്രോക്സി സ്റ്റാക്ക് ഉൾപ്പെടെ** — PassWall (Xray മാത്രം), OpenClash എന്നിവ ബിൽഡ് സ്ക്രിപ്റ്റുകൾ സമന്വയിപ്പിക്കുന്നു.
- **പരിശോധനയുള്ള പൈപ്പ്ലൈൻ** — ഓരോ pull request-ലും `ruff`-ഉം 18 യൂണിറ്റ് ടെസ്റ്റുകളും ഓടുന്നു.

## പിന്തുണയ്ക്കുന്ന ഉപകരണങ്ങൾ

| ഉപകരണം | പ്ലാറ്റ്ഫോം | ഇമേജുകൾ |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI, പഴയ BIOS |

Release ടാഗുകൾ ഉപകരണത്തിന്റെ പേരാണ് (`ruijie_rg-x60-new`, `x86_64`). ഓരോ ഉപകരണത്തിനും
സ്വന്തം release ഉള്ളതിനാൽ ഇൻഡക്സും ഡൗൺലോഡ് പേജും ഇവ ഒരുമിച്ച് കാണിക്കാം.

## ഡൗൺലോഡ്

- **ഡൗൺലോഡ് പേജ്** — <https://ota.kejizero.xyz/> നിലവിലെ ബിൽഡ്, changelog, SHA256 എന്നിവ കാണിക്കുന്നു.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> ഇമേജുകളും `SHA256SUMS`-ഉം സൂക്ഷിക്കുന്നു.
- **ഉപകരണത്തിൽ തന്നെ** — *സിസ്റ്റം → ഓൺലൈൻ അപ്ഗ്രേഡ്* ബ്രൗസർ ഡൗൺലോഡ് ഇല്ലാതെ അതേ കാര്യം ചെയ്യുന്നു.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## ഫ്ലാഷ് ചെയ്യൽ

**A. OpenWrt അല്ലെങ്കിൽ ImmortalWrt-ൽ നിന്ന്**
*സിസ്റ്റം → ബാക്കപ്പ് / ഫേംവെയർ ഫ്ലാഷ്*, `-squashfs-sysupgrade.bin` അപ്‌ലോഡ് ചെയ്യുക;
പ്രധാന പതിപ്പ് മാറുമ്പോൾ കോൺഫിഗറേഷൻ നിലനിർത്തരുത്.

**B. ഫാക്ടറി ഫേംവെയറിൽ നിന്ന്**
ആദ്യം ബൂട്ട്ലോഡർ റിക്കവറി പേജ് (ഈ ബോർഡിൽ സാധാരണയായി U-Boot വെബ് പേജ്) ഇൻസ്റ്റാൾ ചെയ്ത
ശേഷം അതേ ഇമേജ് അവിടെ അപ്‌ലോഡ് ചെയ്യുക. ഫാക്ടറി വെബ് ഇന്റർഫേസിൽ നിന്ന് നേരിട്ട് ഫ്ലാഷ്
ചെയ്യരുത്.

**C. റിക്കവറി**
ബൂട്ട്ലോഡറിൽ നിന്ന് `-initramfs-kernel.bin` ബൂട്ട് ചെയ്ത് താൽക്കാലിക സിസ്റ്റം എടുത്ത ശേഷം
അതിൽ നിന്ന് sysupgrade ഇമേജ് എഴുതുക.

സ്ഥിരസ്ഥിതി വിലാസം `10.0.0.1`, ഉപയോക്താവ് `root`, പാസ്‌വേഡ് `password`. ആദ്യ ലോഗിനിൽ തന്നെ മാറ്റുക.

## ഓൺലൈൻ അപ്ഗ്രേഡ്

ഫേംവെയറിൽ `luci-app-ota` ഉണ്ട്:

- സ്ഥിരസ്ഥിതി ഇൻഡക്സ് `https://ota.kejizero.xyz/ota.json`, *സിസ്റ്റം → ഓൺലൈൻ അപ്ഗ്രേഡ് → കോൺഫിഗറേഷൻ*-ൽ മാറ്റാം;
- SHA256 നിർബന്ധമാണ്: ഇല്ലാത്ത എൻട്രി നിരസിക്കും, പൊരുത്തപ്പെടാത്താൽ ഡൗൺലോഡ് ഇല്ലാതാക്കും;
- *അസുരക്ഷിത കണക്ഷനുകൾ അനുവദിക്കുക* ഓണാക്കിയില്ലെങ്കിൽ വെറും `http` നിരസിക്കും;
- ഉപകരണ കീ `/etc/ota/build.json`, device tree model, `board_name`, ആർക്കിടെക്ചർ എന്ന ക്രമത്തിൽ
  കണ്ടെത്തുന്നു; `vendor,device`, `vendor_device` എന്നീ രണ്ട് രീതികളും സ്വീകരിക്കും.

## ബിൽഡ്

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

`main`-ലേക്ക് പുഷ് ചെയ്താലും ബിൽഡ് തുടങ്ങും. Secrets, ഇൻപുട്ടുകൾ, ccache, ഓരോ ഘട്ടവും
[docs/BUILD.md](../BUILD.md)-ൽ വിശദീകരിച്ചിട്ടുണ്ട്.

## പതിവുചോദ്യങ്ങൾ

**സോഴ്സ് എവിടെ?** LEDE ട്രീ സ്വകാര്യമാണ്. ഈ റിപ്പോയിൽ പൈപ്പ്ലൈനും ബ്രാൻഡിംഗ് അസറ്റുകളും ടെസ്റ്റുകളും ഉണ്ട്.

**`factory` ഇമേജ് എന്തുകൊണ്ട് ഇല്ല?** ഈ ബോർഡുകൾ ബൂട്ട്ലോഡറിന്റെ വെബ് റിക്കവറി പേജിലൂടെയാണ് ഫ്ലാഷ് ചെയ്യുന്നത്, അത് sysupgrade ഇമേജ് നേരിട്ട് സ്വീകരിക്കുന്നു.

**എന്റെ സ്വന്തം ഇൻഡക്സ് ഉപയോഗിക്കാമോ?** ഉപയോഗിക്കാം — `api_url` ഒരു അനുയോജ്യ JSON-ലേക്ക് ചൂണ്ടി എവിടെയെങ്കിലും ഹോസ്റ്റ് ചെയ്യുക.

## കൃതജ്ഞത

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## അനുമതി

ഈ റിപ്പോയിലെ സ്ക്രിപ്റ്റുകൾ, ബ്രാൻഡിംഗ് അസറ്റുകൾ, ഡോക്യുമെന്റേഷൻ എന്നിവ **GPL-2.0**-ൽ പുറത്തിറക്കുന്നു — [LICENSE](../../LICENSE).

ഫേംവെയറിൽ OpenWrt, LEDE, മറ്റു പല അപ്സ്ട്രീം ഘടകങ്ങളും ഉണ്ട്; ഓരോന്നിനും സ്വന്തം അനുമതിയുണ്ട്. ഇമേജ് വീണ്ടും വിതരണം ചെയ്യുമ്പോൾ ആ അനുമതികളും ബാധകമാണ്; GPL-2.0 പ്രത്യേകിച്ച് അനുബന്ധ സോഴ്സ് ലഭ്യമാക്കാൻ ആവശ്യപ്പെടുന്നു.

## നിരാകരണം

ഫ്ലാഷ് ചെയ്യൽ ഉപകരണം കേടാക്കിയേക്കാം. ഫാക്ടറി ഫേംവെയറും നിങ്ങളുടെ കോൺഫിഗറേഷനും
ബാക്കപ്പ് എടുക്കുക, റിക്കവറി മാർഗം മുൻകൂട്ടി മനസ്സിലാക്കുക. ഫേംവെയർ ഉള്ളതുപോലെ, യാതൊരു
വാറന്റിയും കൂടാതെ നൽകുന്നു.

---

അറ്റൻഡർമാർക്കുള്ള കുറിപ്പുകൾ: [docs/BUILD.md](../BUILD.md) · മറ്റ് ഭാഷകൾ: [docs/readme](.)
