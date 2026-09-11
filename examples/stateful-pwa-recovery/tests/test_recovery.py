from __future__ import annotations

from playwright.sync_api import expect


def login(page, name: str) -> None:
    page.get_by_role("button", name=f"Continue as {name}").click()
    expect(page.get_by_role("heading", name=f"{name}'s notes")).to_be_visible()


def test_reload_restores_scoped_draft_without_writing(recovery_page, base_url: str) -> None:
    page, api = recovery_page
    page.goto(base_url)
    login(page, "Ada")
    page.get_by_label("Draft").fill("Keep the exact unsent wording.")
    page.reload()

    expect(page.get_by_role("heading", name="Ada's notes")).to_be_visible()
    expect(page.get_by_label("Draft")).to_have_value("Keep the exact unsent wording.")
    expect(page.locator("#notes li")).to_have_count(0)
    assert api.attempts == []


def test_interrupted_write_retries_same_id_once(recovery_page, base_url: str) -> None:
    page, api = recovery_page
    api.fail_next_posts = 1
    page.goto(base_url)
    login(page, "Ada")
    page.get_by_label("Draft").fill("Save this through the interruption.")
    page.get_by_role("button", name="Save note").click()

    expect(page.get_by_role("status")).to_contain_text("Offline")
    expect(page.locator("#pending-count")).to_have_text("1")
    first_id = api.attempts[0]["id"]
    page.reload()
    expect(page.get_by_role("status")).to_have_text("Saved after retry")

    assert [attempt["id"] for attempt in api.attempts] == [first_id, first_id]
    assert list(api.notes["ada"]) == [first_id]
    expect(page.locator("#notes li")).to_have_count(1)


def test_account_switch_hides_cached_state(recovery_page, base_url: str) -> None:
    page, api = recovery_page
    page.goto(base_url)
    login(page, "Ada")
    page.get_by_label("Draft").fill("Ada private draft")
    page.get_by_role("button", name="Log out").click()
    login(page, "Lin")

    expect(page.get_by_label("Draft")).to_have_value("")
    expect(page.locator("#notes li")).to_have_count(0)
    expect(page.get_by_text("Ada private draft", exact=True)).to_have_count(0)
    assert api.attempts == []

    page.get_by_role("button", name="Log out").click()
    login(page, "Ada")
    expect(page.get_by_label("Draft")).to_have_value("Ada private draft")

