#!/usr/bin/env python3
"""Finite local authoring check. Uses the existing desktop; never publishes."""
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app_preview
import browser
from gmail_application_monitor import private_json
from playwright.sync_api import sync_playwright, expect


def main():
    folder = browser.ROOT / '.local/evidence/app-draft-20260926'
    folder.mkdir(parents=True, exist_ok=True)
    brief = {
        'name': 'L & N: Speech Practice',
        'productUrl': 'https://apps.apple.com/us/app/l-n-speech-practice/id6808872450',
        'audience': 'learners who mix up L and N',
        'problem': 'Hearing the difference between light and night',
        'feature': 'Short listening rounds and single-word recording practice.',
        'useful': 'Ask a partner to read light and night in a mixed order. Write down what you hear, then compare answers.',
        'price': 'iPhone/iPad: US$0.99.',
        'limitation': 'The score is practice feedback, not a perfect judge of pronunciation.',
        'evidenceUrl': 'https://apps.apple.com/us/app/l-n-speech-practice/id6808872450',
        'destinationUrl': 'https://www.linkedin.com/in/lazyingart/',
        'account': 'LazyingArt',
    }
    key = 'lazypromotion.local-draft.v1'
    with app_preview.make_local_server(18936) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            with browser.browser_operation_lock(timeout_seconds=15), sync_playwright() as pw:
                client = pw.chromium.connect_over_cdp(browser.DEFAULT_CDP)
                page = client.contexts[0].new_page()
                errors, writes = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: writes.append(request.method) if request.method not in ('GET', 'HEAD') else None)
                page.on('dialog', lambda dialog: dialog.accept())
                owns_saved = False
                cdp = None
                try:
                    page.bring_to_front(); page.set_viewport_size({'width': 1320, 'height': 980})
                    page.goto('http://127.0.0.1:18936/', wait_until='networkidle')
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-offline-shell', 'ready', timeout=15000)
                    if page.evaluate('(key) => localStorage.getItem(key)', key) is not None:
                        raise RuntimeError('A saved draft already exists. Do not overwrite user work.')
                    page.get_by_role('link', name='Prepare a campaign').click()
                    for name, value in brief.items():
                        page.locator(f'#brief-form [name="{name}"]').fill(value)
                    page.get_by_role('button', name='Build starter draft', exact=True).click()
                    expect(page.locator('#draft-body')).to_have_value(__import__('re').compile('Ask a partner.*', __import__('re').S))
                    page.get_by_role('button', name='Export draft JSON').click()
                    expect(page.locator('#draft-status')).to_contain_text('Preview this exact draft')
                    page.locator('#draft-title').fill('Light or night? Try the ear first')
                    page.get_by_role('button', name='Preview draft', exact=True).click()
                    expect(page.locator('#preview-destination')).to_contain_text('LazyingArt → https://www.linkedin.com/in/lazyingart/')
                    expect(page.locator('#preview-body')).to_contain_text(brief['price'])
                    page.screenshot(path=str(folder / 'desktop-preview.png'), full_page=True)
                    with page.expect_download() as download:
                        page.get_by_role('button', name='Export draft JSON').click()
                    artifact = download.value
                    data = json.loads(Path(artifact.path()).read_text())
                    assert data['state'] == 'draft' and data['publication'] == 'not_connected'
                    assert data['body'] == page.locator('#draft-body').input_value()
                    artifact.delete()
                    page.get_by_role('button', name='Save draft here', exact=True).click(); owns_saved = True
                    expect(page.locator('#draft-status')).to_contain_text('Draft saved')
                    page.reload(wait_until='networkidle')
                    expect(page.get_by_test_id('workspace')).to_have_attribute('data-offline-shell', 'ready', timeout=15000)
                    expect(page.locator('#draft-editor')).to_be_hidden()
                    page.get_by_role('button', name='Load saved draft', exact=True).click()
                    expect(page.locator('#draft-title')).to_have_value('Light or night? Try the ear first')
                    page.locator('#draft-body').fill('<img src=x onerror=alert(1)> literal text')
                    page.get_by_role('button', name='Preview draft', exact=True).click()
                    expect(page.locator('#preview-body')).to_have_text('<img src=x onerror=alert(1)> literal text')
                    assert page.locator('#preview-body img').count() == 0
                    page.locator('#brief-form [name="price"]').fill('Changed price')
                    expect(page.locator('#draft-preview')).to_be_hidden()
                    page.get_by_role('button', name='Save draft here', exact=True).click()
                    expect(page.locator('#draft-status')).to_contain_text('brief changed')
                    page.get_by_role('button', name='Load saved draft', exact=True).click()
                    for width in (320, 390, 780, 1320):
                        page.set_viewport_size({'width': width, 'height': 844})
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.set_viewport_size({'width': 390, 'height': 844})
                    page.get_by_role('button', name='Preview draft', exact=True).click()
                    page.screenshot(path=str(folder / 'mobile-preview.png'), full_page=True)
                    # Test only this tab offline, not the shared browser context.
                    page.reload(wait_until='networkidle')
                    assert page.evaluate('Boolean(navigator.serviceWorker.controller)')
                    cdp = client.contexts[0].new_cdp_session(page)
                    cdp.send('Network.enable')
                    cdp.send('Network.emulateNetworkConditions', {'offline': True, 'latency': 0, 'downloadThroughput': 0, 'uploadThroughput': 0})
                    page.reload(wait_until='domcontentloaded')
                    page.get_by_role('button', name='Load saved draft', exact=True).click()
                    expect(page.locator('#draft-title')).to_have_value('Light or night? Try the ear first')
                    page.get_by_role('button', name='Preview draft', exact=True).click()
                    expect(page.locator('#draft-preview')).to_be_visible()
                    page.get_by_role('button', name='Remove saved draft', exact=True).click()
                    assert page.evaluate('(key) => localStorage.getItem(key)', key) is None
                    owns_saved = False
                    assert not writes and not errors, (writes, errors)
                    private_json(folder / 'result.json', {
                        'state': 'passed', 'brief_to_edited_draft': True, 'exact_export': True,
                        'save_reload': True, 'stale_brief_rejected': True, 'literal_html': True,
                        'offline_draft_preview': True, 'delete_saved': True,
                        'widths_without_overflow': [320, 390, 780, 1320],
                        'network_mutations': len(writes), 'page_errors': len(errors),
                        'native_parity': False, 'publishing': False,
                    })
                    print(json.dumps({'state': 'passed', 'evidence': str(folder)}))
                except Exception:
                    page.screenshot(path=str(folder / 'failure.png'), full_page=True)
                    raise
                finally:
                    if cdp:
                        cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 0, 'downloadThroughput': -1, 'uploadThroughput': -1})
                        cdp.detach()
                    if owns_saved:
                        # Only this finite check's newly created test draft.
                        page.evaluate('(key) => localStorage.removeItem(key)', key)
                    page.close()
        finally:
            server.shutdown(); worker.join(timeout=5)
            assert not worker.is_alive()


if __name__ == '__main__':
    main()
