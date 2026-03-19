import os
import gspread
import tempfile
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import *

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def _client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(creds_json)
            tmp_path = f.name
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmp_path, SCOPE)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    return gspread.authorize(creds)

def get_ws(tab):
    return _client().open(SHEET_NAME).worksheet(tab)

def today():
    return datetime.now().strftime("%d/%m/%Y")

def get_all_players():
    ws = get_ws("Players & Club Fees")
    records = ws.get_all_values()
    headers = records[3]
    players = []
    for row in records[4:]:
        if row[0] and str(row[0]).strip().isdigit():
            players.append(dict(zip(headers, row)))
    return players

def get_player_by_phone(phone):
    phone_clean = phone.replace("-","").replace(" ","").strip()
    for p in get_all_players():
        stored = str(p.get("Phone Number","")).replace("-","").replace(" ","").strip()
        if stored == phone_clean:
            return p.get("Player Name","").strip()
    return None

def get_player_phone(name):
    for p in get_all_players():
        if p.get("Player Name","").strip().lower() == name.strip().lower():
            return str(p.get("Phone Number","")).strip()
    return None

def add_player(name, phone, role, nk_team):
    ws = get_ws("Players & Club Fees")
    players = get_all_players()
    next_no = len(players) + 1
    ws.append_row([next_no, name.title(), phone, today(),
                   role.title(), nk_team.upper(),
                   "", "Pending", "", "", ""])
    return next_no

def mark_club_fee_paid(player_name, paid_to="Admin", amount=None):
    ws = get_ws("Players & Club Fees")
    data = ws.get_all_values()
    for i, row in enumerate(data[PCF_DATA_ROW-1:], start=PCF_DATA_ROW):
        if row[PCF_NAME-1].strip().lower() == player_name.strip().lower():
            if row[PCF_STATUS-1].strip().lower() in ["pending", ""]:
                if amount:
                    ws.update_cell(i, PCF_FEE, amount)
                ws.update_cell(i, PCF_STATUS,   "Paid")
                ws.update_cell(i, PCF_PAIDDATE, today())
                ws.update_cell(i, PCF_PAIDTO,   paid_to)
                return True
    return False

def get_pending_club_fees():
    players = get_all_players()
    return [p for p in players
            if str(p.get("Fee Status","")).strip().lower() == "pending"]

def set_playing_xi(sheet_name, round_name, player_list):
    ws = get_ws(sheet_name)
    added = []
    for player in player_list:
        player = player.strip().title()
        if player:
            ws.append_row([today(), player, round_name, "", "Unpaid", "", ""])
            added.append(player)
    return added

def update_playing_xi(sheet_name, round_name, new_players):
    ws = get_ws(sheet_name)
    data = ws.get_all_values()
    rows_to_del = []
    for i, row in enumerate(data[MF_DATA_ROW-1:], start=MF_DATA_ROW):
        if (row[MF_ROUND-1].strip().lower() == round_name.strip().lower()
                and row[MF_STATUS-1].strip().lower() == "unpaid"):
            rows_to_del.append(i)
    for idx in sorted(rows_to_del, reverse=True):
        ws.delete_rows(idx)
    return set_playing_xi(sheet_name, round_name, new_players)

def record_match_fees(sheet_name, round_name, fee_dict, paid_to="Admin"):
    ws = get_ws(sheet_name)
    data = ws.get_all_values()
    ok, fail = [], []
    for player, amount in fee_dict.items():
        found = False
        for i, row in enumerate(data[MF_DATA_ROW-1:], start=MF_DATA_ROW):
            if (row[MF_PLAYER-1].strip().lower() == player.strip().lower()
                    and row[MF_ROUND-1].strip().lower() == round_name.strip().lower()):
                ws.update_cell(i, MF_AMOUNT, amount)
                ws.update_cell(i, MF_STATUS, "Paid")
                ws.update_cell(i, MF_PAIDTO, paid_to)
                ok.append(player)
                found = True
                break
        if not found:
            fail.append(player)
    return ok, fail

def get_unpaid_match_fees(sheet_name):
    ws = get_ws(sheet_name)
    data = ws.get_all_values()
    unpaid = []
    for row in data[MF_DATA_ROW-1:]:
        if row[MF_STATUS-1].strip().lower() == "unpaid" and row[MF_PLAYER-1].strip():
            unpaid.append({"player": row[MF_PLAYER-1], "round": row[MF_ROUND-1]})
    return unpaid

def add_expense(category, amount, note, paid_by):
    ws = get_ws("Sponsors & Expenses")
    exp_type = "Income" if category.lower() == "sponsorship" else "Expense"
    ws.append_row([today(), category.title(), exp_type, amount, note, paid_by])

def add_settlement(from_name, to_name, amount, reason, recorded_by):
    ws = get_ws("Settlements")
    ws.append_row([today(), from_name, to_name, amount, reason, recorded_by])

def get_summary(month_str=None):
    now = datetime.now()
    month = month_str or now.strftime("%B %Y")
    players = get_all_players()
    cf_paid = sum(int(str(p.get("Club Fee (₹)", 0) or 0))
                  for p in players if p.get("Fee Status","").lower() == "paid")
    cf_pending = sum(int(str(p.get("Club Fee (₹)", 0) or 0))
                     for p in players if p.get("Fee Status","").lower() == "pending")
    mf_paid = mf_unpaid = 0
    for sheet in TEAM_SHEET.values():
        try:
            ws = get_ws(sheet)
            data = ws.get_all_values()
            for row in data[MF_DATA_ROW-1:]:
                amt = int(str(row[MF_AMOUNT-1] or 0)) if row[MF_AMOUNT-1] else 0
                if row[MF_STATUS-1].strip().lower() == "paid":
                    mf_paid += amt
                elif row[MF_STATUS-1].strip().lower() == "unpaid":
                    mf_unpaid += amt
        except Exception:
            pass
    ws = get_ws("Sponsors & Expenses")
    data = ws.get_all_values()
    total_exp = total_inc = 0
    for row in data[EX_DATA_ROW-1:]:
        try:
            amt = int(str(row[EX_AMOUNT-1] or 0))
            if row[EX_TYPE-1].strip().lower() == "expense":
                total_exp += amt
            elif row[EX_TYPE-1].strip().lower() == "income":
                total_inc += amt
        except Exception:
            pass
    total_in = cf_paid + mf_paid
    balance = total_in + total_inc - total_exp
    return {
        "month": month,
        "cf_paid": cf_paid, "cf_pending": cf_pending,
        "mf_paid": mf_paid, "mf_unpaid": mf_unpaid,
        "sponsorship": total_inc,
        "expenses": total_exp,
        "total_in": total_in,
        "balance": balance,
    }
