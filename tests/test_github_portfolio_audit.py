import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import github_portfolio_audit as audit


def catalog(*names):
    return {
        "version": 1,
        "owner": "example-owner",
        "visibility": "public",
        "includes_forks": False,
        "repositories": [
            {
                "name": name,
                "url": f"https://github.com/example-owner/{name}",
            }
            for name in names
        ],
    }


class FakeSubprocess:
    def __init__(
        self, *, ignored=True, tracked=False, private_names=(), fail_endpoint=""
    ):
        self.ignored = ignored
        self.tracked = tracked
        self.private_names = set(private_names)
        self.fail_endpoint = fail_endpoint
        self.commands = []

    @staticmethod
    def result(payload=None, returncode=0, stderr=""):
        stdout = payload if isinstance(payload, str) else json.dumps(payload)
        return SimpleNamespace(
            returncode=returncode, stdout=stdout or "", stderr=stderr
        )

    def __call__(self, command, **kwargs):
        self.commands.append((command, kwargs))
        if command[0] == "git":
            if "ls-files" in command:
                return self.result(returncode=0 if self.tracked else 1)
            if "check-ignore" in command:
                return self.result(returncode=0 if self.ignored else 1)
            raise AssertionError(command)

        self._assert_read_only_gh_command(command, kwargs)
        endpoint = command[-1]
        if endpoint == self.fail_endpoint:
            return self.result(returncode=1, stderr="private-token=must-not-leak")
        base, marker, traffic_path = endpoint.partition("/traffic/")
        name = base.rsplit("/", 1)[-1]
        if not marker:
            return self.result(
                {
                    "private": name in self.private_names,
                    "fork": False,
                    "stargazers_count": 10 if name == "Alpha" else 2,
                    "forks_count": 3 if name == "Alpha" else 1,
                    "open_issues_count": 4 if name == "Alpha" else 0,
                }
            )
        if traffic_path == "views":
            return self.result(
                {
                    "count": 30 if name == "Alpha" else 5,
                    "uniques": 8 if name == "Alpha" else 2,
                    "views": [
                        {
                            "timestamp": "2026-09-08T00:00:00Z",
                            "count": 11,
                            "uniques": 4,
                        },
                        {
                            "timestamp": "2026-09-07T00:00:00Z",
                            "count": 19,
                            "uniques": 5,
                        },
                    ],
                }
            )
        if traffic_path == "clones":
            return self.result(
                {
                    "count": 7 if name == "Alpha" else 1,
                    "uniques": 4 if name == "Alpha" else 1,
                    "clones": [
                        {"timestamp": "2026-09-08T00:00:00Z", "count": 7, "uniques": 4}
                    ],
                }
            )
        if traffic_path == "popular/referrers":
            return self.result(
                [
                    {"referrer": "small.test", "count": 2, "uniques": 2},
                    {"referrer": "large.test", "count": 9, "uniques": 5},
                ]
            )
        if traffic_path == "popular/paths":
            return self.result(
                [
                    {
                        "path": f"/{name}/docs",
                        "title": "Docs",
                        "count": 3,
                        "uniques": 2,
                    },
                    {"path": f"/{name}", "title": name, "count": 12, "uniques": 6},
                ]
            )
        raise AssertionError(endpoint)

    @staticmethod
    def _assert_read_only_gh_command(command, kwargs):
        if command[:2] != ["gh", "api"]:
            raise AssertionError(command)
        method_index = command.index("--method")
        if command[method_index + 1] != "GET":
            raise AssertionError(command)
        if kwargs != {
            "text": True,
            "capture_output": True,
            "check": False,
            "timeout": 60,
        }:
            raise AssertionError(kwargs)


