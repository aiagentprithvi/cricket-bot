# ══════════════════════════════════════════
# CRICKET CLUB BOT — CONFIG
# Edit these values before running the bot
# ══════════════════════════════════════════

SHEET_NAME       = "CricketClubFinance"
CREDENTIALS_FILE = "credentials.json"

TWILIO_ACCOUNT_SID = "your_twilio_account_sid"
TWILIO_AUTH_TOKEN  = "your_twilio_auth_token"
TWILIO_WHATSAPP_NO = "whatsapp:+14155238886"

# Your WhatsApp number(s) — gets admin notifications
# Format: ["whatsapp:+819012345678"]
ADMIN_NUMBERS = ["whatsapp:+819012345678"]

# Admin names exactly as they appear in the Admins sheet
ADMINS = ["Karthik", "SK", "Satheesh", "Club Account"]

# Team key → sheet name mapping
TEAM_SHEET = {
    "div2":  "Div-2 Match fee",
    "div-2": "Div-2 Match fee",
    "div3":  "Div-3 Match fee",
    "div-3": "Div-3 Match fee",
    "nk1":   "Nk1 Match fee",
    "nk2":   "Nk2 Match fee",
    "u15":   "U15 Match fee",
}

# Sheet column positions (1-based) — match your Google Sheet exactly
# Players & Club Fees sheet
PCF_NO       = 1   # #
PCF_NAME     = 2   # Player Name
PCF_PHONE    = 3   # Phone Number
PCF_JOIN     = 4   # Join Date
PCF_ROLE     = 5   # Role
PCF_NKTEAM   = 6   # NK Team
PCF_FEE      = 7   # Club Fee (₹)
PCF_STATUS   = 8   # Fee Status
PCF_PAIDDATE = 9   # Paid Date
PCF_PAIDTO   = 10  # Paid To
PCF_REMARKS  = 11  # Remarks
PCF_DATA_ROW = 5   # first data row (after 4 header rows)

# Match fee sheets columns
MF_DATE    = 1   # Date
MF_PLAYER  = 2   # Player
MF_ROUND   = 3   # Round
MF_AMOUNT  = 4   # Amount (₹)
MF_STATUS  = 5   # Status
MF_PAIDTO  = 6   # Paid to
MF_REMARKS = 7   # Remarks
MF_DATA_ROW= 4   # first data row

# Expenses sheet columns
EX_DATE    = 1   # Date
EX_CAT     = 2   # Category
EX_TYPE    = 3   # Type (Income/Expense)
EX_AMOUNT  = 4   # Amount
EX_NOTE    = 5   # Note
EX_PAIDBY  = 6   # Paid By/To
EX_DATA_ROW= 4   # first data row

# Settlements sheet columns
ST_DATE    = 1   # Date
ST_FROM    = 2   # From
ST_TO      = 3   # To
ST_AMOUNT  = 4   # Amount
ST_REASON  = 5   # Reason
ST_RECBY   = 6   # Recorded By
ST_DATA_ROW= 5   # first data row

VALID_EXPENSE_CATS = [
    "tournament","ground","equipment",
    "refreshments","jersey","sponsorship"
]
