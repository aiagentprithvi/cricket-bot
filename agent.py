import re
from config import TEAM_SHEET, ADMIN_NUMBERS, VALID_EXPENSE_CATS
from sheets import (
    get_all_players, add_player, get_player_by_phone,
    mark_club_fee_paid, get_pending_club_fees,
    set_playing_xi, update_playing_xi,
    record_match_fees, get_unpaid_match_fees,
    add_expense, add_settlement, get_summary,
)

def is_admin(sender):
    return sender in ADMIN_NUMBERS

def fmt(items):
    return "\n".join(f"  • {i}" for i in items) if items else "  None"

# ── Help messages ────────────────────────────────────────

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

🔄 *Settlements:*
  settle Karthik 15000
  reimburse Satheesh 600 Food refund

📊 *Reports:*
  summary
  summary March 2026
  admin summary

Type *help* anytime."""

# ── Main handler ─────────────────────────────────────────

def handle_message(msg: str, sender: str = "") -> str:
    msg   = msg.strip()
    lower = msg.lower().strip()

    try:

        # ── PLAYER REPLIES "PAID" TO REMINDER ───────────
        if lower == "paid":
            phone  = sender.replace("whatsapp:", "").strip()
            player = get_player_by_phone(phone)
            if player:
                from reminder import notify_admins
                if mark_club_fee_paid(player, "Self-confirmed"):
                    notify_admins(
                        f"✅ *Payment Confirmed!*\n"
                        f"*{player}* confirmed club fee payment via WhatsApp.\n"
                        f"Sheet updated automatically 📊"
                    )
                    return (f"✅ Thank you *{player}*!\n"
                            f"Your club fee has been recorded. See you on the field! 🏏")
                return "⚠️ No pending fee found for your number. Contact admin."
            return "⚠️ Your number is not registered. Please contact your admin."

        # ── HELP / GREETING ─────────────────────────────
        if lower in ["help", "hi", "hello", "start", "menu"]:
            return HELP

        # ── ADD PLAYER ──────────────────────────────────
        # add player Name Phone Role NKTeam
        m = re.match(r"add player (\S+)\s+(\S+)\s+(\S+)\s+(\S+)", msg, re.I)
        if m:
            name, phone, role, nk = m.groups()
            no = add_player(name, phone, role, nk)
            return (f"✅ Player *{name.title()}* added as #{no}\n"
                    f"Phone: {phone} | Role: {role.title()} | Team: {nk.upper()}\n"
                    f"Club fee ₹{15000:,} set to *Pending*")

        # ── PLAYERS LIST ────────────────────────────────
        if lower == "players":
            players = get_all_players()
            active  = [p for p in players if p.get("Status","active").lower() != "inactive"]
            lines   = [f"  {i+1}. {p['Player Name']} ({p.get('Role','')}) — {p.get('NK Team','')}"
                       for i, p in enumerate(active)]
            return f"👥 *Players ({len(active)}):*\n" + "\n".join(lines)

        # ── MARK CLUB FEE PAID ──────────────────────────
        # Prithvi paid 15000 Karthik
        m = re.match(r"(\w+)\s+paid\s+(\d+)\s*(\w*)", msg, re.I)
        if m and m.group(1).lower() not in ["match","club","send"]:
            player  = m.group(1)
            amount  = int(m.group(2))
            paid_to = m.group(3).strip() or "Admin"
            if mark_club_fee_paid(player, paid_to, amount):
                from reminder import notify_admins
                notify_admins(
                    f"💰 *Club Fee Received!*\n"
                    f"Player: *{player.title()}*\n"
                    f"Amount: *₹{amount:,}*\n"
                    f"Collected by: *{paid_to}*\n"
                    f"Sheet updated ✅"
                )
                return (f"✅ Club fee *₹{amount:,}* for *{player.title()}* marked as *Paid*\n"
                        f"Collected by: *{paid_to}* | Sheet updated 📊")
            return (f"⚠️ *{player.title()}* not found or already paid.\n"
                    f"Check name or use `clubfee unpaid` to see list.")

        # ── CLUB FEE UNPAID LIST ─────────────────────────
        if re.search(r"clubfee unpaid|unpaid club|club unpaid", lower):
            pending = get_pending_club_fees()
            if not pending:
                return "🎉 All players have paid their club fees!"
            lines = [f"  • {p['Player Name']} — ₹{p.get('Club Fee (₹)','-')}"
                     for p in pending]
            return f"❌ *Pending Club Fees ({len(pending)}):*\n" + "\n".join(lines)

        # ── SEND CLUB REMINDERS MANUALLY ────────────────
        if re.search(r"send club reminder|club reminder|send reminder", lower):
            from reminder import send_club_fee_reminders
            send_club_fee_reminders()
            return "📨 Reminders sent to all pending players now!"

        # ── SET PLAYING XI ──────────────────────────────
        # xi div2 Round1 Ravi,Kumar,Suresh,...
        m = re.match(r"xi\s+(\S+)\s+(\S+)\s+(.+)", msg, re.I)
        if m:
            tkey, rnd, pl_str = m.groups()
            sheet = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"⚠️ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            players = [p.strip() for p in pl_str.replace(";",",").split(",") if p.strip()]
            added   = set_playing_xi(sheet, rnd, players)
            return (f"✅ *Playing XI set — {sheet} | {rnd}*\n"
                    f"Players ({len(added)}):\n" + fmt(added) +
                    f"\n\nAll marked *Unpaid*. Send fees after match with:\n"
                    f"`matchfee {tkey} {rnd} Ravi=1500,Kumar=1500 AdminName`")

        # ── UPDATE PLAYING XI ────────────────────────────
        # update xi div2 Round1 Ravi,Kumar,...
        m = re.match(r"update xi\s+(\S+)\s+(\S+)\s+(.+)", msg, re.I)
        if m:
            tkey, rnd, pl_str = m.groups()
            sheet = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"⚠️ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            players = [p.strip() for p in pl_str.replace(";",",").split(",") if p.strip()]
            updated = update_playing_xi(sheet, rnd, players)
            return (f"✅ *Playing XI updated — {sheet} | {rnd}*\n"
                    f"New XI ({len(updated)}):\n" + fmt(updated))

        # ── RECORD MATCH FEES ────────────────────────────
        # matchfee div2 Round1 Ravi=1500,Kumar=1500 Karthik
        m = re.match(r"matchfee\s+(\S+)\s+(\S+)\s+(.+?)(?:\s+([A-Za-z]\w*))?$", msg, re.I)
        if m:
            tkey, rnd, fee_str, paid_to = m.groups()
            paid_to = paid_to or "Admin"
            sheet   = TEAM_SHEET.get(tkey.lower())
            if not sheet:
                return f"⚠️ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            fee_dict = {}
            for part in fee_str.replace(";",",").split(","):
                if "=" in part:
                    n, a = part.split("=", 1)
                    try: fee_dict[n.strip().title()] = int(a.strip())
                    except: pass
            if not fee_dict:
                return "⚠️ Format: `matchfee div2 Round1 Ravi=1500,Kumar=1500 AdminName`"
            ok, fail = record_match_fees(sheet, rnd, fee_dict, paid_to)
            reply = f"✅ *Match fees recorded — {sheet} | {rnd}*\n"
            if ok:   reply += f"\nPaid ({len(ok)}):\n" + fmt(ok)
            if fail: reply += f"\n\n⚠️ Not found (set XI first):\n" + fmt(fail)
            return reply

        # ── MATCH UNPAID LIST ────────────────────────────
        # match unpaid div2
        m = re.match(r"match unpaid\s+(\S+)", msg, re.I)
        if m:
            tkey  = m.group(1).lower()
            sheet = TEAM_SHEET.get(tkey)
            if not sheet:
                return f"⚠️ Unknown team `{tkey}`. Use: div2 · div3 · nk1 · nk2 · u15"
            unpaid = get_unpaid_match_fees(sheet)
            if not unpaid:
                return f"🎉 All match fees paid for *{sheet}*!"
            lines  = [f"  • {u['player']} — {u['round']}" for u in unpaid]
            return f"❌ *Unpaid — {sheet} ({len(unpaid)}):*\n" + "\n".join(lines)

        # ── ADD EXPENSE / SPONSORSHIP ────────────────────
        # expense tournament 3000 Entry fee Karthik
        # expense sponsorship 100000 Fujisakura
        m = re.match(r"expense\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            cat, amt_str, rest = m.groups()
            cat = cat.lower()
            if cat not in VALID_EXPENSE_CATS:
                return (f"⚠️ Unknown category `{cat}`.\n"
                        f"Use: tournament · ground · equipment · refreshments · jersey · sponsorship")
            amt   = int(amt_str)
            parts = rest.strip().split()
            # Last word is admin name if it looks like a name (no digits)
            if parts and parts[-1].replace("_","").isalpha():
                paid_by = parts[-1]
                note    = " ".join(parts[:-1])
            else:
                paid_by = "Admin"
                note    = rest.strip()
            add_expense(cat, amt, note, paid_by)
            label = "💰 Sponsorship income" if cat == "sponsorship" else "💸 Expense"
            return (f"{label} recorded!\n"
                    f"Category: *{cat.title()}* | Amount: *₹{amt:,}*\n"
                    f"Note: {note} | By: {paid_by} | Sheet updated 📊")

        # ── SETTLE (admin → club) ─────────────────────────
        # settle Karthik 15000 [reason]
        m = re.match(r"settle\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            admin, amt_str, reason = m.groups()
            amt    = int(amt_str)
            reason = reason.strip() or "Fee handover"
            add_settlement(admin.title(), "Club Account", amt, reason, admin.title())
            from reminder import notify_admins
            notify_admins(
                f"🔄 *Settlement Recorded!*\n"
                f"*{admin.title()}* → Club Account\n"
                f"Amount: ₹{amt:,} | Reason: {reason}\n"
                f"Admins sheet updated ✅"
            )
            return (f"✅ Settlement recorded!\n"
                    f"*{admin.title()}* handed *₹{amt:,}* to Club Account\n"
                    f"Admins sheet updated 📊")

        # ── REIMBURSE (club → admin) ──────────────────────
        # reimburse Satheesh 600 Food refund
        m = re.match(r"reimburse\s+(\w+)\s+(\d+)\s*(.*)", msg, re.I)
        if m:
            admin, amt_str, reason = m.groups()
            amt    = int(amt_str)
            reason = reason.strip() or "Expense reimbursement"
            add_settlement("Club Account", admin.title(), amt, reason, "Admin")
            from reminder import notify_admins
            notify_admins(
                f"🔄 *Reimbursement Recorded!*\n"
                f"Club Account → *{admin.title()}*\n"
                f"Amount: ₹{amt:,} | Reason: {reason}\n"
                f"Admins sheet updated ✅"
            )
            return (f"✅ Reimbursement recorded!\n"
                    f"Club Account paid *{admin.title()}* ₹{amt:,}\n"
                    f"Reason: {reason} | Sheet updated 📊")

        # ── ADMIN SUMMARY ─────────────────────────────────
        if re.search(r"admin summary|admin balance", lower):
            players = get_all_players()
            paid    = [p for p in players if p.get("Fee Status","").lower() == "paid"]
            pending = [p for p in players if p.get("Fee Status","").lower() == "pending"]
            lines   = []
            for name in ["Karthik","SK","Satheesh","Club Account"]:
                coll = sum(int(str(p.get("Club Fee (₹)",0) or 0))
                           for p in paid if p.get("Paid To","").lower() == name.lower())
                lines.append(f"  • {name}: ₹{coll:,} collected")
            return (f"👤 *Admin Collections (Club Fees):*\n"
                    + "\n".join(lines) +
                    f"\n\n*Paid:* {len(paid)} | *Pending:* {len(pending)}\n"
                    f"For full breakdown see Admins sheet in Google Sheets.")

        # ── SUMMARY ──────────────────────────────────────
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

        return "❓ Command not recognised. Type *help* to see all commands."

    except Exception as e:
        print(f"[ERROR] {e}")
        return "⚠️ Something went wrong. Please try again or type *help*."
