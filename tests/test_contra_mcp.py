from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ContraMcpTests(unittest.TestCase):
    def test_project_config_keeps_contra_writes_reviewed(self) -> None:
        config = (ROOT / ".codex" / "config.toml").read_text(encoding="utf-8")
        match = re.search(
            r"\[mcp_servers\.contra\](.*?)(?=\n\[|\Z)", config, re.S
        )
        self.assertIsNotNone(match)
        section = match.group(1)
        self.assertIn('url = "https://contra.com/mcp"', section)
        self.assertIn('default_tools_approval_mode = "writes"', section)
        self.assertIn("required = false", section)
        self.assertNotRegex(section, r"(?i)(access_token|refresh_token|password)")

    def test_operator_doc_has_no_literal_oauth_material(self) -> None:
        text = (ROOT / "docs" / "contra-mcp.md").read_text(encoding="utf-8")
        self.assertIn("two-step prepare-and-confirm", text)
        self.assertIn("list_job_feed", text)
        self.assertIn("access-limited", text)
        self.assertNotRegex(text, r"(?i)bearer\s+[a-z0-9._~-]{20,}")
        self.assertNotRegex(text, r"(?i)(access|refresh)[_-]?token\s*[:=]\s*\S+")


if __name__ == "__main__":
    unittest.main()