class GitHubPortfolioAuditTests(unittest.TestCase):
    def test_build_report_collects_every_catalog_repository_through_get_endpoints(self):
        fake = FakeSubprocess()
        with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
            report = audit.build_report(
                catalog("Alpha", "Beta"), generated_at="2026-09-09T01:02:03Z"
            )

        self.assertEqual(report["repository_count"], 2)
        self.assertEqual(report["generated_at"], "2026-09-09T01:02:03Z")
        self.assertEqual(
            [item["name"] for item in report["repositories"]], ["Alpha", "Beta"]
        )
        self.assertEqual(len(fake.commands), 10)
        endpoints = [command[-1] for command, _ in fake.commands]
        for name in ("Alpha", "Beta"):
            base = f"repos/example-owner/{name}"
            self.assertEqual(
                endpoints.count(base)
                + endpoints.count(f"{base}/traffic/views")
                + endpoints.count(f"{base}/traffic/clones")
                + endpoints.count(f"{base}/traffic/popular/referrers")
                + endpoints.count(f"{base}/traffic/popular/paths"),
                5,
            )
        self.assertTrue(all("--method" in command for command, _ in fake.commands))
        self.assertTrue(
            all(
                command[command.index("--method") + 1] == "GET"
                for command, _ in fake.commands
            )
        )

    def test_report_preserves_aggregate_rollups_and_sorted_summaries(self):
        fake = FakeSubprocess()
        with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
            report = audit.build_report(catalog("Alpha"))

        repository = report["repositories"][0]
        self.assertEqual(
            repository["public_metrics"], {"stars": 10, "forks": 3, "open_issues": 4}
        )
        views = repository["owner_visible_traffic"]["views"]
        clones = repository["owner_visible_traffic"]["clones"]
        self.assertEqual((views["count"], views["unique_visitors"]), (30, 8))
        self.assertEqual((clones["count"], clones["unique_cloners"]), (7, 4))
        self.assertEqual(views["window_starts_at"], "2026-09-07T00:00:00Z")
        self.assertEqual(views["window_ends_at"], "2026-09-08T00:00:00Z")
        self.assertEqual(
            repository["owner_visible_traffic"]["top_referrers"][0]["referrer"],
            "large.test",
        )
        self.assertEqual(
            repository["owner_visible_traffic"]["top_paths"][0]["path"], "/Alpha"
        )

    def test_ranking_is_attention_only_and_deterministic(self):
        fake = FakeSubprocess()
        with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
            report = audit.build_report(catalog("Beta", "Alpha"))

        self.assertEqual(report["repositories"][0]["attention_rank"], 1)
        self.assertGreater(
            report["repositories"][0]["attention_score"],
            report["repositories"][1]["attention_score"],
        )
        interpretation = report["interpretation"]
        self.assertEqual(
            interpretation["classification"], "relative_portfolio_attention_signal"
        )
        self.assertFalse(interpretation["traffic_is_lead_evidence"])
        self.assertFalse(interpretation["traffic_is_customer_evidence"])
        self.assertFalse(interpretation["traffic_is_sales_evidence"])
        self.assertFalse(interpretation["traffic_is_revenue_evidence"])
        self.assertNotIn("lead_count", json.dumps(report))
        self.assertNotIn("revenue_usd", json.dumps(report))

    def test_private_repository_response_is_refused_before_traffic_calls(self):
        fake = FakeSubprocess(private_names={"Secret"})
        with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(ValueError, "non-public repository"):
                audit.build_report(catalog("Secret"))

        self.assertEqual(len(fake.commands), 1)
        self.assertEqual(fake.commands[0][0][-1], "repos/example-owner/Secret")

    def test_api_failure_does_not_expose_cli_stderr(self):
        endpoint = "repos/example-owner/Alpha/traffic/views"
        fake = FakeSubprocess(fail_endpoint=endpoint)
        with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
            with self.assertRaises(RuntimeError) as raised:
                audit.build_report(catalog("Alpha"))

        self.assertIn(endpoint, str(raised.exception))
        self.assertNotIn("must-not-leak", str(raised.exception))
        self.assertNotIn("private-token", str(raised.exception))

    def test_output_must_be_json_inside_repo_untracked_and_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / ".local" / "evidence" / "audit.json"
            accepted = FakeSubprocess()
            with mock.patch(
                "github_portfolio_audit.subprocess.run", side_effect=accepted
            ):
                self.assertEqual(
                    audit.validate_private_output_path(output, root=root),
                    output.resolve(),
                )
            self.assertEqual(len(accepted.commands), 2)
            self.assertIn("ls-files", accepted.commands[0][0])
            self.assertIn("check-ignore", accepted.commands[1][0])

            tracked = FakeSubprocess(tracked=True)
            with mock.patch(
                "github_portfolio_audit.subprocess.run", side_effect=tracked
            ):
                with self.assertRaisesRegex(ValueError, "must not be tracked"):
                    audit.validate_private_output_path(output, root=root)

            visible = FakeSubprocess(ignored=False)
            with mock.patch(
                "github_portfolio_audit.subprocess.run", side_effect=visible
            ):
                with self.assertRaisesRegex(ValueError, "must be ignored"):
                    audit.validate_private_output_path(output, root=root)

            with self.assertRaisesRegex(ValueError, "inside the repository"):
                audit.validate_private_output_path(
                    root.parent / "audit.json", root=root
                )
            with self.assertRaisesRegex(ValueError, "JSON file"):
                audit.validate_private_output_path(
                    root / ".local" / "audit.txt", root=root
                )
            output.parent.mkdir(parents=True)
            target = output.parent / "target.json"
            target.write_text("{}", encoding="utf-8")
            output.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                audit.validate_private_output_path(output, root=root)

    def test_run_audit_writes_only_final_private_file_with_owner_permissions(self):
        fake = FakeSubprocess()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = root / "github-repos.json"
            catalog_path.write_text(json.dumps(catalog("Alpha")), encoding="utf-8")
            output = root / ".local" / "evidence" / "audit.json"
            with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
                report = audit.run_audit(
                    output_path=output,
                    catalog_path=catalog_path,
                    root=root,
                    generated_at="2026-09-09T01:02:03Z",
                )

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            files = sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            )
            self.assertEqual(files, [".local/evidence/audit.json", "github-repos.json"])
            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn("private-token", serialized)
            self.assertFalse(report["scope"]["credentials_stored"])

    def test_collection_failure_preserves_an_existing_private_report(self):
        endpoint = "repos/example-owner/Alpha/traffic/clones"
        fake = FakeSubprocess(fail_endpoint=endpoint)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = root / "github-repos.json"
            catalog_path.write_text(json.dumps(catalog("Alpha")), encoding="utf-8")
            output = root / ".local" / "evidence" / "audit.json"
            output.parent.mkdir(parents=True)
            output.write_text("previous complete report\n", encoding="utf-8")
            with mock.patch("github_portfolio_audit.subprocess.run", side_effect=fake):
                with self.assertRaises(RuntimeError):
                    audit.run_audit(
                        output_path=output,
                        catalog_path=catalog_path,
                        root=root,
                    )

            self.assertEqual(
                output.read_text(encoding="utf-8"), "previous complete report\n"
            )

    def test_catalog_rejects_forks_nonpublic_visibility_and_duplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalog.json"
            cases = []
            fork_catalog = catalog("Alpha")
            fork_catalog["includes_forks"] = True
            cases.append((fork_catalog, "source repositories only"))
            private_catalog = catalog("Alpha")
            private_catalog["visibility"] = "private"
            cases.append((private_catalog, "only public"))
            duplicate_catalog = catalog("Alpha", "alpha")
            cases.append((duplicate_catalog, "duplicate repository"))
            empty_catalog = catalog()
            cases.append((empty_catalog, "non-empty list"))
            mismatched_url_catalog = catalog("Alpha")
            mismatched_url_catalog["repositories"][0]["url"] = (
                "https://github.com/example-owner/Beta"
            )
            cases.append((mismatched_url_catalog, "does not match catalog owner"))
            for payload, message in cases:
                with self.subTest(message=message):
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        audit.load_catalog(path)

    def test_boolean_or_negative_counts_are_not_accepted_as_metrics(self):
        for value in (True, -1, 1.5, "2"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    audit._nonnegative_int(value, "metric")


if __name__ == "__main__":
    unittest.main()
