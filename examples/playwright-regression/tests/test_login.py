from __future__ import annotations

from playwright.sync_api import expect

from pages.login_page import LoginPage


def test_valid_user_reaches_dashboard(page, base_url: str) -> None:
    login = LoginPage(page, base_url)
    login.open()
    login.sign_in("ada@example.test", "fixture-pass")

    expect(page).to_have_title("Dashboard")
    expect(login.status).to_have_text("Welcome, Ada")


def test_invalid_password_is_rejected(page, base_url: str) -> None:
    login = LoginPage(page, base_url)
    login.open()
    login.sign_in("ada@example.test", "wrong-pass")

    expect(page).to_have_title("Regression specimen")
    expect(login.status).to_have_text("Email or password is incorrect")
