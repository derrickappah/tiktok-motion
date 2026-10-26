import asyncio, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = Path("./profiles/acc_1").resolve()
    port = 9340
    url = "https://www.tiktok.com/@derrickappah4/photo/7697701219929885959"
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--start-maximized"
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(3)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)

            # Use raw string r'''...''' so Python never modifies regex escapes
            metrics = await page.evaluate(r'''() => {
                const metrics = {
                    likes: null,
                    comments: null,
                    saves: null,
                    shares: null
                };

                const parseDigits = (str) => {
                    if (!str) return null;
                    const m = str.match(/([0-9]+[0-9.,]*[KMBkmb]?)/);
                    return m ? m[1] : null;
                };

                // 1. Check all elements matching count attributes
                const mapping = [
                    { key: 'likes', countSel: '[data-e2e="like-count"], [data-e2e="browse-like-count"]', iconSel: '[data-e2e="like-icon"], [data-e2e="browse-like-icon"]', label: 'like' },
                    { key: 'comments', countSel: '[data-e2e="comment-count"], [data-e2e="browse-comment-count"]', iconSel: '[data-e2e="comment-icon"], [data-e2e="browse-comment-icon"]', label: 'comment' },
                    { key: 'saves', countSel: '[data-e2e="favorite-count"], [data-e2e="undefined-count"]', iconSel: '[data-e2e="favorite-icon"], [data-e2e="undefined-icon"]', label: 'favorite' },
                    { key: 'shares', countSel: '[data-e2e="share-count"]', iconSel: '[data-e2e="share-icon"], [data-e2e="share-btn"]', label: 'share' }
                ];

                for (const item of mapping) {
                    // Check text in count element
                    const countEls = Array.from(document.querySelectorAll(item.countSel));
                    for (const el of countEls) {
                        const val = (el.innerText || el.textContent || '').trim();
                        const d = parseDigits(val);
                        if (d) {
                            metrics[item.key] = d;
                            break;
                        }
                    }

                    // Check aria-label on icon/button
                    if (!metrics[item.key]) {
                        const iconEls = Array.from(document.querySelectorAll(item.iconSel));
                        for (const el of iconEls) {
                            const aria = el.getAttribute('aria-label') || '';
                            const d = parseDigits(aria);
                            if (d) {
                                metrics[item.key] = d;
                                break;
                            }
                        }
                    }
                }

                // 2. Check all buttons with aria-label containing like, comment, share, favorite
                const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
                for (const btn of buttons) {
                    const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (!aria) continue;

                    if (!metrics.likes && aria.includes('like')) {
                        const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*likes?/i);
                        if (m) metrics.likes = m[1];
                    }
                    if (!metrics.comments && aria.includes('comment')) {
                        const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*comments?/i);
                        if (m) metrics.comments = m[1];
                    }
                    if (!metrics.saves && (aria.includes('favorite') || aria.includes('save'))) {
                        const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*(?:added to\s*)?(?:favorites?|saves?)/i);
                        if (m) metrics.saves = m[1];
                    }
                    if (!metrics.shares && aria.includes('share')) {
                        const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*shares?/i);
                        if (m) metrics.shares = m[1];
                    }
                }

                // 3. Fallback: If action bar is rendered on screen, any metric without digits is 0 (not null/NA)
                const hasActionBar = document.querySelector('[data-e2e="like-icon"], [data-e2e="like-count"], [aria-label*="Like" i]');
                if (hasActionBar) {
                    if (metrics.likes === null) metrics.likes = '0';
                    if (metrics.comments === null) metrics.comments = '0';
                    if (metrics.saves === null) metrics.saves = '0';
                    if (metrics.shares === null) metrics.shares = '0';
                }

                return metrics;
            }''')
            print("EXTRACTED METRICS:", metrics)
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(inspect())
