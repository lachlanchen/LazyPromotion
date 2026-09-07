import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LopakaEmbeddedUiCampaignTests(unittest.TestCase):
    def test_submitted_application_keeps_claims_and_revenue_bounded(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "lopaka-embedded-ui-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(campaign["source_need"]["state"], "official_current_paid_contract")
        self.assertEqual(campaign["fit"]["projects"], ["stm32dev", "WordsCardEink"])
        self.assertIn("Public LVGL", campaign["fit"]["not_proven"][0])
        application = campaign["application"]
        self.assertEqual(application["state"], "sent_awaiting_human_reply")
        self.assertFalse(application["resume_uploaded"])
        self.assertFalse(application["lvgl_experience_claimed"])
        self.assertFalse(application["customer_shipping_claimed"])
        self.assertFalse(application["automatic_follow_up"])
        funnel = campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["automatic_receipt_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
