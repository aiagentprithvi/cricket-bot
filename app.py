from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from agent import handle_message
from reminder import start_scheduler
import os

app = Flask(__name__)
start_scheduler()

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg    = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")
    print(f"[MSG] {sender}: {msg}")
    reply  = handle_message(msg, sender=sender)
    resp   = MessagingResponse()
    resp.message(reply)
    return str(resp)

@app.route("/", methods=["GET"])
def health():
    return "🏏 Cricket Club Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
