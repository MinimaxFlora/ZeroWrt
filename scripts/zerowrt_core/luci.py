"""LuCI status-page help links and zh_Hans translations.

The feed checkout is patched in-place after ``feeds install``.  Keep the patch
small, idempotent and verified: the JS is syntax-sensitive and a missing PO
entry silently falls back to English.
"""

from __future__ import annotations

from pathlib import Path

from . import util

STATUS_JS = Path("feeds/luci/modules/luci-mod-status/htdocs/luci-static/resources/view/status/include/10_system.js")
BASE_PO = Path("feeds/luci/modules/luci-base/po/zh_Hans/base.po")

STYLE_MARKER = "zerowrt-support-style"
STYLE_BLOCK = """\t\tif (!document.getElementById('zerowrt-support-style')) {
\t\t\tdocument.head.appendChild(E('style', { 'id': 'zerowrt-support-style' }, `
\t\t\t\t.support-btn {
\t\t\t\t\tdisplay: inline-flex;
\t\t\t\t\talign-items: center;
\t\t\t\t\tjustify-content: center;
\t\t\t\t\theight: 28px;
\t\t\t\t\tpadding: 0 12px;
\t\t\t\t\tborder-radius: 6px;
\t\t\t\t\tbackground: rgba(64, 158, 255, .85);
\t\t\t\t\tcolor: #fff !important;
\t\t\t\t\tfont-size: 13px;
\t\t\t\t\ttext-decoration: none !important;
\t\t\t\t\ttransition: all .2s ease;
\t\t\t\t\tbox-shadow: 0 2px 6px rgba(0, 0, 0, .15);
\t\t\t\t\tbackdrop-filter: blur(6px);
\t\t\t\t}

\t\t\t\t.support-btn:hover {
\t\t\t\t\ttransform: translateY(-2px);
\t\t\t\t\tbox-shadow: 0 6px 14px rgba(0, 0, 0, .25);
\t\t\t\t\topacity: .9;
\t\t\t\t}

\t\t\t\t.support-btn:active {
\t\t\t\t\ttransform: scale(.92);
\t\t\t\t}

\t\t\t\t.support-btn:nth-child(2) {
\t\t\t\t\tbackground: rgba(103, 194, 58, .85);
\t\t\t\t}

\t\t\t\t.support-btn:nth-child(3) {
\t\t\t\t\tbackground: rgba(230, 162, 60, .85);
\t\t\t\t}
\t\t\t`));
\t\t}

"""

FIELD_ANCHOR = "\t\t\t_('CPU usage (%)'),    cpuusage.cpuusage\n"
FIELD_BLOCK = """\t\t\t_('CPU usage (%)'),    cpuusage.cpuusage,
\t\t\t_('Help & Feedback'),  E('div', { 'style': 'display:flex;gap:8px;align-items:center;' }, [
\t\t\t\tE('a', {
\t\t\t\t\t'href': 'https://github.com/MinimaxFlora/ZeroWrt',
\t\t\t\t\t'target': '_blank',
\t\t\t\t\t'rel': 'noopener noreferrer',
\t\t\t\t\t'class': 'support-btn'
\t\t\t\t}, _('Project Website')),
\t\t\t\tE('a', {
\t\t\t\t\t'href': 'https://github.com/MinimaxFlora/ZeroWrt/issues',
\t\t\t\t\t'target': '_blank',
\t\t\t\t\t'rel': 'noopener noreferrer',
\t\t\t\t\t'class': 'support-btn'
\t\t\t\t}, _('Issue Feedback')),
\t\t\t\tE('a', {
\t\t\t\t\t'href': 'https://pay.kejizero.xyz',
\t\t\t\t\t'target': '_blank',
\t\t\t\t\t'rel': 'noopener noreferrer',
\t\t\t\t\t'class': 'support-btn'
\t\t\t\t}, _('Donation Address'))
\t\t\t])
"""

