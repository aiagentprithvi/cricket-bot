import re
from config import TEAM_SHEET, ADMIN_NUMBERS, VALID_EXPENSE_CATS
from sheets import (
    get_all_players, add_player, get_player_by_phone,
    mark_club_fee_paid, get_pending_club_fees,
    set_playing_xi, update_playing_xi,
    record_match_fees, get_unpaid_match_fees,
    add_expense, add_settlement, get_summary,
    add_umpire_fee, get_unpaid_umpire_fees, get_umpire_summary,
)

def fmt(items):
    return "\n".join(f"  • {i}" for i in items) if items else "  None"

# Empty string = no reply sent (saves Twilio messages)
NO_REPLY = ""

HELP = """🏏 *Cricket Club Finance Bot*

👤 *Players:*
  add player Ravi 819012345678 Bowler NK1
  players

💰 *Club Fees:*
  Prithvi paid 15000 Karthik
  clubfee unpaid
  send club reminders

🏏 *Match (TEAM=div2/div3/nk1/nk2/u15):*
  xi div2 Round1 Ravi,Kumar,Suresh
  update xi div2 Round1 Ravi,Kumar
  matchfee div2 Round1 Ravi=1500,Kumar=1500 Karthik
  match unpaid div2

💸 *Expenses:*
  expense tournament 3000 Entry fee Karthik
  expense sponsorship 100000 Fujisakura

🎯 *Umpire Fees (LEAGUE=div2/div3/nk1/nk2):*
  umpire div2 Round1 Ravi 500 Karthik
  umpire unpaid
  umpire summary

🔄 *Settlements:*
  settle Karthik 15000
  reimburse Satheesh 600 Food refund

📊 *Reports (always reply):*
  summary
  summary March 2026
  admin summary
  players
  clubfee unpaid
  match unpaid div2

ℹ️ Success actions update Google Sheet silently.
   Only errors will get a reply message.

Type *help* anytime."""

