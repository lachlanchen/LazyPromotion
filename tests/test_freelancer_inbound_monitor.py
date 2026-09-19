from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import freelancer_inbound_monitor as monitor


class FreelancerInboundMonitorTests(unittest.TestCase):
    def test_seamo_project_urls_use_existing_review_only_monitor(self):
        base = (
            "https://www.freelancer.com/projects/technical-writing/"
            "SEAMO-Step-Step-Solutions"
        )
        for suffix in ("", "/details", "/proposals?bidCreated=true"):
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    monitor.project_id_for_url(base + suffix),
                    "seamo-solutions-freelancer",
                )

    def test_new_seamo_bid_adds_quiet_baseline_without_opening_messages(self):
        projects = {
            item["campaign_id"]: {
                "bid_state": "active_submitted",
                "rank": 9,
                "proposal_count": 9,
            }
            for item in monitor.TRACKED_PROJECTS
        }
        previous = {
            "version": 2,
            "message_badge_count": 1,
            "projects": {
                key: value for key, value in projects.items()
                if key != "seamo-solutions-freelancer"
            },
        }
        status, state = monitor.summarize_portfolio_observation(
            authenticated=True,
            projects=projects,
            message_badge_count=1,
            previous=previous,
            checked_at="2026-09-19T15:20:00Z",
        )
        self.assertEqual(status["tracked_bid_count"], 4)
        self.assertTrue(
            status["projects"]["seamo-solutions-freelancer"]["baseline_created"]
        )
        self.assertFalse(status["review_required"])
        self.assertFalse(status["message_opened"])
        self.assertIn("seamo-solutions-freelancer", state["projects"])

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

    def test_expired_listing_header_without_selection_is_closed(self):
        self.assertEqual(
            monitor.bid_state(
                "Project title\nNo Freelancer Selected\nBids\n89\n"
                "Average bid\nINR 25000\nDetails\nProposals\nYour Proposal"
            ),
            "closed",
        )

    def test_proposal_mention_of_no_selection_does_not_close_listing(self):
        self.assertEqual(
            monitor.bid_state(
                "Project title\nOpen\nBids\n9\nDetails\nProposals\n"
                "Your Proposal\nRetract\nEdit\n"
                "An old listing said No Freelancer Selected Bids 89."
            ),
            "active_submitted",
        )

    def observe_sequence(self, observations, *, timeout_ms=1000):
        elapsed = [0.0]
        page = Mock()

        def advance(ms):
            elapsed[0] += ms / 1000

        page.wait_for_timeout.side_effect = advance
        pending = iter(observations)
        current = observations[0]

        def read(_page):
            nonlocal current
            self.assertIs(_page, page)
            current = next(pending, current)
            return dict(current)

        with (
            patch.object(monitor.time, "monotonic", side_effect=lambda: elapsed[0]),
            patch.object(monitor, "page_observation", side_effect=read) as reader,
        ):
            result = monitor.settled_page_observation(page, timeout_ms=timeout_ms)
        return result, page, reader.call_count, elapsed[0]

    def observation(self, state="unknown", *, authenticated=True):
        return {
            "authenticated": authenticated,
            "bid_state": state,
            "message_badge_count": 0,
            "rank": None,
            "proposal_count": None,
        }

    def test_late_proposal_uses_fresh_state_without_navigating(self):
        active = self.observation("active_submitted")
        active["message_badge_count"] = 1
        result, page, reads, elapsed = self.observe_sequence(
            [self.observation(), self.observation(), active]
        )
        self.assertEqual(result, active)
        self.assertEqual(reads, 3)
        self.assertEqual(elapsed, 0.5)
        self.assertEqual(
            [call[0] for call in page.mock_calls],
            ["wait_for_timeout", "wait_for_timeout"],
        )

    def test_persistent_unknown_remains_unknown_at_finite_deadline(self):
        unknown = self.observation()
        result, page, reads, elapsed = self.observe_sequence([unknown], timeout_ms=600)
        self.assertEqual(result, unknown)
        self.assertEqual(reads, 4)
        self.assertAlmostEqual(elapsed, 0.6)
        self.assertEqual(page.wait_for_timeout.call_count, 3)
        page.goto.assert_not_called()
        page.reload.assert_not_called()

    def test_late_account_header_is_not_immediately_called_signed_out(self):
        active = self.observation("active_submitted")
        result, _, reads, _ = self.observe_sequence(
            [self.observation(authenticated=False), active]
        )
        self.assertEqual(result, active)
        self.assertEqual(reads, 2)

    def test_persistent_signed_out_state_is_not_replaced_with_active(self):
        signed_out = self.observation(authenticated=False)
        result, _, _, elapsed = self.observe_sequence([signed_out], timeout_ms=500)
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["bid_state"], "unknown")
        self.assertEqual(elapsed, 0.5)

    def test_terminal_states_are_returned_without_waiting_for_active_card(self):
        for state in ("closed", "awarded_review_required", "active_submitted"):
            with self.subTest(state=state):
                result, page, reads, _ = self.observe_sequence([self.observation(state)])
                self.assertEqual(result["bid_state"], state)
                self.assertEqual(reads, 1)
                page.wait_for_timeout.assert_not_called()

    def test_observation_deadline_is_validated(self):
        with self.assertRaises(ValueError):
            monitor.settled_page_observation(Mock(), timeout_ms=-1)

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
