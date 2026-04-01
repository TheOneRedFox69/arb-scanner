# 🎯 Sports Arbitrage Scanner

A Python tool that monitors live odds across multiple bookmakers and sports,
detects arbitrage opportunities, and alerts you via email.

Works for 2-way markets (MLB, NBA, NFL, Tennis) and 3-way markets (Soccer).

---

## 📁 File Structure

```
arb_tool/
├── arb_calculator.py   # Core maths: arb detection & stake calculation
├── odds_fetcher.py     # Fetches odds from The Odds API
├── alerts.py           # Email alert formatting and sending
├── scanner.py          # Main scan loop (run this for command-line use)
├── dashboard.py        # Streamlit web dashboard
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your secrets (copy to .env)
└── .gitignore          # Prevents .env from being committed
```

---

## 🚀 Setup (GitHub Codespaces)

### Step 1 — Open a Codespace
1. Go to your GitHub repo
2. Click **Code → Codespaces → Create codespace on main**
3. Wait for it to load (takes ~1 minute)

### Step 2 — Upload the files
Drag all files from this project into the Codespace file explorer.

### Step 3 — Install dependencies
In the Codespace terminal, run:
```bash
pip install -r requirements.txt
```

### Step 4 — Configure your secrets
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- `ODDS_API_KEY` — from the-odds-api.com
- `EMAIL_SENDER` / `EMAIL_PASSWORD` / `EMAIL_RECIPIENT` — your Gmail details

> ⚠️ `EMAIL_PASSWORD` must be a **Gmail App Password**, not your login password.
> Get one at: Google Account → Security → 2-Step Verification → App Passwords

### Step 5 — Run the dashboard
```bash
streamlit run dashboard.py
```
Codespaces will show a popup — click **Open in Browser** to see your dashboard.

### Step 6 — Or run the scanner in the background
```bash
python scanner.py
```
This scans on a schedule and emails you when opportunities are found.

---

## 📱 Android App Setup

Once your dashboard is deployed (e.g. on Railway.app):
1. Open the URL in **Chrome on Android**
2. Tap the **three-dot menu → Add to Home Screen**
3. The app installs like a native app with its own icon

---

## 💡 Supported Sports & Markets

| Sport | Markets |
|-------|---------|
| Soccer (EPL, La Liga, UCL) | H2H (1X2 — 3-way), Both Teams to Score |
| NFL | H2H, Over/Under |
| NBA | H2H, Over/Under |
| MLB | H2H, Over/Under |
| Tennis (ATP) | H2H |

---

## ⚠️ Important Notes

- **Free Odds API tier:** 500 requests/month. With 7 sports, each scan uses ~7 requests.
  At default 1-hour intervals, you'll use ~168 requests/week — well within the free tier.
- **Arb windows close fast** on popular markets. Act quickly when an alert arrives.
- **Bookmakers monitor** for arb betting and may limit accounts. Keep stakes natural-looking.
- Always **verify odds on the bookmaker site** before placing — they change in seconds.
