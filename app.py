from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from agent import handle_message
from reminder import start_scheduler
import os
import traceback

app = Flask(__name__)
start_scheduler()

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg    = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")
    print(f"[MSG] {sender}: {msg}")
    try:
        reply = handle_message(msg, sender=sender)
    except Exception as e:
        print(f"[FULL ERROR] {traceback.format_exc()}")
        reply = "⚠️ Something went wrong. Please try again."
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

@app.route("/", methods=["GET"])
def health():
    return "🏏 Cricket Club Bot is running!", 200

@app.route("/test-sheets", methods=["GET"])
def test_sheets():
    try:
        from sheets import get_all_players
        players = get_all_players()
        return f"✅ Connected! Found {len(players)} players.", 200
    except Exception as e:
        return f"❌ Error: {traceback.format_exc()}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
