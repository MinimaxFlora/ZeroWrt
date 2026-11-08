from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PINNED_ACTION_RE = re.compile(r"@[0-9a-f]{40}(?:\s+#.*)?$")


class WorkflowTest(unittest.TestCase):
    def test_workflows_parse(self) -> None:
        for path in sorted(WORKFLOWS.glob("*.yml")):
            with self.subTest(path=path.name):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)

    def test_actions_are_pinned_to_sha(self) -> None:
        for path in sorted(WORKFLOWS.glob("*.yml")):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith(("uses:", "- uses:")):
                    continue
                value = stripped.split("uses:", 1)[1].strip()
                with self.subTest(path=path.name, action=value):
                    self.assertRegex(value, PINNED_ACTION_RE)


if __name__ == "__main__":
    unittest.main()
