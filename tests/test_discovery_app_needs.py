import unittest

import browser
import promotion


class AppNeedDiscoveryTests(unittest.TestCase):
    def route(self, project):
        return next(row for row in browser.discovery_query_lanes("reddit")["core"]
                    if row["project_id"] == project)

    def test_apps_have_explicit_topic_and_need_core_routes(self):
        for project in ("l-and-n", "github-bunko"):
            route = self.route(project)
            self.assertEqual(route["query"].count(" AND "), 2)
            self.assertTrue(route["required_body_groups"])
            self.assertFalse(any(row["project_id"] == project for row in
                                 browser.discovery_query_lanes("reddit")["long_tail"]))

    def test_landn_requires_the_actual_contrast_and_a_need(self):
        route = self.route("l-and-n")
        for text in (
            "I confuse L and N sounds. Can anyone help with pronunciation?",
            "Looking for listening practice to distinguish n/l sounds.",
        ):
            self.assertTrue(browser.route_body_qualified(text, route))
        for text in (
            "Can anyone help with English R and L pronunciation?",
            "How do my dark L sounds in feel sound?",
            "I built my app for L and N pronunciation practice.",
            "A historical description of n/l sounds and pronunciation.",
        ):
            self.assertFalse(browser.route_body_qualified(text, route))

    def test_bunko_requires_reading_aids_not_generic_history_or_a_launch(self):
        route = self.route("github-bunko")
        for text in (
            "Can anyone recommend Japanese novels with furigana for reading?",
            "Is there a Chinese bilingual reader for books?",
        ):
            self.assertTrue(browser.route_body_qualified(text, route))
        for text in (
            "Where can I read about Chinese history?",
            "I built my app for reading Japanese novels with furigana. Recommend it!",
            "Can anyone recommend a French bilingual reader for books?",
        ):
            self.assertFalse(browser.route_body_qualified(text, route))

    def test_generated_reddit_routes_require_topic_and_intent(self):
        project = {"name": "Example", "keywords": ["local documents"]}
        self.assertEqual(browser.automatic_query("reddit", project),
                         '("local documents") AND (help OR advice OR recommend)')
        self.assertEqual(browser.automatic_query("reddit", project, "parallel text reader"),
                         '("parallel text reader") AND (help OR advice OR recommend)')
        self.assertNotIn(" AND ", browser.automatic_query("x", project))
        self.assertEqual(browser.automatic_query("hackernews", project), 'Ask HN "local documents"')

    def test_authorship_restrictions_apply_to_exact_communities(self):
        for community in ("JapaneseResources", "LanguageLearning", "ChineseHistory"):
            for action in ("public_reply", "private_contact"):
                reason = promotion.agent_contact_block_reason(
                    "reddit", f"https://www.reddit.com/r/{community}/comments/example/request/",
                    action=action,
                )
                self.assertTrue(reason)
                self.assertIn("AI", reason)
        for community in ("ESL_Teachers", "SideProject", "AppsWebappsFullstack"):
            self.assertEqual(promotion.agent_contact_block_reason(
                "reddit", f"https://www.reddit.com/r/{community}/comments/example/request/",
                action="public_reply",
            ), "")

    def test_chinese_history_translation_exception_is_not_agent_permission(self):
        policy = promotion.community_policy(
            "reddit", "https://www.reddit.com/r/ChineseHistory/comments/example/request/",
        )
        self.assertFalse(policy["agent_public_reply_allowed"])
        self.assertFalse(policy["agent_private_contact_allowed"])
        self.assertIn("own original writing", policy["reason"])
        self.assertIn("another author's classic", policy["reason"])
        self.assertEqual(promotion.community_policy(
            "reddit", "https://www.reddit.com/r/ChineseHistoryBooks/comments/example/request/",
        ), {})


if __name__ == "__main__":
    unittest.main()
