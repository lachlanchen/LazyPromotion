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
        self.assertTrue(
            monitor.is_project_page(
                "https://www.freelancer.com/projects/kotlin/"
                "Provide-Android-APK-Download-Link/details"
            )
        )
        self.assertEqual(
            monitor.project_id_for_url(
                "https://www.freelancer.com/projects/kotlin/"
                "Provide-Android-APK-Download-Link/proposals?bidCreated=true"
            ),
            "android-apk-delivery-freelancer",
        )
        self.assertEqual(
            monitor.project_id_for_url(
                "https://www.freelancer.com/projects/virtual-assistant/"
                "KiCad-Plugin-Testing-Feedback/proposals?bidCreated=true"
            ),
            "kicad-plugin-testing-freelancer",
        )
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

    def test_portfolio_baseline_tracks_both_bids_quietly(self):
        projects = {
            "playwright-regression-contract": {
                "bid_state": "active_submitted",
                "rank": 57,
                "proposal_count": 58,
            },
            "android-apk-delivery-freelancer": {
                "bid_state": "active_submitted",
                "rank": 87,
                "proposal_count": 88,
            },
        }
        status, state = monitor.summarize_portfolio_observation(
            authenticated=True,
            projects=projects,
            message_badge_count=0,
            previous=None,
            checked_at="2026-09-11T23:55:00Z",
        )
        self.assertEqual(status["tracked_bid_count"], 2)
        self.assertTrue(status["baseline_created"])
        self.assertFalse(status["review_required"])
        self.assertFalse(status["message_opened"])
        self.assertEqual(state["version"], 2)

    def test_portfolio_adds_new_kicad_bid_as_quiet_project_baseline(self):
        projects = {
            "playwright-regression-contract": {
                "bid_state": "active_submitted",
                "rank": 57,
                "proposal_count": 58,
            },
            "android-apk-delivery-freelancer": {
                "bid_state": "active_submitted",
                "rank": 90,
                "proposal_count": 91,
            },
            "kicad-plugin-testing-freelancer": {
                "bid_state": "active_submitted",
                "rank": 20,
                "proposal_count": 20,
            },
        }
        previous = {
            "version": 2,
            "message_badge_count": 0,
            "projects": {
                key: value
                for key, value in projects.items()
                if key != "kicad-plugin-testing-freelancer"
            },
        }
        status, _ = monitor.summarize_portfolio_observation(
            authenticated=True,
            projects=projects,
            message_badge_count=0,
            previous=previous,
            checked_at="2026-09-12T01:50:00Z",
        )
        self.assertEqual(status["tracked_bid_count"], 3)
        self.assertTrue(
            status["projects"]["kicad-plugin-testing-freelancer"][
                "baseline_created"
            ]
        )
        self.assertFalse(status["review_required"])

    def test_portfolio_bid_change_names_only_the_changed_campaign(self):
        projects = {
            "playwright-regression-contract": {
                "bid_state": "closed",
                "rank": None,
                "proposal_count": None,
            },
            "android-apk-delivery-freelancer": {
                "bid_state": "active_submitted",
                "rank": 89,
                "proposal_count": 90,
            },
        }
        previous = {
            "version": 2,
            "message_badge_count": 0,
            "projects": {
                "playwright-regression-contract": {
                    "bid_state": "active_submitted",
                    "rank": 57,
                    "proposal_count": 58,
                },
                "android-apk-delivery-freelancer": {
                    "bid_state": "active_submitted",
                    "rank": 87,
                    "proposal_count": 88,
                },
            },
        }
        status, _ = monitor.summarize_portfolio_observation(
            authenticated=True,
            projects=projects,
            message_badge_count=0,
            previous=previous,
            checked_at="2026-09-12T00:00:00Z",
        )
        self.assertTrue(status["review_required"])
        self.assertEqual(
            status["review_project_ids"], ["playwright-regression-contract"]
        )
        self.assertFalse(
            status["projects"]["android-apk-delivery-freelancer"][
                "bid_state_changed"
            ]
        )

    def test_portfolio_message_badge_increase_never_opens_message(self):
        projects = {
            "android-apk-delivery-freelancer": {
                "bid_state": "active_submitted",
                "rank": 87,
                "proposal_count": 88,
            }
        }
        previous = {
            "version": 2,
            "message_badge_count": 10,
            "projects": projects,
        }
        status, _ = monitor.summarize_portfolio_observation(
            authenticated=True,
            projects=projects,
            message_badge_count=11,
            previous=previous,
            checked_at="2026-09-12T00:05:00Z",
        )
        self.assertTrue(status["new_message_signal"])
        self.assertTrue(status["review_required"])
        self.assertFalse(status["message_opened"])


if __name__ == "__main__":
    unittest.main()