def handle_message(msg: str, sender: str = "") -> str:
    msg   = msg.strip()
    lower = msg.lower().strip()

    try:

        # ── HELP / GREETING — always reply ──────────────
        if lower in ["help", "hi", "hello", "start", "menu"]:
            return HELP

        # ── ADD PLAYER — only reply on error ────────────
        # add player Name Phone Role NKTeam
        m = re.match(r"add player (\S+)\s+(\S+)\s+(\S+)\s+(\S+)", msg, re.I)
        if m:
            name, phone, role, nk = m.groups()
            try:
                add_player(name, phone, role, nk)
                print(f"[OK] Player added: {name}")
                return NO_REPLY  # silent success — check Google Sheet
            except Exception as e:
                return f"❌ Error adding player *{name}*: {str(e)}\nCheck format: `add player Name Phone Role NK1`"

        # ── PLAYERS LIST — always reply (query) ─────────
        if lower == "players":
            players = get_all_players()
            if not players:
                return "No players found. Add with: `add player Name Phone Role NK1`"
            lines = [f"  {p.get('#','')}.  {p['Player Name']} ({p.get('Role','')}) — {p.get('NK Team','')}"
                     for p in players]
            return f"👥 *Players ({len(players)}):*\n" + "\n".join(lines)

        # ── MARK CLUB FEE PAID — only reply on error ────
        # Prithvi paid 15000 Karthik
        m = re.match(r"(\w+)\s+paid\s+(\d+)\s*(\w*)", msg, re.I)
        if m and m.group(1).lower() not in ["match", "club", "send"]:
            player  = m.group(1)
            amount  = int(m.group(2))
            paid_to = m.group(3).strip() or "Admin"
            if mark_club_fee_paid(player, paid_to, amount):
                print(f"[OK] Club fee paid: {player} ₹{amount} to {paid_to}")
                return NO_REPLY  # silent success — check Google Sheet
            return (f"❌ *{player.title()}* not found or already paid.\n"
                    f"Check spelling or use `clubfee unpaid` to see list.")

        # ── CLUB FEE UNPAID — always reply (query) ──────
        if re.search(r"clubfee unpaid|unpaid club|club unpaid", lower):
            pending = get_pending_club_fees()
            if not pending:
                return "🎉 All players have paid their club fees!"
            lines = [f"  • {p['Player Name']} — ₹{p.get('Club Fee (₹)','-') or 'not set'}"
                     for p in pending]
            return f"❌ *Pending Club Fees ({len(pending)}):*\n" + "\n".join(lines)

        # ── SEND CLUB REMINDERS — only reply on error ───
        if re.search(r"send club reminder|club reminder|send reminder", lower):
            try:
                from reminder import send_club_fee_reminders
                send_club_fee_reminders()
                print("[OK] Club reminders sent")
                return NO_REPLY  # silent — admins see result in sheet
            except Exception as e:
                return f"❌ Error sending reminders: {str(e)}"

        # ── SET PLAYING XI — only reply on error ────────
        # xi div2 Round1 Ravi,Kumar,Suresh
        m = re.match(r"xi\s+(\S+)\s+(\S+)\s+(.+)", msg, re.I)
        if m:
            tkey, rnd, pl_str = m.groups()
            sheet = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"❌ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            try:
                players = [p.strip() for p in pl_str.replace(";",",").split(",") if p.strip()]
                set_playing_xi(sheet, rnd, players)
                print(f"[OK] XI set: {sheet} {rnd} — {players}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error setting XI: {str(e)}"

        # ── UPDATE PLAYING XI — only reply on error ──────
        # update xi div2 Round1 Ravi,Kumar
        m = re.match(r"update xi\s+(\S+)\s+(\S+)\s+(.+)", msg, re.I)
        if m:
            tkey, rnd, pl_str = m.groups()
            sheet = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"❌ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            try:
                players = [p.strip() for p in pl_str.replace(";",",").split(",") if p.strip()]
                update_playing_xi(sheet, rnd, players)
                print(f"[OK] XI updated: {sheet} {rnd}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error updating XI: {str(e)}"

        # ── RECORD MATCH FEES — only reply on error ──────
        # matchfee div2 Round1 Ravi=1500,Kumar=1500 Karthik
        m = re.match(r"matchfee\s+(\S+)\s+(\S+)\s+(.+?)(?:\s+([A-Za-z]\w*))?$", msg, re.I)
        if m:
            tkey, rnd, fee_str, paid_to = m.groups()
            paid_to = paid_to or "Admin"
            sheet   = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"❌ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            fee_dict = {}
            for part in fee_str.replace(";",",").split(","):
                if "=" in part:
                    n, a = part.split("=", 1)
                    try:
                        fee_dict[n.strip().title()] = int(a.strip())
                    except:
                        pass
            if not fee_dict:
                return "❌ Format: `matchfee div2 Round1 Ravi=1500,Kumar=1500 AdminName`"
            try:
                ok, fail = record_match_fees(sheet, rnd, fee_dict, paid_to)
                print(f"[OK] Match fees: {sheet} {rnd} — OK:{ok} Fail:{fail}")
                if fail:
                    # Only reply if some players were not found
                    return (f"⚠️ Some players not found in {sheet} {rnd}:\n"
                            + fmt(fail) +
                            f"\n\nSet XI first with:\n`xi {tkey} {rnd} {','.join(fail)}`")
                return NO_REPLY  # all good — silent
            except Exception as e:
                return f"❌ Error recording fees: {str(e)}"

        # ── MATCH UNPAID — always reply (query) ──────────
        # match unpaid div2
        m = re.match(r"match unpaid\s+(\S+)", msg, re.I)
        if m:
            tkey  = m.group(1).lower()
            sheet = TEAM_SHEET.get(tkey)
            if not sheet:
                return f"❌ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            unpaid = get_unpaid_match_fees(sheet)
            if not unpaid:
                return f"🎉 All match fees paid for *{sheet}*!"
            lines = [f"  • {u['player']} — {u['round']}" for u in unpaid]
            return f"❌ *Unpaid — {sheet} ({len(unpaid)}):*\n" + "\n".join(lines)

        # ── ADD EXPENSE — only reply on error ────────────
        # expense tournament 3000 Entry fee Karthik
        m = re.match(r"expense\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            cat, amt_str, rest = m.groups()
            cat = cat.lower()
            if cat not in VALID_EXPENSE_CATS:
                return (f"❌ Unknown category `{cat}`.\n"
                        f"Use: tournament · ground · equipment · "
                        f"refreshments · jersey · sponsorship")
            try:
                amt   = int(amt_str)
                parts = rest.strip().split()
                if parts and parts[-1].replace("_","").isalpha():
                    paid_by = parts[-1]
                    note    = " ".join(parts[:-1])
                else:
                    paid_by = "Admin"
                    note    = rest.strip()
                add_expense(cat, amt, note, paid_by)
                print(f"[OK] Expense: {cat} ₹{amt} by {paid_by}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error adding expense: {str(e)}"

        # ── SETTLE — only reply on error ─────────────────
        # settle Karthik 15000 [reason]
        m = re.match(r"settle\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            admin, amt_str, reason = m.groups()
            try:
                amt    = int(amt_str)
                reason = reason.strip() or "Fee handover"
                add_settlement(admin.title(), "Club Account", amt, reason, admin.title())
                print(f"[OK] Settlement: {admin} → Club ₹{amt}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error recording settlement: {str(e)}"

        # ── REIMBURSE — only reply on error ──────────────
        # reimburse Satheesh 600 Food refund
        m = re.match(r"reimburse\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            admin, amt_str, reason = m.groups()
            try:
                amt    = int(amt_str)
                reason = reason.strip() or "Expense reimbursement"
                add_settlement("Club Account", admin.title(), amt, reason, "Admin")
                print(f"[OK] Reimbursement: Club → {admin} ₹{amt}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error recording reimbursement: {str(e)}"

        # ── ADMIN SUMMARY — always reply (query) ─────────
        if re.search(r"admin summary|admin balance", lower):
            players  = get_all_players()
            paid     = [p for p in players if p.get("Fee Status","").lower() == "paid"]
            pending  = [p for p in players if p.get("Fee Status","").lower() in ["pending",""]]
            by_admin = {}
            for p in paid:
                name = p.get("Paid To","Unknown").strip() or "Unknown"
                try:
                    amt = int(str(p.get("Club Fee (₹)",0) or 0))
                except:
                    amt = 0
                by_admin[name] = by_admin.get(name, 0) + amt
            lines = [f"  • {k}: ₹{v:,}" for k,v in by_admin.items()]
            return (f"👤 *Admin Collections (Club Fees):*\n"
                    + ("\n".join(lines) if lines else "  None yet") +
                    f"\n\n✅ Paid: {len(paid)} | ❌ Pending: {len(pending)}")

        # ── SUMMARY — always reply (query) ───────────────
        m = re.match(r"summary\s*(.*)", msg, re.I)
        if m:
            month = m.group(1).strip() or None
            s     = get_summary(month)
            return (
                f"📊 *Summary — {s['month']}*\n\n"
                f"💰 *Club Fees:*\n"
                f"  Paid:    ₹{s['cf_paid']:,}\n"
                f"  Pending: ₹{s['cf_pending']:,}\n\n"
                f"🏏 *Match Fees:*\n"
                f"  Paid:    ₹{s['mf_paid']:,}\n"
                f"  Unpaid:  ₹{s['mf_unpaid']:,}\n\n"
                f"🤝 *Sponsorship:* ₹{s['sponsorship']:,}\n"
                f"💸 *Expenses:*    ₹{s['expenses']:,}\n"
                f"{'─'*24}\n"
                f"✅ *Total In:*  ₹{s['total_in']:,}\n"
                f"💰 *Balance:*   ₹{s['balance']:,}"
            )

        # ── ADD UMPIRE FEE — only reply on error ────────
        # umpire div2 Round1 Ravi 500 Karthik
        m = re.match(r"umpire\s+(\S+)\s+(\S+)\s+(\w+)\s+(\d+)\s*(\w*)", msg, re.I)
        if m:
            league, rnd, umpire, amt_str, paid_by = m.groups()
            league  = league.upper().replace("DIV2","Div-2").replace("DIV3","Div-3")\
                           .replace("DIV-2","Div-2").replace("DIV-3","Div-3")\
                           .replace("NK1","Nk1").replace("NK2","Nk2")
            paid_by = paid_by.strip() or "Admin"
            valid   = ["Div-2","Div-3","Nk1","Nk2"]
            if league not in valid:
                return f"❌ Unknown league `{league}`. Use: div2 · div3 · nk1 · nk2"
            try:
                add_umpire_fee(league, rnd, umpire, int(amt_str), paid_by)
                print(f"[OK] Umpire fee: {league} {rnd} {umpire} ₹{amt_str}")
                return NO_REPLY  # silent — check Google Sheet
            except Exception as e:
                return f"❌ Error adding umpire fee: {str(e)}"

        # ── UMPIRE UNPAID — always reply (query) ─────────
        if re.search(r"umpire unpaid|unpaid umpire", lower):
            unpaid = get_unpaid_umpire_fees()
            if not unpaid:
                return "🎉 All umpire fees have been paid!"
            lines = [f"  • {u['umpire']} — {u['league']} {u['round']} ₹{u['fee']}"
                     for u in unpaid]
            return f"❌ *Unpaid Umpire Fees ({len(unpaid)}):*\n" + "\n".join(lines)

        # ── UMPIRE SUMMARY — always reply (query) ────────
        if re.search(r"umpire summary|umpire total", lower):
            s = get_umpire_summary()
            lines = [f"  • {k}: ₹{v:,}" for k, v in s['by_league'].items()]
            return (
                f"🎯 *Umpire Fees Summary*\n\n"
                f"✅ Total Paid:    ₹{s['total_paid']:,}\n"
                f"⏳ Total Pending: ₹{s['total_pending']:,}\n\n"
                f"*By League:*\n" + ("\n".join(lines) if lines else "  None yet")
            )

        return "❓ Command not recognised. Type *help* to see all commands." 

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return "⚠️ Something went wrong. Please try again or type *help*."
