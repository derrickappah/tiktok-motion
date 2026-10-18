# TikTok Multi-Account Automation

Python + Playwright script designed to manage multiple TikTok accounts from an `accounts.json` file. Each account retains its own persistent browser session (cookies, storage, and fingerprints) and can route through dedicated proxies.

---

## 1. Setup

### Step A: Install Requirements
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 2. Configure Accounts (`accounts.json`)

Define your 10 accounts in [`accounts.json`](file:///c:/Users/DELL/Documents/antigravity/keen-noether/accounts.json).

```json
[
  {
    "id": "acc_1",
    "name": "Account 1",
    "proxy": "http://user:password@proxy-ip:port",
    "custom_user_agent": ""
  },
  {
    "id": "acc_2",
    "name": "Account 2",
    "proxy": "http://user:password@proxy2-ip:port",
    "custom_user_agent": ""
  }
]
```

> **Proxy format:** Supports `http://user:password@ip:port` or `ip:port:user:pass`. If you are not using a proxy for an account, leave it blank `""`.

---

## 3. Initial Login (One-Time Only)

Because of TikTok's CAPTCHAs and 2FA, each account must be logged in **once manually**. The session is saved permanently in `./profiles/<account_id>`.

Log in to a specific account:
```bash
python tiktok_auto.py --login acc_1
```
A browser window will open. Complete the login and CAPTCHA. Once you're inside TikTok, hit **ENTER** in your terminal to save the session.

To log in all accounts one-by-one:
```bash
python tiktok_auto.py --login-all
```

---

## 4. Run Automations on a Post

Whenever you have a post link, run the command with your desired flags:

### Like + Follow + Comment:
```bash
python tiktok_auto.py --url "https://www.tiktok.com/@creator/video/123456789" --like --follow --comment "Great video! 🔥"
```

### Use Randomized Comments across Accounts:
Avoid identical comments by using `--comment random`:
```bash
python tiktok_auto.py --url "https://www.tiktok.com/@creator/video/123456789" --like --comment random
```

### Like Only (Selected accounts):
```bash
python tiktok_auto.py --url "https://www.tiktok.com/@creator/video/123456789" --like --accounts "acc_1,acc_2,acc_3"
```

### Custom Stagger Delays:
```bash
python tiktok_auto.py --url "https://www.tiktok.com/@creator/video/123456789" --like --delay-min 30 --delay-max 90
```

---

## Anti-Ban Features Built In:
1. **Isolated Fingerprints**: Every account runs inside its own persistent browser directory with distinct cookies, cache, and LocalStorage.
2. **Watch Time Simulation**: Simulates 8–15 seconds of watch time and mouse micro-scrolls before any action is clicked.
3. **Typing Simulation**: Types comments with randomized keystroke intervals (40ms–120ms).
4. **Staggered Delays**: Configurable random cooldown between accounts to prevent simultaneous burst flags.