TRANSLATIONS = (
    ("Help & Feedback", "帮助与反馈"),
    ("Project Website", "项目主页"),
    ("Issue Feedback", "问题反馈"),
    ("Donation Address", "捐赠地址"),
)


def _require(path: Path) -> None:
    if not path.is_file():
        raise util.BuildError(f"missing LuCI file: {path}; run feeds install first")


def _line_number(text: str, needle: str) -> int:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    raise util.BuildError(f"cannot locate {needle!r} in the patched status page")


def patch_status_js(tree: Path) -> dict[str, int]:
    tree = Path(tree)
    path = tree / STATUS_JS
    _require(path)
    text = util.read_text(path)

    already = STYLE_MARKER in text and "_('Help & Feedback')" in text
    if not already:
        anchor = "\trender: function(data) {\n"
        if text.count(anchor) != 1:
            raise util.BuildError(f"{STATUS_JS}: render() anchor was not found exactly once")
        text = text.replace(anchor, anchor + STYLE_BLOCK, 1)

        if text.count(FIELD_ANCHOR) != 1:
            raise util.BuildError(f"{STATUS_JS}: CPU usage field anchor was not found exactly once")
        text = text.replace(FIELD_ANCHOR, FIELD_BLOCK, 1)

    util.write_text(path, text)

    lines = {msgid: _line_number(text, f"_('{msgid}')") for msgid, _translation in TRANSLATIONS}
    for marker in ("support-btn", "Help & Feedback", "Project Website", "Issue Feedback", "Donation Address"):
        if text.count(marker) < 1:
            raise util.BuildError(f"{STATUS_JS}: help/feedback marker {marker!r} is missing")
    if text.count("_('Help & Feedback')") != 1:
        raise util.BuildError(f"{STATUS_JS}: help/feedback block was duplicated")
    if "noopener noreferrer" not in text:
        raise util.BuildError(f"{STATUS_JS}: external links are missing rel=noopener")
    return lines


def _po_block(msgid: str, msgstr: str, line: int) -> str:
    reference = f"modules/luci-mod-status/htdocs/luci-static/resources/view/status/include/10_system.js:{line}"
    return f'#: {reference}\nmsgid "{msgid}"\nmsgstr "{msgstr}"\n'


def _ensure_po_header(text: str) -> str:
    """Add the two header fields gettext expects but the feed omits."""
    if '"Project-Id-Version:' not in text:
        text = text.replace('msgstr ""\n', 'msgstr ""\n"Project-Id-Version: LuCI\\n"\n', 1)
    if '"MIME-Version:' not in text:
        text = text.replace('msgstr ""\n', 'msgstr ""\n"MIME-Version: 1.0\\n"\n', 1)
    return text


def patch_base_po(tree: Path, lines: dict[str, int]) -> None:
    tree = Path(tree)
    path = tree / BASE_PO
    _require(path)
    text = _ensure_po_header(util.read_text(path))
    additions: list[str] = []

    for msgid, msgstr in TRANSLATIONS:
        expected = f'msgid "{msgid}"\nmsgstr "{msgstr}"'
        if expected in text:
            continue
        if f'msgid "{msgid}"' in text:
            raise util.BuildError(f"{BASE_PO}: {msgid!r} exists with a different translation")
        additions.append(_po_block(msgid, msgstr, lines[msgid]))

    if additions:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + "\n".join(additions)
    util.write_text(path, text)

    final = util.read_text(path)
    for msgid, msgstr in TRANSLATIONS:
        expected = f'msgid "{msgid}"\nmsgstr "{msgstr}"'
        if expected not in final:
            raise util.BuildError(f"{BASE_PO}: translation for {msgid!r} is missing")
    util.log(f"LuCI: help/feedback links and {len(TRANSLATIONS)} zh_Hans strings patched")


def apply(tree: Path) -> None:
    """Patch the status page and its zh_Hans catalog."""
    lines = patch_status_js(tree)
    patch_base_po(tree, lines)
