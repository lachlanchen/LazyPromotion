import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "cjk-chunk-boundary"


@unittest.skipUnless(shutil.which("node"), "Node is required for the JavaScript example")
class CjkChunkBoundaryTests(unittest.TestCase):
    def test_javascript_regressions(self):
        subprocess.run(
            ["node", "--test", str(EXAMPLE / "test.cjs")],
            check=True, capture_output=True, text=True, timeout=15,
        )

    def test_demo_reports_observed_boundaries_not_token_or_customer_claims(self):
        result = subprocess.run(
            ["node", str(EXAMPLE / "demo.cjs")],
            check=True, capture_output=True, text=True, timeout=5,
        )
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["whitespaceMatches"], 1)
        self.assertEqual(evidence["codePoints"], 1000)
        self.assertEqual(evidence["chunks"], 5)
        self.assertEqual(evidence["maximumChunkCodePoints"], 200)
        self.assertTrue(evidence["exactSourceRecovered"])
        self.assertFalse(evidence["embeddingTokenLimitVerified"])

    def test_article_javascript_runs_and_preserves_the_same_ranges(self):
        source = (ROOT / "articles/chinese-rag-whitespace-chunks/post.md").read_text()
        blocks = re.findall(r"```js\n(.*?)\n```", source, flags=re.DOTALL)
        self.assertEqual(len(blocks), 2)
        check = """
const assert = require('node:assert/strict');
assert.equal(words.length, 1);
assert.equal([...text].length, 1000);
const chunks = splitWithOffsets('甲𠮷乙🧪丙', 2);
assert.deepEqual(chunks.map(c => [c.start, c.end]), [[0, 3], [3, 6], [6, 7]]);
assert.equal(chunks.map(c => c.text).join(''), '甲𠮷乙🧪丙');
assert.throws(() => splitWithOffsets('text', 0), RangeError);
"""
        subprocess.run(
            ["node", "-e", "\n".join(blocks) + check],
            check=True, capture_output=True, text=True, timeout=5,
        )
