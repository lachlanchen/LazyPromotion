import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WeTheFlywheelCampaignTests(unittest.TestCase):
    def test_failed_form_and_single_email_remain_distinct(self):
        campaign = json.loads(
            (
                ROOT
                / "campaigns"
                / "wetheflywheel-agentic-engineer.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(campaign["fit"]["projects"], ["LazyPromotion", "LazyEdge"])
        application = campaign["application"]
        self.assertEqual(
            application["state"], "paused_operator_dependency"
        )
        self.assertEqual(application["official_form"]["submit_attempts"], 1)
        self.assertFalse(application["official_form"]["accepted"])
        self.assertFalse(application["official_form"]["retried"])
        self.assertFalse(application["resume_attached"])
        self.assertFalse(application["whatsapp_supplied"])
        self.assertFalse(application["fallback"]["automatic_follow_up"])
        self.assertFalse(application["route_review"]["cv_sent"])
        self.assertFalse(application["route_review"]["time_committed"])
        self.assertFalse(application["route_review"]["commercial_terms_accepted"])

    def test_outbound_application_is_not_revenue(self):
        campaign = json.loads(
            (
                ROOT
                / "campaigns"
                / "wetheflywheel-agentic-engineer.json"
            ).read_text(encoding="utf-8")
        )
        funnel = campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["sender_side_sent_evidence_observed"])
        self.assertTrue(funnel["human_reply_observed"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_project_question_does_not_accept_the_ongoing_role(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "wetheflywheel-agentic-engineer.json").read_text(
                encoding="utf-8"
            )
        )
        application = campaign["application"]
        review = application["route_review"]
        question = review["project_only_qualification"]
        self.assertEqual(application["state"], "paused_operator_dependency")
        self.assertTrue(review["follow_up_sent"])
        self.assertEqual(question["state"], "question_sent_awaiting_reply")
        self.assertEqual(question["message_count"], 1)
        self.assertEqual(question["attachment_count"], 0)
        for field in (
            "automatic_follow_up",
            "new_application",
            "scope_offered_by_buyer",
            "rate_agreed",
            "work_accepted",
        ):
            with self.subTest(field=field):
                self.assertFalse(question[field])
        for field in ("cv_sent", "time_committed", "commercial_terms_accepted"):
            with self.subTest(field=field):
                self.assertFalse(review[field])
        serialized = json.dumps(question)
        self.assertNotIn("@", serialized)
        self.assertNotIn("message_body", question)


if __name__ == "__main__":
    unittest.main()
