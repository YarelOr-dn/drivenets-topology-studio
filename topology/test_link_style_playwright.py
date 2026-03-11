#!/usr/bin/env python3
"""Test the link style arrow button: linkStyle before/after click, active class, console errors."""
import asyncio
import sys
from playwright.async_api import async_playwright

async def main():
    results = []
    console_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1400, 'height': 900})

        def on_console(msg):
            if msg.type == 'error':
                console_errors.append(msg.text)

        page.on('console', on_console)

        # Navigate and wait for topology editor (use 'load' - networkidle can hang on long-polling)
        await page.goto('http://localhost:8080', wait_until='load', timeout=20000)
        # Wait for arrow button to exist (may be in collapsed section)
        await page.wait_for_selector('#btn-link-style-arrow', state='attached', timeout=15000)
        # Expand left toolbar if collapsed
        if await page.evaluate('document.body.classList.contains("toolbar-collapsed")'):
            await page.click('#toolbar-toggle')
            await asyncio.sleep(0.3)
        # Expand Links section if collapsed
        link_section = page.locator('#link-tool-section')
        cls = await link_section.get_attribute('class') or ''
        if 'expanded' not in cls:
            await page.click('#link-tool-section .toolbar-section-header')
            await asyncio.sleep(0.3)
        await page.wait_for_function(
            'window.topologyEditor && typeof window.topologyEditor.linkStyle === "string"',
            timeout=5000
        )

        # 1. Get linkStyle before click
        before = await page.evaluate('window.topologyEditor.linkStyle')
        results.append(('linkStyle BEFORE click', before))

        # 2. Check arrow button state before
        arrow_before = await page.evaluate('''() => {
            const btn = document.getElementById('btn-link-style-arrow');
            return btn ? { exists: true, hasActive: btn.classList.contains('active') } : { exists: false };
        }''')
        results.append(('Arrow button exists', arrow_before.get('exists', False)))
        results.append(('Arrow button "active" BEFORE click', arrow_before.get('hasActive', False)))

        # 3. Click the arrow button via JS (bypasses visibility - element may be in collapsed/scrollable area)
        await page.evaluate('document.getElementById("btn-link-style-arrow").click()')
        await asyncio.sleep(0.2)

        # 4. Get linkStyle after click
        after = await page.evaluate('window.topologyEditor.linkStyle')
        results.append(('linkStyle AFTER click', after))

        # 5. Check arrow button state after
        arrow_after = await page.evaluate('''() => {
            const btn = document.getElementById('btn-link-style-arrow');
            return btn ? btn.classList.contains('active') : false;
        }''')
        results.append(('Arrow button "active" AFTER click', arrow_after))

        await browser.close()

    # Report
    print('=' * 60)
    print('LINK STYLE ARROW BUTTON TEST RESULTS')
    print('=' * 60)
    for label, value in results:
        print(f'{label}: {value}')
    print()
    print('linkStyle change:', repr(before), '->', repr(after))
    print()
    if arrow_after:
        print('[PASS] Arrow button correctly shows active state after click')
    else:
        print('[FAIL] Arrow button should have "active" class when arrow style is selected')
    print()
    if console_errors:
        print('Console errors:')
        for e in console_errors:
            print('  -', e)
    else:
        print('No JavaScript errors in console')
    print('=' * 60)

    return 0 if arrow_after and (before != after or after in ('arrow', 'double-arrow', 'dashed-arrow', 'dashed-double-arrow')) else 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
