#!/usr/bin/env python3
"""Finite visible UI checks on the existing LazyPromotion desktop, no posting."""
import json
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
import app_preview
import browser
from gmail_application_monitor import private_json


def main():
    evidence_dir = browser.ROOT / ".local" / "evidence" / "app-preview-20260926"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with app_preview.make_local_server(18936) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with browser.browser_operation_lock(timeout_seconds=30), sync_playwright() as pw:
                client = pw.chromium.connect_over_cdp(browser.DEFAULT_CDP)
                context = client.contexts[0]
                page = next((p for p in context.pages if urlsplit(p.url).netloc == '127.0.0.1:18936'), None)
                created = page is None
                if created:
                    page = context.new_page()
                old_viewport = page.viewport_size
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                cdp = None
                try:
                    page.bring_to_front()
                    page.set_viewport_size({'width': 1320, 'height': 980})
                    page.goto('http://127.0.0.1:18936/', wait_until='networkidle')
                    if page.evaluate("localStorage.getItem('lazypromotion.public-preview.v1')") is not None:
                        raise RuntimeError('A saved preview copy already exists; do not overwrite user review data.')
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'ready')
                    expect(page.get_by_role('heading', name='L & N: Speech Practice')).to_be_visible()
                    expect(page.get_by_test_id('publication')).to_have_count(2)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.screenshot(path=str(evidence_dir / 'desktop.png'), full_page=True)
                    page.get_by_role('button', name='Bunko: Classics with Ruby').click()
                    expect(page.get_by_test_id('publication')).to_have_count(3)
                    expect(page.get_by_text('Signed-in check only', exact=True).first).to_be_visible()
                    page.get_by_text('Read published text', exact=True).first.click()
                    expect(page.locator('.post-body').first).to_contain_text('Bunko')
                    for width in (320, 390, 780):
                        page.set_viewport_size({'width': width, 'height': 844})
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.set_viewport_size({'width': 390, 'height': 844})
                    page.screenshot(path=str(evidence_dir / 'mobile.png'), full_page=True)
                    page.get_by_role('button', name='Save offline copy', exact=True).click()
                    expect(page.locator('#storage-state')).to_contain_text('Saved locally')
                    page.reload(wait_until='networkidle')
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'ready')
                    assert page.evaluate('Boolean(navigator.serviceWorker.controller)')
                    cdp = context.new_cdp_session(page)
                    cdp.send('Network.enable')
                    cdp.send('Network.emulateNetworkConditions', {'offline': True, 'latency': 0, 'downloadThroughput': 0, 'uploadThroughput': 0})
                    page.reload(wait_until='domcontentloaded')
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'saved', timeout=12000)
                    expect(page.locator('#sync-state')).to_contain_text('saved copy from')
                    expect(page.get_by_role('button', name='Save offline copy', exact=True)).to_be_disabled()
                    page.screenshot(path=str(evidence_dir / 'offline.png'), full_page=True)
                    page.get_by_role('button', name='Remove saved copy', exact=True).click()
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'error')
                    cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 0, 'downloadThroughput': -1, 'uploadThroughput': -1})
                    page.get_by_role('button', name='Refresh', exact=True).click()
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'ready')
                    page.route('**/api/v1/workspace', lambda route: route.fulfill(json={'version': 99}))
                    page.get_by_role('button', name='Refresh', exact=True).click()
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'error')
                    expect(page.get_by_test_id('publication')).to_have_count(0)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.screenshot(path=str(evidence_dir / 'error.png'), full_page=True)
                    page.unroute('**/api/v1/workspace')
                    page.get_by_role('button', name='Refresh', exact=True).click()
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-status', 'ready')
                    assert not errors, errors
                    private_json(evidence_dir / 'result.json', {
                        'state': 'passed', 'products': 2, 'publications': 5,
                        'widths_without_overflow': [320, 390, 780, 1320],
                        'offline_reload': True, 'clear_saved_copy': True,
                        'unsupported_version_denied': True, 'page_errors': 0,
                        'pwa_install_qualification': 'not_run',
                        'native_clients_tested': False, 'store_release': False,
                    })
                    print(json.dumps({'state': 'passed', 'evidence': str(evidence_dir)}))
                except Exception:
                    page.screenshot(path=str(evidence_dir / 'failure.png'), full_page=True)
                    raise
                finally:
                    if cdp is not None:
                        cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 0, 'downloadThroughput': -1, 'uploadThroughput': -1})
                        cdp.detach()
                    page.unroute('**/api/v1/workspace')
                    if created:
                        page.close()
                    elif old_viewport:
                        page.set_viewport_size(old_viewport)
        finally:
            server.shutdown(); thread.join(timeout=5)
            assert not thread.is_alive()


if __name__ == '__main__':
    main()
