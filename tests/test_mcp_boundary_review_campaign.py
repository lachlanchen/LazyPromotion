import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "mcp-boundary-review.json"
SCOPE_TEMPLATE = ROOT / "docs" / "mcp-review-scope-template.md"
PACKET = (
    ROOT
    / "examples"
    / "mcp-boundary-review"
    / "artifacts"
    / "lkt-mcp-boundary-review-sample.zip"
)
COVER = ROOT / "assets" / "contra-mcp-boundary-review-cover-v1.png"


class McpBoundaryReviewCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_two_bounded_reviews_reach_target_without_inventing_revenue(self):
        self.assertEqual(self.payload["version"], 34)
        self.assertIn("2 paid reviews x USD 500", self.payload["strategy"]["target_math"])
        offer = self.payload["offer"]
        self.assertEqual(offer["price"], "USD 500")
        self.assertEqual(offer["base_repository_revision_limit"], 1)
        self.assertEqual(offer["follow_up_successor_revision_limit"], 1)
        self.assertEqual(offer["follow_up_failed_check_limit"], 3)
        self.assertEqual(offer["mcp_server_limit"], 1)
        self.assertEqual(offer["tool_and_resource_limit"], 8)
        self.assertEqual(offer["protocol_check_limit"], 10)
        self.assertEqual(len(offer["default_check_set"]), 10)
        self.assertIn("result handoff", offer["default_check_set"][2])
        self.assertIn("intended client", offer["default_check_set"][3])
        self.assertIn("up to three checks", offer["follow_up_recheck"])
        self.assertEqual(sum(offer["deliverable_allocation_usd"].values()), 500)
        self.assertEqual(self.payload["funnel"]["received_revenue_usd"], 0)

    def test_public_repository_preflight_is_static_private_and_not_a_sale(self):
        preflight = self.payload["public_repository_preflight_generator"]
        self.assertEqual(preflight["state"], "live_public_offer_exposed_verified")
        self.assertEqual(preflight["script"], "mcp_public_preflight.py")
        self.assertEqual(
            preflight["source_revision"],
            "8b06e0bfb6485dc30fa15f425c37394bb1dd223c",
        )
        self.assertIn("explicit GitHub API GET", preflight["method"])
        self.assertIn("owner-only", preflight["output"].casefold())
        self.assertFalse(preflight["live_sample"]["repository_code_executed"])
        self.assertEqual(preflight["live_sample"]["detected_tools"], 2)
        self.assertEqual(preflight["live_sample"]["detected_resources"], 1)
        self.assertEqual(preflight["landing_exposure"]["state"], "live_verified")
        self.assertIn("#preflight", preflight["landing_exposure"]["url"])
        self.assertIn("preflight-sample", preflight["landing_exposure"]["sample_url"])
        self.assertTrue(preflight["landing_exposure"]["sample_markdown"].endswith("report.md"))
        self.assertEqual(len(preflight["landing_exposure"]["sample_markdown_sha256"]), 64)
        self.assertEqual(len(preflight["landing_exposure"]["paths"]), 4)
        self.assertIn("free scoping aid", preflight["boundary"])
        self.assertFalse(self.payload["funnel"]["payment_confirmed"])

    def test_offer_preserves_security_and_data_boundaries(self):
        offer = self.payload["offer"]
        excluded = " ".join(offer["excluded"]).casefold()
        self.assertIn("penetration testing", excluded)
        self.assertIn("security certification", excluded)
        self.assertIn("production secrets", excluded)
        self.assertIn("not a public self-serve checkout", offer["payment_policy"].casefold())
        self.assertIn("metadata only", offer["data_policy"].casefold())

    def test_executed_public_packet_is_pinned_and_integral(self):
        proof = self.payload["public_proof"]
        self.assertEqual(proof["revision"], "e750e5ae24b780e45de896f7dc3a769d2410dabd")
        self.assertEqual(proof["observed"]["focused_tests_passed"], 14)
        self.assertEqual(proof["observed"]["tools"], 2)
        self.assertEqual(proof["observed"]["resources"], 1)
        self.assertEqual(proof["observed"]["prompts"], 0)
        self.assertIn("NO-GO for direct remote exposure", proof["decision"])
        self.assertEqual(
            proof["packet"]["sha256"],
            hashlib.sha256(PACKET.read_bytes()).hexdigest(),
        )
        self.assertTrue(proof["packet"]["live_byte_identical"])

    def test_demand_is_separate_from_selection_or_sales(self):
        self.assertEqual(len(self.payload["demand_evidence"]), 5)
        self.assertTrue(
            all(item["source"].startswith("https://") for item in self.payload["demand_evidence"])
        )
        self.assertFalse(self.payload["intake"]["lead_or_sale_observed"])
        self.assertFalse(self.payload["funnel"]["qualified_lead_observed"])
        self.assertFalse(self.payload["funnel"]["payment_confirmed"])
        latest = self.payload["demand_evidence"][-1]
        self.assertIn("/r/mcp/", latest["source"])
        self.assertIn("large read-only result", latest["need"])
        self.assertIn("not a buyer inquiry", latest["boundary"])

    def test_upwork_mcp_role_is_not_mistaken_for_an_autonomous_route(self):
        route = self.payload["channels"]["upwork_mcp_expert"]
        self.assertIn("personal_interview", route["state"])
        self.assertEqual(route["published_rate"], "USD 60–120 per hour")
        self.assertFalse(route["low_involvement_fit"])
        self.assertFalse(route["application_submitted"])
        self.assertEqual(route["connects_spent"], 0)
        self.assertIn("Do not guess personal experience", route["policy"])

    def test_contextual_github_reply_is_exact_and_not_a_lead(self):
        replies = self.payload["channels"]["community_replies"]
        self.assertEqual(
            replies["state"],
            "two_github_reviews_and_three_reddit_architecture_replies",
        )
        item = replies["github_bos_egress_decision"]
        self.assertIn("#issuecomment-", item["public_reply"])
        self.assertEqual(item["reviewed_body_sha256"], item["live_body_sha256"])
        self.assertTrue(item["exact_body_verified"])
        self.assertIn("not an audit of BOS", item["sample_disclosure"])
        monitor = item["reply_monitor"]
        self.assertEqual(monitor["state"], "active_and_baselined")
        self.assertEqual(monitor["thread"], "arjun-techjays/bos#18")
        self.assertFalse(monitor["body_or_comment_text_requested"])
        self.assertFalse(monitor["automatic_reply"])
        self.assertEqual(monitor["baseline_comment_count"], 2)
        self.assertEqual(monitor["alerts_after_baseline"], 0)
        self.assertFalse(item["reply_received"])
        self.assertFalse(item["lead_or_sale_observed"])
        self.assertEqual(item["verified_received_gross_usd"], 0)
        self.assertIn("not automated outreach", item["policy"])
        second = replies["github_azkena_auth_boundary"]
        self.assertIn("#issuecomment-", second["public_reply"])
        self.assertEqual(second["reviewed_body_sha256"], second["live_body_sha256"])
        self.assertTrue(second["exact_body_verified"])
        self.assertFalse(second["owned_link_included"])
        self.assertEqual(second["reply_monitor"]["state"], "active_and_baselined")
        self.assertFalse(second["reply_monitor"]["body_or_comment_text_requested"])
        self.assertFalse(second["reply_monitor"]["automatic_reply"])
        self.assertEqual(second["reply_monitor"]["baseline_comment_count"], 1)
        self.assertEqual(second["reply_monitor"]["alerts_after_baseline"], 0)
        self.assertFalse(second["reply_received"])
        self.assertFalse(second["lead_or_sale_observed"])
        self.assertEqual(second["verified_received_gross_usd"], 0)
        third = replies["reddit_kin_graph_design"]
        self.assertIn("/r/mcp/", third["public_reply"])
        self.assertEqual(third["reviewed_body_sha256"], third["live_body_sha256"])
        self.assertTrue(third["exact_body_verified"])
        self.assertFalse(third["owned_link_included"])
        self.assertFalse(third["project_or_offer_named"])
        self.assertEqual(
            third["reply_monitor"]["state"],
            "visible_baseline_no_direct_reply",
        )
        self.assertFalse(third["reply_monitor"]["body_or_comment_text_requested"])
        self.assertFalse(third["reply_monitor"]["automatic_reply"])
        self.assertTrue(third["reply_monitor"]["baseline_created"])
        self.assertEqual(third["reply_monitor"]["current_direct_reply_count"], 0)
        self.assertFalse(third["reply_received"])
        self.assertFalse(third["lead_or_sale_observed"])
        self.assertEqual(third["verified_received_gross_usd"], 0)
        fourth = replies["reddit_cross_client_memory"]
        self.assertIn("/r/mcp/", fourth["public_reply"])
        self.assertEqual(fourth["reviewed_body_sha256"], fourth["live_body_sha256"])
        self.assertTrue(fourth["exact_body_verified"])
        self.assertFalse(fourth["owned_link_included"])
        self.assertFalse(fourth["project_or_offer_named"])
        self.assertFalse(fourth["reply_received"])
        self.assertFalse(fourth["lead_or_sale_observed"])
        self.assertEqual(fourth["verified_received_gross_usd"], 0)
        fifth = replies["reddit_knx_result_handoff"]
        self.assertIn("/r/mcp/", fifth["public_reply"])
        self.assertEqual(fifth["reviewed_body_sha256"], fifth["live_body_sha256"])
        self.assertTrue(fifth["exact_body_verified"])
        self.assertFalse(fifth["owned_link_included"])
        self.assertFalse(fifth["project_or_offer_named"])
        self.assertFalse(fifth["reply_received"])
        self.assertFalse(fifth["lead_or_sale_observed"])
        self.assertEqual(fifth["verified_received_gross_usd"], 0)

    def test_price_is_validated_without_becoming_a_security_claim(self):
        validation = self.payload["market_validation"]
        self.assertIn("Keep USD 500", validation["decision"])
        self.assertEqual(len(validation["benchmarks"]), 3)
        self.assertTrue(all(item["source"].startswith("https://") for item in validation["benchmarks"]))
        self.assertIn("pre-deployment evidence", validation["decision"])

    def test_payment_path_is_guarded_and_non_mutating(self):
        payment = self.payload["payment_readiness"]
        self.assertEqual(payment["state"], "ready_for_reviewed_live_request")
        self.assertEqual(payment["price"], "USD 500")
        self.assertEqual(payment["quantity"], 1)
        self.assertEqual(payment["fulfillment_review_notes"], 9)
        self.assertFalse(payment["public_payment_link"])
        self.assertEqual(payment["scope_template"], "docs/mcp-review-scope-template.md")
        self.assertIn("No Product", payment["read_only_account_check"])

    def test_scope_template_is_customer_ready_without_weakening_the_offer(self):
        text = SCOPE_TEMPLATE.read_text(encoding="utf-8")
        offer = self.payload["offer"]
        self.assertIn("**USD 500**", text)
        self.assertIn("no more than eight tools and resources", text)
        self.assertIn("## Ten agreed checks", text)
        self.assertIn("within seven business days", text.casefold())
        self.assertIn("Within fourteen calendar days", text)
        self.assertIn("up to three checks", text)
        self.assertIn("not a guarantee", text)
        self.assertIn("no public\nself-serve checkout", text)
        allocations = offer["deliverable_allocation_usd"]
        self.assertEqual(sum(allocations.values()), 500)
        for amount in allocations.values():
            self.assertIn(f"USD {amount}", text)
        self.assertIn("[scope ID and version]", text)

    def test_live_intake_round_trip_is_verified_without_claiming_a_lead(self):
        intake = self.payload["intake"]
        self.assertEqual(intake["state"], "live_verified")
        self.assertTrue(intake["review_before_send"])
        self.assertTrue(intake["receiver_authenticated_decrypted_and_saved"])
        self.assertTrue(intake["remote_spool_empty"])
        self.assertEqual(len(intake["required_buyer_inputs"]), 3)
        self.assertIn("public GitHub repository URL", intake["required_buyer_inputs"])
        self.assertEqual(len(intake["private_repository_additional_inputs"]), 2)
        self.assertIn("client and transport", intake["private_repository_additional_inputs"][0])
        self.assertEqual(
            intake["backend_commit"],
            "df140bfbccc035ec05eabc076af25b0557983c66",
        )
        self.assertIn("PHP 8.2", intake["deployment_verification"])
        self.assertIn("second receiver pass returned no_pending", intake["live_round_trip"])
        self.assertFalse(intake["lead_or_sale_observed"])

    def test_linkedin_x_instagram_and_reddit_queues_preserve_reviewed_evidence(self):
        postiz = self.payload["channels"]["postiz"]
        self.assertEqual(
            postiz["state"],
            "linkedin_x_instagram_and_reddit_profile_queue_verified",
        )
        self.assertEqual(postiz["publish_at"], "2026-09-16T02:00:00.000Z")
        self.assertIn("14 focused tests", postiz["content"])
        self.assertIn("fixed USD 500 pre-deployment review", postiz["content"])
        self.assertIn("utm_source=linkedin", postiz["destination"])
        self.assertIn("queue volume did not increase", postiz["superseded_post_removed"])
        self.assertIn("September 14 PubMed", postiz["verification"])
        self.assertIn("September 15 lecture-pack", postiz["verification"])
        self.assertIn("only queued LinkedIn publication", postiz["verification"])
        x_post = postiz["x"]
        self.assertEqual(x_post["state"], "queue_verified")
        self.assertEqual(x_post["publish_at"], "2026-09-16T02:00:00.000Z")
        self.assertEqual(x_post["profile"], "lazyingart")
        self.assertEqual(len(x_post["content"]), 251)
        self.assertIn("fixed $500 review", x_post["content"])
        self.assertIn("lazying.art/mcp-boundary-review/sample-report/", x_post["content"])
        self.assertTrue(x_post["settings"]["made_with_ai"])
        self.assertIn("volume did not increase", x_post["replaced_post"])
        self.assertIn("malformed queued record was deleted", x_post["verification"])
        instagram = postiz["instagram"]
        self.assertEqual(instagram["state"], "queue_verified")
        self.assertEqual(instagram["provider"], "instagram-standalone")
        self.assertEqual(instagram["publish_at"], "2026-09-16T04:00:00.000Z")
        self.assertEqual(instagram["profile"], "LazyingArt Lachlan Chen")
        self.assertIn("not the same as private", instagram["content"])
        self.assertIn("fixed USD 500 review", instagram["content"])
        self.assertEqual(
            instagram["content_sha256"],
            hashlib.sha256(instagram["content"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(instagram["settings"]["post_type"], "post")
        self.assertEqual(instagram["media"]["dimensions"], "1200x630")
        self.assertEqual(
            instagram["media"]["source_sha256"],
            instagram["media"]["postiz_sha256"],
        )
        self.assertIn("thirty-two hours", instagram["replaced_or_added_volume"])
        self.assertIn("attention signals only", instagram["analytics_context"])
        reddit = postiz["reddit_profile"]
        self.assertEqual(reddit["state"], "queue_verified")
        self.assertEqual(reddit["provider"], "reddit")
        self.assertEqual(reddit["publish_at"], "2026-09-13T04:00:00.000Z")
        self.assertEqual(reddit["profile"], "Ok-Perception1122")
        self.assertEqual(reddit["settings"]["subreddit"], "/r/u_Ok-Perception1122")
        self.assertEqual(reddit["settings"]["type"], "self")
        self.assertIn("seven small things", reddit["content"])
        self.assertEqual(reddit["content"], reddit["postiz_content"])
        self.assertEqual(
            reddit["content_sha256"],
            hashlib.sha256(reddit["content"].encode("utf-8")).hexdigest(),
        )
        self.assertIn("utm_source=reddit", reddit["destination"])
        self.assertFalse(reddit["shortlink"])
        self.assertIn("owned Reddit profile", reddit["volume_boundary"])
        self.assertIn("not another r/mcp reply", reddit["volume_boundary"])
        self.assertIn("visible Postiz calendar", reddit["verification"])
        self.assertFalse(reddit["lead_or_sale_observed"])
        self.assertEqual(reddit["verified_received_gross_usd"], 0)
        self.assertFalse(postiz["lead_or_sale_observed"])

    def test_contra_listing_preserves_scope_and_revenue_boundaries(self):
        contra = self.payload["contra_marketplace"]
        self.assertEqual(contra["state"], "published_live_verified_identity_and_payout_pending")
        self.assertEqual(contra["price"], "USD 500 one-time")
        self.assertEqual(contra["duration"], "2 weeks")
        self.assertEqual(contra["faq_count"], 3)
        self.assertEqual(len(contra["tags"]), 6)
        self.assertEqual(contra["title"], "MCP Server Pre-Deployment Review")
        self.assertEqual(
            contra["linked_example"],
            "MCP Server Pre-Deployment Review: Executed Sample",
        )
        self.assertIn("up-to-three-failed-check", contra["payment_policy"])
        self.assertIn("stay on Contra", contra["payment_policy"])
        self.assertFalse(contra["identity_verified"])
        self.assertFalse(contra["payout_configured"])
        self.assertFalse(contra["buyer_inquiry_observed"])
        self.assertFalse(contra["payment_observed"])
        self.assertEqual(contra["received_gross_usd"], 0)

    def test_contra_case_is_exact_project_owned_proof(self):
        case = self.payload["contra_marketplace"]["portfolio_case"]
        self.assertEqual(case["state"], "published_live_verified")
        self.assertIn("/p/om7mm3NN-", case["url"])
        self.assertEqual(case["cover_dimensions"], "1600x1200")
        self.assertEqual(
            case["cover_sha256"],
            hashlib.sha256(COVER.read_bytes()).hexdigest(),
        )
        self.assertEqual(case["tools"], ["Git", "GitHub", "Python"])
        self.assertIn("not verified customer work", case["boundary"])

    def test_lazyblog_guide_is_live_without_claiming_attention(self):
        lazyblog = self.payload["channels"]["lazyblog"]
        self.assertEqual(lazyblog["state"], "published_live_verified")
        self.assertEqual(
            lazyblog["source"],
            "articles/review-mcp-server-before-deployment/post.md",
        )
        self.assertIn("/3829/", lazyblog["published_url"])
        self.assertEqual(lazyblog["published_post_id"], 3829)
        self.assertIn("server-local paths", lazyblog["verification"])
        self.assertIn("BLOG publication receipt commit 516e753", lazyblog["verification"])
        self.assertIn("without duplication", lazyblog["verification"])
        self.assertFalse(lazyblog["lead_or_sale_observed"])

    def test_owned_offer_links_the_guide_with_one_exact_boundary(self):
        delivery = self.payload["owned_delivery"]
        self.assertEqual(
            delivery["website_commit"],
            "3fe0f03a6cb39ba05001c7b28a2fa3fa20f2717f",
        )
        self.assertIn("actions/runs/34704612577", delivery["deployment_run"])
        preview = delivery["social_preview"]
        self.assertEqual(preview["state"], "live_verified")
        self.assertEqual(preview["dimensions"], "1200x630")
        self.assertRegex(preview["sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("no customer claim", preview["boundary"])
        conversion = delivery["sample_conversion"]
        self.assertEqual(conversion["state"], "live_verified")
        self.assertEqual(conversion["hero_action"], "Check my server")
        self.assertIn("utm_content=sample_hero", conversion["destination"])
        self.assertEqual(conversion["mobile_viewport"], "390x844")
        self.assertTrue(conversion["above_fold"])
        self.assertFalse(conversion["horizontal_overflow"])
        self.assertEqual(
            conversion["upstream_attribution_preserved"],
            ["utm_source", "utm_medium", "utm_campaign", "utm_content"],
        )
        self.assertRegex(conversion["attribution_bridge_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(len(conversion["public_preflight_required_inputs"]), 3)
        self.assertEqual(len(conversion["private_repository_additional_inputs"]), 2)
        self.assertIn("zero endpoint requests", conversion["public_preflight_live_review"])
        self.assertIn("metadata-only fit check", conversion["boundary"])
        self.assertIn("result-handoff checks", delivery["verification"])
        self.assertIn("above the fold", delivery["verification"])
        self.assertIn("all four Reddit campaign tags", delivery["verification"])

    def test_lkt_readmes_route_mcp_interest_to_exact_proof(self):
        github = self.payload["channels"]["github"]
        self.assertEqual(github["state"], "proof_and_tracked_reader_route")
        self.assertEqual(
            github["readme_route_commit"],
            "625a8d6e4c9ed1e1047ccacff32f982fea959d81",
        )
        self.assertIn("eleven README editions", github["role"])
        self.assertIn("267 repository tests", github["verification"])
        profile = github["profile_route"]
        self.assertEqual(profile["commit"], "0b0080c")
        self.assertEqual(profile["position"], "first service row")
        self.assertIn("utm_campaign=mcp_boundary_review", profile["destination"])
        self.assertIn("up to eight tools and resources", profile["scope"])
        self.assertFalse(profile["attention_or_sale_observed"])


if __name__ == "__main__":
    unittest.main()
