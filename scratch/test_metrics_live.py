import asyncio, json, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = Path("./profiles/acc_1").resolve()
    port = 9338
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

            metrics = await page.evaluate('''() => {
                const metrics = {
                    likes: null,
                    comments: null,
                    saves: null,
                    shares: null
                };

                const parseDigits = (text) => {
                    if (!text) return null;
                    const m = text.match(/([0-9]+[0-9.,]*[KMBkmb]?)/);
                    return m ? m[1] : null;
                };

                // Strategy 1: Check all elements matching count attributes
                const countMapping = [
                    { key: 'likes', selectors: ['[data-e2e="like-count"]', '[data-e2e="browse-like-count"]', 'strong[data-e2e*="like"]'] },
                    { key: 'comments', selectors: ['[data-e2e="comment-count"]', '[data-e2e="browse-comment-count"]', 'strong[data-e2e*="comment"]'] },
                    { key: 'saves', selectors: ['[data-e2e="favorite-count"]', '[data-e2e="undefined-count"]', 'strong[data-e2e*="favorite"]'] },
                    { key: 'shares', selectors: ['[data-e2e="share-count"]', 'strong[data-e2e*="share"]'] }
                ];

                for (const item of countMapping) {
                    for (const sel of item.selectors) {
                        const els = Array.from(document.querySelectorAll(sel));
                        for (const el of els) {
                            const val = (el.innerText || el.textContent || '').trim();
                            const digits = parseDigits(val);
                            if (digits) {
                                metrics[item.key] = digits;
                                break;
                            }
                        }
                        if (metrics[item.key]) break;
                    }
                }

                // Strategy 2: Check aria-labels on action buttons / containers
                const actionElements = Array.from(document.querySelectorAll('[data-e2e*="icon"], div[role="button"], button'));
                for (const el of actionElements) {
                    const aria = el.getAttribute('aria-label') || '';
                    if (!aria) continue;

                    // Likes
                    if (!metrics.likes && /like/i.test(aria)) {
                        const m = aria.match(/([0-9]+[0-9.,]*[KMBkmb]?)\s*likes?/i);
                        if (m) metrics.likes = m[1];
                    }

                    // Comments
                    if (!metrics.comments && /comment/i.test(aria)) {
                        const m = aria.match(/([0-9]+[0-9.,]*[KMBkmb]?)\s*comments?/i);
                        if (m) metrics.comments = m[1];
                    }

                    // Saves / Favorites
                    if (!metrics.saves && /(favorite|save|bookmark)/i.test(aria)) {
                        const m = aria.match(/([0-9]+[0-9.,]*[KMBkmb]?)\s*(?:added to\s*)?(?:favorites?|saves?)/i);
                        if (m) metrics.saves = m[1];
                    }

                    // Shares
                    if (!metrics.shares && /share/i.test(aria)) {
                        const m = aria.match(/([0-9]+[0-9.,]*[KMBkmb]?)\s*shares?/i);
                        if (m) metrics.shares = m[1];
                    }
                }

                // Strategy 3: Check rehydration script data recursively for stats
                try {
                    const script = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__') || document.getElementById('SIGI_STATE');
                    if (script) {
                        const parsed = JSON.parse(script.textContent || '{}');
                        const findStats = (obj) => {
                            if (!obj || typeof obj !== 'object') return null;
                            if (obj.diggCount !== undefined || obj.commentCount !== undefined) return obj;
                            for (const k of Object.keys(obj)) {
                                const found = findStats(obj[k]);
                                if (found) return found;
                            }
                            return null;
                        };
                        const stats = findStats(parsed);
                        if (stats) {
                            if (!metrics.likes && stats.diggCount !== undefined) metrics.likes = String(stats.diggCount);
                            if (!metrics.comments && stats.commentCount !== undefined) metrics.comments = String(stats.commentCount);
                            if (!metrics.saves && stats.collectCount !== undefined) metrics.saves = String(stats.collectCount);
                            if (!metrics.shares && stats.shareCount !== undefined) metrics.shares = String(stats.shareCount);
                        }
                    }
                } catch (e) {}

                // Strategy 4: If action bar is present but label has no digits, count is 0!
                const hasActionContainer = document.querySelector('[data-e2e*="like-icon"], [data-e2e*="like-count"], [aria-label*="Like" i]');
                if (hasActionContainer) {
                    if (metrics.likes === null) metrics.likes = '0';
                    if (metrics.comments === null) metrics.comments = '0';
                    if (metrics.saves === null) metrics.saves = '0';
                    if (metrics.shares === null) metrics.shares = '0';
                }

                return metrics;
            }''')

            print("Extracted Metrics:", metrics)
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(inspect())
