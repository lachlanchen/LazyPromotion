import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import github_inbound_monitor as monitor


def issue(repository, number, *, title=None):
    return {
        "number": number,
        "title": title or f"Issue {number}",
        "url": f"https://github.com/{monitor.OWNER}/{repository}/issues/{number}",
        "state": "OPEN",
        "createdAt": f"2026-09-{number:02d}T01:02:03Z",
        "updatedAt": f"2026-09-{number:02d}T02:03:04Z",
        "author": {"login": f"person-{number}"},
    }


def pull_request(
    repository,
    number,
    *,
    title=None,
    updated_at=None,
    comment_count=0,
    review_count=0,
):
    return {
        "number": number,
        "title": title or f"Pull request {number}",
        "url": f"https://github.com/{monitor.OWNER}/{repository}/pull/{number}",
        "state": "OPEN",
        "isDraft": False,
        "createdAt": f"2026-09-{number:02d}T01:02:03Z",
        "updatedAt": updated_at or f"2026-09-{number:02d}T02:03:04Z",
        "author": {"login": f"contributor-{number}"},
        "comments": {"totalCount": comment_count},
        "reviews": {"totalCount": review_count},
    }


def external_issue(
    owner,
    repository,
    number,
    *,
    updated_at="2026-09-12T12:19:01Z",
    comment_count=2,
    state="OPEN",
):
    return {
        "number": number,
        "title": "Remote MCP servers, unauthenticated: decide the egress path",
        "url": f"https://github.com/{owner}/{repository}/issues/{number}",
        "state": state,
        "updatedAt": updated_at,
        "comments": {"totalCount": comment_count},
    }


def graphql_payload(
    issues_by_repository=None,
    *,
    pull_requests_by_repository=None,
    visibility_by_repository=None,
    external_issues=None,
    external_visibility=None,
):
    issues_by_repository = issues_by_repository or {}
    pull_requests_by_repository = pull_requests_by_repository or {}
    visibility_by_repository = visibility_by_repository or {}
    external_issues = external_issues or {}
    external_visibility = external_visibility or {}
    data = {}
    for index, name in enumerate(monitor.REPOSITORIES):
        issues = issues_by_repository.get(name, [])
        data[f"repo{index}"] = {
            "nameWithOwner": f"{monitor.OWNER}/{name}",
            "visibility": visibility_by_repository.get(name, "PUBLIC"),
            "issues": {
                "totalCount": len(issues),
                "pageInfo": {"hasNextPage": False},
                "nodes": issues,
            },
            "pullRequests": {
                "totalCount": len(pull_requests_by_repository.get(name, [])),
                "pageInfo": {"hasNextPage": False},
                "nodes": pull_requests_by_repository.get(name, []),
            },
        }
    for index, (owner, repository, number) in enumerate(monitor.EXTERNAL_ISSUES):
        key = monitor.external_thread_key(owner, repository, number)
        data[f"external{index}"] = {
            "nameWithOwner": f"{owner}/{repository}",
            "visibility": external_visibility.get(key, "PUBLIC"),
            "issue": external_issues.get(
                key, external_issue(owner, repository, number)
            ),
        }
    return {"data": data}


class FakeRunner:
    def __init__(self, payloads, *, ignored=True, tracked=False, gh_failure=False):
        self.payloads = list(payloads)
        self.ignored = ignored
        self.tracked = tracked
        self.gh_failure = gh_failure
        self.commands = []

    @staticmethod
    def result(payload=None, *, returncode=0, stderr=""):
        stdout = payload if isinstance(payload, str) else json.dumps(payload)
        return SimpleNamespace(
            returncode=returncode,
            stdout=stdout or "",
            stderr=stderr,
        )

    def __call__(self, command, **kwargs):
        self.commands.append((command, kwargs))
        if command[0] == "git":
            if "ls-files" in command:
                return self.result(returncode=0 if self.tracked else 1)
            if "check-ignore" in command:
                return self.result(returncode=0 if self.ignored else 1)
            raise AssertionError(command)
        if command[:3] != ["gh", "api", "graphql"]:
            raise AssertionError(command)
        if kwargs != {
            "text": True,
            "capture_output": True,
            "check": False,
            "timeout": 60,
        }:
            raise AssertionError(kwargs)
        if self.gh_failure:
            return self.result(
                returncode=1,
                stderr="token and account details must not escape",
            )
        return self.result(self.payloads.pop(0))


class GitHubInboundMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = self.root / ".local" / "github-inbound-status.json"

    def tearDown(self):
        self.temporary.cleanup()

    def test_one_fixed_graphql_query_has_no_bodies_or_mutation(self):
        fake = FakeRunner([graphql_payload()])
        observation = monitor.fetch_public_issues(runner=fake)

        self.assertEqual(len(observation["repositories"]), len(monitor.REPOSITORIES))
        gh_commands = [item for item in fake.commands if item[0][0] == "gh"]
        self.assertEqual(len(gh_commands), 1)
        command, _ = gh_commands[0]
        self.assertEqual(command[:3], ["gh", "api", "graphql"])
        self.assertEqual(command[command.index("--method") + 1], "POST")
        query_arg = next(value for value in command if value.startswith("query="))
        query = query_arg.removeprefix("query=")
        self.assertTrue(query.lstrip().startswith("query "))
        self.assertNotIn("mutation", query.casefold())
        self.assertNotIn("body", query.casefold())
        self.assertIn("pullRequests", query)
        self.assertIn("comments { totalCount }", query)
        self.assertIn("reviews { totalCount }", query)
        self.assertIn("issue(number: 18)", query)
        self.assertIn("issue(number: 14)", query)
        self.assertIn("issue(number: 10)", query)
        self.assertNotIn("comments { nodes", query)
        for name in monitor.REPOSITORIES:
            self.assertIn(json.dumps(name), query)

    def test_external_issue_is_baselined_then_activity_alerts_without_body(self):
        owner, repository, number = monitor.EXTERNAL_ISSUES[0]
        key = monitor.external_thread_key(owner, repository, number)
        baseline = graphql_payload()
        changed = graphql_payload(
            external_issues={
                key: external_issue(
                    owner,
                    repository,
                    number,
                    updated_at="2026-09-12T13:00:00Z",
                    comment_count=3,
                )
            }
        )
        fake = FakeRunner([baseline, changed])

        first = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-12T12:30:00Z",
        )
        self.assertEqual(first["alerts"], [])
        self.assertEqual(
            first["external_thread_allowlist"],
            [monitor.external_thread_key(*item) for item in monitor.EXTERNAL_ISSUES],
        )
        self.assertEqual(
            first["summary"]["external_threads_checked"],
            len(monitor.EXTERNAL_ISSUES),
        )

        second = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-12T13:15:00Z",
        )
        self.assertEqual(len(second["alerts"]), 1)
        alert = second["alerts"][0]
        self.assertEqual(alert["kind"], "external_public_issue_activity_observed")
        self.assertEqual(alert["key"], key)
        self.assertEqual(alert["comment_count"], 3)
        self.assertEqual(second["summary"]["external_thread_alerts"], 1)
        serialized = self.state.read_text(encoding="utf-8").casefold()
        self.assertNotIn('"body"', serialized)
        self.assertFalse(
            second["policy"]["external_issue_activity_is_lead_evidence"]
        )
        self.assertFalse(
            second["policy"]["external_issue_activity_is_revenue_evidence"]
        )

    def test_nonpublic_external_issue_is_rejected(self):
        owner, repository, number = monitor.EXTERNAL_ISSUES[0]
        key = monitor.external_thread_key(owner, repository, number)
        fake = FakeRunner(
            [graphql_payload(external_visibility={key: "PRIVATE"})]
        )
        with self.assertRaisesRegex(ValueError, "non-public external"):
            monitor.fetch_public_issues(runner=fake)

    def test_build_state_rejects_external_issue_outside_fixed_allowlist(self):
        observation = monitor.fetch_public_issues(
            runner=FakeRunner([graphql_payload()])
        )
        observation["external_threads"][0]["key"] = "someone/else#99"
        with self.assertRaisesRegex(ValueError, "fixed allowlist"):
            monitor.build_state(observation, None)

    def test_nonpublic_repository_response_is_rejected(self):
        private_name = monitor.REPOSITORIES[-1]
        fake = FakeRunner(
            [
                graphql_payload(
                    {monitor.REPOSITORIES[0]: [issue(monitor.REPOSITORIES[0], 1)]},
                    visibility_by_repository={private_name: "PRIVATE"},
                )
            ]
        )
        with self.assertRaisesRegex(ValueError, "non-public"):
            monitor.fetch_public_issues(runner=fake)

    def test_baseline_then_only_new_key_alerts_and_seen_keys_are_preserved(self):
        first_name = monitor.REPOSITORIES[0]
        baseline = graphql_payload({first_name: [issue(first_name, 1)]})
        second = graphql_payload(
            {first_name: [issue(first_name, 2), issue(first_name, 1)]}
        )
        fake = FakeRunner([baseline, second])

        first = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-09T01:00:00Z",
        )
        self.assertTrue(first["baseline_created"])
        self.assertEqual(first["alerts"], [])
        self.assertEqual(first["seen_issue_keys"], [monitor.issue_key(first_name, 1)])

        second_report = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-09T01:15:00Z",
        )
        self.assertFalse(second_report["baseline_created"])
        self.assertEqual(
            [alert["key"] for alert in second_report["alerts"]],
            [monitor.issue_key(first_name, 2)],
        )
        self.assertEqual(
            second_report["seen_issue_keys"],
            [monitor.issue_key(first_name, 1), monitor.issue_key(first_name, 2)],
        )
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        serialized = self.state.read_text(encoding="utf-8").casefold()
        self.assertNotIn('"body"', serialized)
        self.assertFalse(second_report["policy"]["issue_is_lead_evidence"])
        self.assertFalse(second_report["policy"]["issue_is_revenue_evidence"])
        self.assertFalse(second_report["policy"]["github_mutations_performed"])

    def test_pull_requests_are_baselined_then_new_and_updated_activity_alerts(self):
        repository = monitor.REPOSITORIES[0]
        first_pull_request = pull_request(repository, 11)
        fake = FakeRunner(
            [
                graphql_payload(
                    pull_requests_by_repository={repository: [first_pull_request]}
                ),
                graphql_payload(
                    pull_requests_by_repository={
                        repository: [
                            pull_request(
                                repository,
                                11,
                                updated_at="2026-09-11T03:03:04Z",
                                review_count=1,
                            ),
                            pull_request(repository, 12),
                        ]
                    }
                ),
            ]
        )

        baseline = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-11T02:15:00Z",
        )
        self.assertEqual(baseline["alerts"], [])
        self.assertEqual(
            baseline["seen_pull_request_keys"],
            [monitor.pull_request_key(repository, 11)],
        )

        changed = monitor.monitor_once(
            state_path=self.state,
            root=self.root,
            runner=fake,
            checked_at="2026-09-11T03:15:00Z",
        )
        self.assertEqual(
            [alert["kind"] for alert in changed["alerts"]],
            [
                "public_pull_request_activity_observed",
                "new_public_pull_request_observed",
            ],
        )
        self.assertEqual(changed["summary"]["pull_request_alerts"], 2)
        self.assertEqual(changed["summary"]["pull_requests_in_current_windows"], 2)
        self.assertFalse(changed["policy"]["pull_request_is_lead_evidence"])
        self.assertFalse(changed["policy"]["pull_request_is_revenue_evidence"])
        serialized = self.state.read_text(encoding="utf-8").casefold()
        self.assertNotIn('"body"', serialized)

    def test_existing_issue_only_state_migrates_without_pull_request_alert_storm(self):
        repository = monitor.REPOSITORIES[0]
        previous = {
            "version": 1,
            "initialized": True,
            "owner": monitor.OWNER,
            "repository_allowlist": list(monitor.REPOSITORIES),
            "seen_issue_keys": [],
        }
        report = monitor.build_state(
            monitor.fetch_public_issues(
                runner=FakeRunner(
                    [
                        graphql_payload(
                            pull_requests_by_repository={
                                repository: [pull_request(repository, 11)]
                            }
                        )
                    ]
                )
            ),
            previous,
        )
        self.assertEqual(report["alerts"], [])
        self.assertEqual(
            report["seen_pull_request_keys"],
            [monitor.pull_request_key(repository, 11)],
        )

    def test_seen_state_survives_an_issue_leaving_the_current_window(self):
        repository = monitor.REPOSITORIES[0]
        previous = {
            "version": 1,
            "initialized": True,
            "owner": monitor.OWNER,
            "repository_allowlist": list(monitor.REPOSITORIES),
            "seen_issue_keys": [monitor.issue_key(repository, 1)],
        }
        observation = monitor.fetch_public_issues(
            runner=FakeRunner([graphql_payload()])
        )
        report = monitor.build_state(observation, previous)
        self.assertEqual(report["seen_issue_keys"], [monitor.issue_key(repository, 1)])
        self.assertEqual(report["alerts"], [])

    def test_appended_public_repository_is_baselined_without_losing_seen_history(self):
        previous_repository = monitor.REPOSITORIES[0]
        appended_repository = monitor.REPOSITORIES[-1]
        previous = {
            "version": 1,
            "initialized": True,
            "owner": monitor.OWNER,
            "repository_allowlist": list(monitor.REPOSITORIES[:-1]),
            "seen_issue_keys": [monitor.issue_key(previous_repository, 1)],
        }
        monitor.write_private_json(self.state, previous, root=self.root)
        loaded = monitor.load_state(self.state)
        self.assertEqual(loaded["repository_allowlist"], list(monitor.REPOSITORIES[:-1]))

        observation = monitor.fetch_public_issues(
            runner=FakeRunner(
                [
                    graphql_payload(
                        {
                            previous_repository: [issue(previous_repository, 1)],
                            appended_repository: [issue(appended_repository, 2)],
                        }
                    )
                ]
            )
        )
        expanded = monitor.build_state(observation, loaded)
        self.assertEqual(expanded["allowlist_expanded"], [appended_repository])
        self.assertEqual(expanded["alerts"], [])
        self.assertEqual(
            expanded["seen_issue_keys"],
            [
                monitor.issue_key(previous_repository, 1),
                monitor.issue_key(appended_repository, 2),
            ],
        )

        later_observation = monitor.fetch_public_issues(
            runner=FakeRunner(
                [
                    graphql_payload(
                        {
                            previous_repository: [issue(previous_repository, 1)],
                            appended_repository: [
                                issue(appended_repository, 2),
                                issue(appended_repository, 3),
                            ],
                        }
                    )
                ]
            )
        )
        later = monitor.build_state(later_observation, expanded)
        self.assertEqual(
            [alert["key"] for alert in later["alerts"]],
            [monitor.issue_key(appended_repository, 3)],
        )

    def test_failed_query_preserves_existing_state_and_sanitizes_cli_error(self):
        repository = monitor.REPOSITORIES[0]
        good = FakeRunner([graphql_payload({repository: [issue(repository, 1)]})])
        monitor.monitor_once(state_path=self.state, root=self.root, runner=good)
        before = self.state.read_bytes()
        failing = FakeRunner([], gh_failure=True)
        with self.assertRaisesRegex(RuntimeError, "GraphQL query failed") as raised:
            monitor.monitor_once(
                state_path=self.state,
                root=self.root,
                runner=failing,
            )
        self.assertEqual(self.state.read_bytes(), before)
        self.assertNotIn("token", str(raised.exception).casefold())
        self.assertNotIn("account", str(raised.exception).casefold())

    def test_state_path_is_restricted_ignored_untracked_and_not_linked(self):
        accepted = FakeRunner([])
        self.assertEqual(
            monitor.validate_state_path(self.state, root=self.root, runner=accepted),
            self.state,
        )
        with self.assertRaisesRegex(ValueError, r"\.local"):
            monitor.validate_state_path(
                self.root / "public.json",
                root=self.root,
                runner=accepted,
            )
        with self.assertRaisesRegex(ValueError, "inside"):
            monitor.validate_state_path(
                self.root.parent / "outside.json",
                root=self.root,
                runner=accepted,
            )
        with self.assertRaisesRegex(ValueError, "JSON"):
            monitor.validate_state_path(
                self.root / ".local" / "state.txt",
                root=self.root,
                runner=accepted,
            )

        tracked = FakeRunner([], tracked=True)
        with self.assertRaisesRegex(ValueError, "not be tracked"):
            monitor.validate_state_path(self.state, root=self.root, runner=tracked)
        visible = FakeRunner([], ignored=False)
        with self.assertRaisesRegex(ValueError, "must be ignored"):
            monitor.validate_state_path(self.state, root=self.root, runner=visible)

        target = self.root / "actual-local"
        target.mkdir()
        (self.root / ".local").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            monitor.validate_state_path(self.state, root=self.root, runner=accepted)

    def test_loop_rejects_intervals_shorter_than_fifteen_minutes(self):
        with self.assertRaisesRegex(ValueError, "at least 15"):
            monitor.monitor_loop(
                14,
                state_path=self.state,
                root=self.root,
                runner=FakeRunner([]),
            )


class GitHubInboundWrapperTests(unittest.TestCase):
    def test_wrapper_is_valid_single_session_launcher(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "github-inbound-monitor.sh"
        completed = subprocess.run(
            ["bash", "-n", str(script)], capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = script.read_text(encoding="utf-8")
        self.assertIn('SESSION="lazypromotion-github-inbound-monitor"', text)
        self.assertIn("python github_inbound_monitor.py loop", text)
        self.assertIn("tmux has-session", text)
        self.assertEqual(text.count("tmux new-session"), 1)
        self.assertIn("INTERVAL_MINUTES < 15", text)
        self.assertIn("chmod 600", text)
        self.assertIn('tail -n 1 "$LOG"', text)


if __name__ == "__main__":
    unittest.main()
