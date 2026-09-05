import json
import unittest
from pathlib import Path

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "campaigns" / "meeting-intelligence-mission.json"


class MeetingIntelligenceCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))

    def test_offer_is_bounded_and_milestones_equal_quote(self):
        offer = self.campaign["offer"]
        self.assertEqual(offer["quotation_usd"], 8000)
        self.assertEqual(sum(offer["milestones_usd"]), offer["quotation_usd"])
        self.assertEqual(offer["scope_caps"]["pilot_meetings"], 3)
        self.assertEqual(offer["scope_caps"]["minutes_per_meeting"], 60)

    def test_public_proof_keeps_important_boundaries(self):
        proof = self.campaign["owned_proof"]
        limits = " ".join(proof["limits"]).casefold()
        self.assertIn("scripted", limits)
        self.assertIn("manual", limits)
        self.assertIn("real-room asr", limits)
        self.assertIn("customer outcomes", limits)
        self.assertIn("metadata", proof["contact_path"])
        self.assertIn("before any confidential audio is attached", proof["contact_path"])
        self.assertRegex(proof["website_commit"], r"^[0-9a-f]{40}$")

    def test_linkedin_queue_uses_one_first_party_destination(self):
        linkedin = self.campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_queued")
        self.assertEqual(linkedin["verification"]["state_rechecked_after_schedule"], "QUEUE")
        self.assertFalse(linkedin["verification"]["shortener_used"])
        self.assertEqual(linkedin["verification"]["duplicate_queue_items"], 0)
        self.assertIn("lazying.art/meeting-intelligence/", linkedin["scheduled_content_link"])
        self.assertNotIn("dub.sh", linkedin["scheduled_content_link"])

    def test_read_only_monitor_can_route_the_queued_post(self):
        linkedin = self.campaign["channels"]["linkedin"]
        route = owned_monitor.route_for_post(
            "linkedin",
            linkedin["content"],
            owned_monitor.route_index(ROOT / "campaigns"),
        )
        self.assertEqual(route["campaign_id"], "meeting-intelligence-mission")
        self.assertEqual(route["route"], "product")

    def test_marketplace_and_revenue_states_do_not_overclaim(self):
        upwork = self.campaign["channels"]["upwork"]
        funnel = self.campaign["funnel"]
        self.assertFalse(upwork["application_submitted"])
        self.assertEqual(upwork["connects_spent"], 0)
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
