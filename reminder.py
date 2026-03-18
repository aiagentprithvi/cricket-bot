import schedule, time, threading
from datetime import datetime
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NO, ADMIN_NUMBERS

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_wa(to, body):
    try:
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        client.messages.create(from_=TWILIO_WHATSAPP_NO, to=to, body=body)
        print(f"[WA] → {to}")
        return True
    except Exception as e:
        print(f"[WA ERROR] {to}: {e}")
        return False

def notify_admins(msg):
    for admin in ADMIN_NUMBERS:
        send_wa(admin, msg)

def send_club_fee_reminders():
    from sheets import get_pending_club_fees
    print(f"[REMINDER] Running — {datetime.now()}")
    pending = get_pending_club_fees()
    if not pending:
        notify_admins("✅ All players have paid their club fees! 🎉")
        return
    sent = failed = no_phone = 0
    names_sent = []
    for p in pending:
        phone = str(p.get("Phone Number","")).strip()
        name  = p.get("Player Name","")
        if not phone or "XXXXXXXXXX" in phone:
            no_phone += 1
            continue
        msg = (
            f"Hi *{name}* 👋\n\n"
            f"Reminder from *Cricket Club* 🏏\n\n"
            f"Your *club fee* of *₹{p.get('Club Fee (₹)',15000):,}* "
            f"is still *pending*.\n\n"
            f"Please pay at the earliest and reply *PAID* to confirm ✅\n\n"
            f"Thank you! 🙏"
        )
        if send_wa(phone, msg):
            sent += 1; names_sent.append(name)
        else:
            failed += 1
    notify_admins(
        f"📋 *Club Fee Reminders Sent*\n\n"
        f"✅ Sent: {sent} | ❌ Failed: {failed} | 📵 No phone: {no_phone}\n\n"
        f"*Notified:*\n" + "\n".join(f"• {n}" for n in names_sent)
    )

def run_scheduler():
    print("[SCHEDULER] Started")
    print("  → Weekly: Every Monday 10:00 AM")
    print("  → Monthly: 5th of month 6:00 PM")
    schedule.every().monday.at("10:00").do(send_club_fee_reminders)
    def monthly():
        if datetime.now().day == 5:
            send_club_fee_reminders()
    schedule.every().day.at("18:00").do(monthly)
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
