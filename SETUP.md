# 🏏 Cricket Club Bot — Complete Setup Guide

## Files in this folder
```
app.py              ← Main Flask server
agent.py            ← WhatsApp command parser
sheets.py           ← Google Sheets read/write
reminder.py         ← Auto reminder scheduler
config.py           ← Your settings (edit this!)
requirements.txt    ← Python packages
Procfile            ← For Railway deployment
railway.json        ← Railway config
CricketClubFinance.xlsx ← Upload this to Google Sheets
```

---

## PHASE 1 — Google Sheets Setup

### 1. Upload Excel to Google Sheets
1. Go to https://sheets.google.com
2. Click **Import** → Upload `CricketClubFinance.xlsx`
3. Select **Replace spreadsheet**
4. Make sure name shows as **CricketClubFinance** at the top

### 2. Get Google API credentials
1. Go to https://console.cloud.google.com
2. Select your **CricketBot** project
3. **APIs & Services → Library → Enable:**
   - Google Sheets API ✅
   - Google Drive API ✅
4. **Credentials → Service Account → Keys → Add Key → JSON**
5. Download → rename to `credentials.json`
6. Open `credentials.json` in Notepad → copy the `client_email` value
7. In Google Sheets → **Share** → paste that email → Editor → Send

---

## PHASE 2 — Edit config.py

Open `config.py` in Notepad and update:

```python
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN  = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_WHATSAPP_NO = "whatsapp:+14155238886"
ADMIN_NUMBERS      = ["whatsapp:+819012345678"]   # YOUR number
ADMINS             = ["Karthik", "SK", "Satheesh", "Club Account"]
```

---

## PHASE 3 — Deploy to Railway (24x7 Free Hosting)

### Step 1 — GitHub
1. Go to https://github.com → Sign up / Login
2. Click **+** → **New repository** → name: `cricket-bot` → Public → Create
3. Download **GitHub Desktop**: https://desktop.github.com
4. Open GitHub Desktop → **Add existing repository** → select your `cricket_final` folder
5. Click **Publish repository** → **Publish**

### Step 2 — Add credentials.json as Secret on Railway
(Never upload credentials.json to GitHub — it's secret!)

### Step 3 — Railway
1. Go to https://railway.app → Sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select `cricket-bot`
4. Railway auto-detects Python and starts deploying ✅

### Step 4 — Add Environment Variables on Railway
In Railway → your project → **Variables** → Add each:

| Variable | Value |
|---|---|
| `TWILIO_ACCOUNT_SID` | your SID |
| `TWILIO_AUTH_TOKEN` | your token |
| `SHEET_NAME` | CricketClubFinance |
| `GOOGLE_CREDENTIALS` | paste entire credentials.json content |

### Step 5 — Update sheets.py for Railway credentials
Railway uses environment variable instead of file.
Replace the `_client()` function in `sheets.py` with:

```python
import os, json
def _client():
    import tempfile
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        # Running on Railway — use environment variable
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(creds_json)
            tmp_path = f.name
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmp_path, SCOPE)
    else:
        # Running locally — use file
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    return gspread.authorize(creds)
```

### Step 6 — Get Railway URL
1. Railway → Settings → **Domains** → **Generate Domain**
2. Copy your URL e.g. `https://cricket-bot.up.railway.app`

### Step 7 — Connect to Twilio
1. Twilio → Messaging → Try it out → Send a WhatsApp message
2. **Sandbox Settings → When a message comes in:**
```
https://cricket-bot.up.railway.app/whatsapp
```
3. Save ✅

---

## PHASE 4 — Test on WhatsApp

Send these messages to the Twilio number:
```
help
players
Prithvi paid 15000 Karthik
clubfee unpaid
xi div2 Round1 Ravi,Kumar,Suresh,Arjun
matchfee div2 Round1 Ravi=1500,Kumar=1500 Karthik
expense tournament 3000 Entry fee Karthik
settle Karthik 15000
summary
```

---

## Auto Reminders (No action needed)
- **Every Monday 10:00 AM** → Club fee reminder to all Pending players
- **5th of every month 6:00 PM** → Monthly reminder
- **Player replies PAID** → Auto-marked in sheet + admin notified

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot not responding | Check Railway logs → Deployments |
| Google Sheets error | Check GOOGLE_CREDENTIALS variable |
| WhatsApp not reaching bot | Update Twilio webhook URL |
| Player not found | Check spelling matches sheet exactly |
