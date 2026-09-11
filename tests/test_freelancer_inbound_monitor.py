from __future__ import annotations

import unittest

import freelancer_inbound_monitor as monitor


class FreelancerInboundMonitorTests(unittest.TestCase):
    def test_project_page_accepts_canonical_and_proposal_urls(self):
        canonical = (
            "https://www.freelancer.com/projects/automation/"
            "Playwright-Python-Regression-Suite"
        )
        self.assertTrue(monitor.is_project_page(canonical))
        self.assertTrue(monitor.is_project_page(f"{canonical}/proposals"))
        self.assertTrue(monitor.is_project_page(f"{canonical}/proposals/"))
        self.assertFalse(
            monitor.is_project_page(
                "https://example.com/projects/automation/"
                "Playwright-Python-Regression-Suite"
            )
        )
        self.assertFalse(
            monitor.is_project_page(
                "https://www.freelancer.com/projects/automation/another-project"
            )
        )

    def test_bid_state_recognizes_active_proposal(self):
        self.assertEqual(
            monitor.bid_state("Your Proposal\nLachlan\nRetract\nEdit"),
            "active_submitted",
        )

    def test_initial_observation_creates_quiet_baseline(self):
        status, state = monitor.summarize_observation(
            authenticated=True,
            current_bid_state="active_submitted",
            message_badge_count=0,
            rank=57,
            proposal_count=58,
            previous=None,
            checked_at="2026-09-11T20:40:00Z",
        )
        self.assertTrue(status["baseline_created"])
        self.assertFalse(status["review_required"])
        self.assertFalse(status["message_opened"])
        self.assertFalse(status["automatic_reply"])
        self.assertEqual(state["proposal_count"], 58)

    def test_new_message_signal_requires_review_without_opening(self):
        status, _ = monitor.summarize_observation(
            authenticated=True,
            current_bid_state="active_submitted",
            message_badge_count=1,
            rank=58,
            proposal_count=60,
            previous={"bid_state": "active_submitted", "message_badge_count": 0},
            checked_at="2026-09-11T20:45:00Z",
        )
        self.assertTrue(status["new_message_signal"])
        self.assertTrue(status["review_required"])
        self.assertFalse(status["message_opened"])

    def test_award_state_requires_review_even_without_badge(self):
        status, _ = monitor.summarize_observation(
            authenticated=True,
            current_bid_state="awarded_review_required",
            message_badge_count=0,
            rank=None,
            proposal_count=None,
            previous={"bid_state": "active_submitted", "message_badge_count": 0},
            checked_at="2026-09-11T20:50:00Z",
        )
        self.assertTrue(status["bid_state_changed"])
        self.assertTrue(status["review_required"])

    def test_rank_must_be_a_complete_pair(self):
        with self.assertRaises(ValueError):
            monitor.summarize_observation(
                authenticated=True,
                current_bid_state="active_submitted",
                message_badge_count=0,
                rank=1,
                proposal_count=None,
                previous=None,
                checked_at="2026-09-11T20:55:00Z",
            )


if __name__ == "__main__":
    unittest.main()
