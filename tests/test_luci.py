from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import luci, util


class LuciTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name)
        self.js = self.tree / luci.STATUS_JS
        self.js.parent.mkdir(parents=True)
        self.js.write_text(
            "'use strict';\n"
            "\n"
            "return baseclass.extend({\n"
            "\trender: function(data) {\n"
            "\t\tvar fields = [\n"
            "\t\t\t_('Hostname'), boardinfo.hostname,\n"
            "\t\t\t_('CPU usage (%)'),    cpuusage.cpuusage\n"
            "\t\t];\n"
            "\t}\n"
            "});\n",
            encoding="utf-8",
        )
        self.po = self.tree / luci.BASE_PO
        self.po.parent.mkdir(parents=True)
        self.po.write_text(
            'msgid ""\nmsgstr ""\n"Language: zh_Hans\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n',
            encoding="utf-8",
        )
        self.zones = self.tree / luci.FIREWALL_ZONES
        self.zones.parent.mkdir(parents=True)
        self.zones.write_text(
            "return baseclass.extend({\n"
            "\trender: function() {\n"
            "\t\t/* Netfilter flow offload support */\n"
            "\n"
            "\t\tif (L.hasSystemFeature('offloading')) {\n"
            "\t\t\ts = m.section(form.TypedSection, 'defaults', _('Routing/NAT Offloading'),\n"
            "\t\t\t\t_('Not fully compatible with QoS/SQM.'));\n"
            "\n"
            '\t\t\to = s.option(form.RichListValue, "offloading_type", _("Flow offloading type"));\n'
            "\t\t\to.load = function (section_id) {\n"
            "\t\t\t\tvar flow_offloading = uci.get('firewall', section_id, 'flow_offloading');\n"
            "\t\t\t};\n"
            "\t\t}\n"
            "\n"
            "\t\ts = m.section(form.GridSection, 'zone', _('Zones'));\n"
            "\t}\n"
            "});\n",
            encoding="utf-8",
        )

    def test_apply_is_idempotent_and_translates(self) -> None:
        luci.apply(self.tree)
        js = self.js.read_text(encoding="utf-8")
        self.assertIn("zerowrt-support-style", js)
        self.assertIn("_('Help & Feedback')", js)
        self.assertIn("_('Project Website')", js)
        self.assertIn("_('Issue Feedback')", js)
        self.assertIn("_('Donation Address')", js)
        self.assertIn("rel': 'noopener noreferrer'", js)
        self.assertNotIn("TODO", js)

        po = self.po.read_text(encoding="utf-8")
        self.assertIn('"Project-Id-Version: LuCI\\n"', po)
        self.assertIn('"MIME-Version: 1.0\\n"', po)
        for msgid, msgstr in luci.TRANSLATIONS:
            self.assertIn(f'msgid "{msgid}"\nmsgstr "{msgstr}"', po)
        self.assertIn("10_system.js:", po)

        zones = self.zones.read_text(encoding="utf-8")
        self.assertNotIn("Netfilter flow offload support", zones)
        self.assertNotIn("offloading_type", zones)
        self.assertNotIn("flow_offloading", zones)
        self.assertIn("_('Zones')", zones)

        before = js, po, zones
        luci.apply(self.tree)
        self.assertEqual(
            (
                self.js.read_text(encoding="utf-8"),
                self.po.read_text(encoding="utf-8"),
                self.zones.read_text(encoding="utf-8"),
            ),
            before,
        )

    def test_missing_status_page_fails(self) -> None:
        self.js.unlink()
        with self.assertRaises(util.BuildError):
            luci.apply(self.tree)


if __name__ == "__main__":
    unittest.main()
