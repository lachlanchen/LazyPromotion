import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "minimax-h3-voice-reference-diagnostic.json"


class MiniMaxH3VoiceReferenceDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_reply_answers_a_current_exact_need_without_a_pitch(self):
        source = self.data["source_need"]
        reddit = self.data["channels"]["reddit"]

        self.assertIn("1wdv3dj", source["url"])
        self.assertEqual(reddit["state"], "helpful_reply_published")
        self.assertFalse(reddit["linked_owned_asset"])
        self.assertFalse(reddit["product_or_price_mentioned"])
        self.assertIn("connector order", reddit["content"])
        self.assertIn("several seeds", reddit["content"])

    def test_single_run_evidence_is_not_presented_as_a_general_result(self):
        evidence = self.data["source_evidence"]

        self.assertIn("One local Ref2VA render", evidence["project_owned_result"])
        self.assertIn("not a guarantee", evidence["claim_boundary"])
        self.assertIn("not linked", evidence["claim_boundary"])

    def test_open_source_reply_names_the_full_code_path_without_claiming_a_patch(self):
        need = self.data["related_open_source_need"]
        github = self.data["channels"]["github"]

        self.assertIn("2294", need["url"])
        self.assertEqual(github["state"], "technical_reply_published")
        self.assertTrue(github["linked_owned_asset"])
        self.assertFalse(github["product_or_price_mentioned"])
        self.assertIn("handler", github["content"])
        self.assertIn("pipeline", github["content"])
        self.assertIn("Do not add another comment", github["policy"])
        self.assertNotIn("implemented", github["policy"].lower())

    def test_helpful_interaction_does_not_inflate_the_revenue_funnel(self):
        funnel = self.data["funnel"]

        self.assertEqual(funnel["state"], "helpful_interaction")
        self.assertFalse(funnel["reply_received"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["scope_accepted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
