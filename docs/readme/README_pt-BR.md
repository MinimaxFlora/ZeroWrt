<div align="center">

[English](../../README.md) · [简体中文](README_zh-CN.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · **Português (Brasil)** · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Firmware personalizado baseado em LEDE, com atualização online em um clique.

**Faça o push, ganhe um firmware. Abra o LuCI e clique em atualizar.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Alvo](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Página de download](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Logs de build](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>Sistema → Atualização online → Verificar atualizações</code>

</div>

> [!IMPORTANT]
> **Somente fontes oficiais.** O firmware é publicado apenas nas
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) deste repositório e
> em [ota.kejizero.xyz](https://ota.kejizero.xyz/). Um nome de repositório
> parecido ou um README copiado não torna um build oficial.

---

ZeroWrt é um firmware personalizado para roteadores da classe OpenWrt, compilado de uma
árvore LEDE privada pelo GitHub Actions. Todo build é gerado a partir do código, publicado
com `SHA256SUMS` e `BUILD_INFO.txt` e registrado em um índice de atualização, para que o
dispositivo se atualize sozinho pelo LuCI.

O interessante não é mais uma lista de pacotes, e sim o ciclo: um commit inicia o build, o
build publica a imagem e o índice, e o roteador vê a nova versão na próxima verificação.

## Recursos

- **Atualização em um clique** — o LuCI lê o índice, baixa com retomada e progresso, valida o SHA256 e a imagem com `sysupgrade -T` e então grava e reinicia.
- **Comparação honesta de versão** — o carimbo de build decide; sem ele, compara strings de versão. Data desconhecida aparece como desconhecida, não é inventada.
- **Configuração vinda do workflow** — IP da LAN, hostname e três SSIDs/senhas de Wi-Fi são entradas de build, não arquivos editados à mão.
- **Identidade Argon 3** — plano de fundo, logo de login, favicon e paleta (`#2E9D72` / `#4CAF86`) substituídos na compilação.
- **Stack de proxy incluído** — PassWall (apenas Xray) e OpenClash, sincronizados pelos scripts de build.
- **Pipeline com controle** — `ruff` e 18 testes unitários em todo pull request.

## Dispositivos suportados

| Dispositivo | Alvo | Imagens |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI e BIOS legado |

As tags de release são o nome do dispositivo (`ruijie_rg-x60-new`, `x86_64`). Cada
dispositivo mantém a própria release, então o índice e a página de download podem listá-los
lado a lado.

## Download

- **Página de download** — <https://ota.kejizero.xyz/> mostra o build atual, o changelog e o SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> guarda as imagens e o `SHA256SUMS`.
- **No dispositivo** — *Sistema → Atualização online* faz o mesmo sem baixar no navegador.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Gravação

**A. A partir do OpenWrt ou ImmortalWrt**
*Sistema → Backup / Gravar firmware*, envie o `-squashfs-sysupgrade.bin` e não mantenha a
configuração ao trocar de versão principal.

**B. A partir do firmware de fábrica**
Instale primeiro a recuperação do bootloader (a página web U-Boot habitual nesta placa) e
envie a mesma imagem por lá. Não grave pela interface de fábrica.

**C. Recuperação**
Inicie o `-initramfs-kernel.bin` pelo bootloader para ter um sistema temporário e grave a
imagem sysupgrade a partir dele.

Endereço padrão `10.0.0.1`, usuário `root`, senha `password`. Troque no primeiro acesso.

## Atualização online

O firmware inclui o `luci-app-ota`:

- o índice padrão é `https://ota.kejizero.xyz/ota.json` e pode ser alterado em *Sistema → Atualização online → Configuração*;
- o SHA256 é obrigatório: entrada sem ele é recusada e, se não conferir, o download é apagado;
- `http` sem TLS é recusado, a menos que *permitir conexões inseguras* esteja ativo;
- a chave do dispositivo é obtida de `/etc/ota/build.json`, do modelo da árvore de dispositivos, do `board_name` e da arquitetura, nessa ordem, aceitando as duas grafias (`vendor,device` e `vendor_device`).

## Compilação

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Um push para `main` também compila. Segredos, entradas, ccache e cada etapa estão em
[docs/BUILD.md](../BUILD.md).

## FAQ

**Onde está o código?** A árvore LEDE é privada. Este repositório contém o pipeline, os assets de marca e os testes.

**Por que não existe imagem `factory`?** Estas placas são gravadas pela página de recuperação do bootloader, que aceita a imagem sysupgrade diretamente.

**Posso usar meu próprio índice?** Sim — aponte `api_url` para qualquer JSON compatível e hospede onde quiser.

## Agradecimentos

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [sbwml](https://github.com/sbwml) |
| :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> |
| [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## Licença

Os scripts, os assets de marca e a documentação deste repositório são publicados sob **GPL-2.0** — veja [LICENSE](../../LICENSE).

O firmware inclui OpenWrt, LEDE e muitos outros componentes upstream, cada um com sua licença. Ao redistribuir uma imagem, essas licenças também valem; a GPL-2.0 exige, em especial, disponibilizar o código-fonte correspondente.

## Aviso

Gravar firmware pode inutilizar o aparelho. Faça backup do firmware de fábrica e da sua
configuração e entenda o caminho de recuperação antes de começar. O firmware é fornecido
como está, sem garantia.

---

Notas para mantenedores: [docs/BUILD.md](../BUILD.md) · Outros idiomas: [docs/readme](.)
