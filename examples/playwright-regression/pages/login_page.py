from __future__ import annotations

from playwright.sync_api import Page


class LoginPage:
    """Selectors and user actions for the specimen login page."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.email = page.get_by_label("Email")
        self.password = page.get_by_label("Password")
        self.submit = page.get_by_role("button", name="Sign in")
        self.status = page.get_by_role("status")

    def open(self) -> None:
        self.page.goto(self.base_url, wait_until="domcontentloaded")

    def sign_in(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()
