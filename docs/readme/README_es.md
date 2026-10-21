<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · **Español** · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware personalizado basado en LEDE, con actualización en línea de un clic.

**Haz push y sale un firmware. Abre LuCI y pulsa actualizar.**

[![Compilación](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Objetivo](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)

[Página de descarga](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Registros de build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Sistema → Actualización en línea → Buscar actualizaciones</code>

</div>

> [!IMPORTANT]
> **Solo fuentes oficiales.** El firmware se publica únicamente en los
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) de este repositorio
> y en [ota.kejizero.xyz](https://ota.kejizero.xyz/). Un nombre de repositorio
> parecido o un README copiado no convierten una compilación en oficial.

---

ZeroWrt es un firmware personalizado para routers de la clase OpenWrt, compilado desde un
árbol LEDE privado con GitHub Actions. Cada compilación se genera desde el código fuente,
se publica con `SHA256SUMS` y `BUILD_INFO.txt`, y se registra en un índice de
actualizaciones para que el equipo pueda actualizarse solo desde LuCI.

Lo interesante no es otra lista de paquetes, sino el ciclo: un commit inicia una
compilación, la compilación publica la imagen y el índice, y el router ve la nueva versión
en la siguiente comprobación.

## Características

- **Actualización con un clic** — LuCI lee el índice, descarga con reanudación y progreso, verifica el SHA256 y la imagen con `sysupgrade -T`, y luego la graba y reinicia.
- **Comprobación honesta de versión** — decide la fecha de compilación y, si no existe, compara cadenas de versión; una fecha desconocida se muestra como desconocida, no se inventa.
- **Configuración desde el workflow** — IP de LAN, nombre de host y tres SSID y contraseñas de Wi-Fi son entradas del build, no archivos editados a mano.
- **Marca Argon 3** — fondo, logo de acceso, favicon y paleta (`#2E9D72` / `#4CAF86`) se sustituyen al compilar.
- **Stack de proxy incluido** — PassWall (solo Xray) y OpenClash, sincronizados por los scripts de build.
- **Pipeline con control** — `ruff` y 18 pruebas unitarias en cada pull request.

## Dispositivos compatibles

| Dispositivo | Objetivo | Imágenes |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI y BIOS heredado |

Las etiquetas de release son el nombre del dispositivo (`ruijie_rg-x60-new`, `x86_64`).
Cada dispositivo conserva su propio release, así el índice y la página de descarga pueden
listarlos juntos.

## Descarga

- **Página de descarga** — <https://ota.kejizero.xyz/> muestra la compilación actual, el changelog y el SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> aloja las imágenes y `SHA256SUMS`.
- **En el equipo** — *Sistema → Actualización en línea* hace lo mismo sin descargar en el navegador.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flasheo

**A. Desde OpenWrt o ImmortalWrt**
*Sistema → Copia de seguridad / Flashear firmware*, sube el `-squashfs-sysupgrade.bin` y
no conserves la configuración al cambiar de versión mayor.

**B. Desde el firmware de fábrica**
Instala primero el gestor de arranque con recuperación (la página web U-Boot habitual en
esta placa) y sube allí la misma imagen. No flashes desde la interfaz de fábrica.

**C. Recuperación**
Arranca el `-initramfs-kernel.bin` desde el gestor de arranque para tener un sistema
temporal y desde ahí graba la imagen sysupgrade.

Dirección predeterminada `10.0.0.1`, usuario `root`, contraseña `password`. Cámbiala al entrar.

## Actualización en línea

El firmware incluye `luci-app-ota`:

- el índice es `https://ota.kejizero.xyz/ota.json` por defecto y se cambia en *Sistema → Actualización en línea → Configuración*;
- el SHA256 es obligatorio: una entrada sin él se rechaza y, si no coincide, se borra la descarga;
- se rechaza `http` sin cifrar salvo que se active *permitir conexiones inseguras*;
- la clave del dispositivo se resuelve desde `/etc/ota/build.json`, el modelo del árbol de dispositivos, `board_name` y la arquitectura, en ese orden, y se aceptan ambas grafías (`vendor,device` y `vendor_device`).

## Compilación

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Un push a `main` también compila. Los secretos, las entradas, la caché ccache y cada paso
están en [docs/BUILD.md](../BUILD.md).

## FAQ

**¿Dónde está el código?** El árbol LEDE es privado. Este repositorio contiene el pipeline, los recursos de marca y las pruebas.

**¿Por qué no hay imagen `factory`?** Estas placas se flashean desde la página de recuperación del gestor de arranque, que acepta directamente la imagen sysupgrade.

**¿Puedo usar mi propio índice?** Sí: apunta `api_url` a cualquier JSON compatible y alójalo donde quieras.

## Aviso legal

Flashear puede inutilizar el equipo. Haz copia del firmware de fábrica y de tu
configuración, y entiende la ruta de recuperación antes de empezar. El firmware se
entrega tal cual, sin garantía.

---

Notas para mantenedores: [docs/BUILD.md](../BUILD.md) · Otros idiomas: [docs/readme](.)
