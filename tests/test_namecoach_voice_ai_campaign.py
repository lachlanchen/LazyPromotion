import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NameCoachVoiceAiCampaignTests(unittest.TestCase):
    def test_sent_note_keeps_g2p_and_revenue_claims_bounded(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "namecoach-voice-ai-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(campaign["fit"]["projects"], ["L-and-N", "MultilingualWhisper"])
        self.assertIn("production grapheme-to-phoneme", campaign["fit"]["not_proven"][0])
        application = campaign["application"]
        self.assertEqual(application["state"], "sent_awaiting_human_reply")
        self.assertEqual(application["attachments_sent"], 0)
        self.assertFalse(application["production_g2p_claimed"])
        self.assertTrue(application["paid_take_home_requested"])
        self.assertFalse(application["automatic_follow_up"])
        funnel = campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["delivery_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["paid_take_home_offered"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
