"""
WhatsApp Wound Care & Diabetic Foot bot.
Stack (all free to start): Flask + Twilio WhatsApp Sandbox + Groq (Llama 3.3 70B).

How it works:
  WhatsApp user -> Twilio -> POST /whatsapp (this app) -> Groq LLM -> reply back on WhatsApp

Run:  python app.py   (see README.md for full setup)
"""

import os
from collections import defaultdict, deque

import httpx
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
from dotenv import load_dotenv

from system_prompt import SYSTEM_PROMPT

load_dotenv()

# ---- Config -----------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # optional: enables the Telegram bot
MAX_TURNS = 6  # how many recent user+bot exchanges to remember per number

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Copy .env.example to .env and fill it in.")

client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Simple in-memory conversation history, keyed by the sender's WhatsApp number.
# (For production use a real database like SQLite/Redis instead.)
history = defaultdict(lambda: deque(maxlen=MAX_TURNS * 2))


def split_message(text: str, limit: int = 1400):
    """Split a long reply into chunks <= limit chars, breaking on line breaks."""
    if len(text) <= limit:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        # If a single line is itself too long, hard-slice it.
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def get_ai_reply(user_number: str, user_text: str) -> str:
    """Send the message + recent history to Groq and return the bot's reply."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[user_number])
    messages.append({"role": "user", "content": user_text})

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,      # low = more factual / consistent for medical use
            max_tokens=500,       # keep replies short (WhatsApp limit is 1600 chars)
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:  # network / API errors -> friendly bilingual fallback
        print("Groq error:", e)
        return ("⚠️ حصل خطأ مؤقت، جرّب تبعت السؤال تاني.\n"
                "⚠️ Temporary error, please send your question again.")

    # Save this exchange to memory
    history[user_number].append({"role": "user", "content": user_text})
    history[user_number].append({"role": "assistant", "content": reply})
    return reply


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Twilio hits this endpoint whenever a WhatsApp message arrives."""
    user_text = (request.values.get("Body") or "").strip()
    user_number = request.values.get("From", "unknown")

    if not user_text:
        reply = "ابعتلي سؤالك عن العناية بالجروح أو القدم السكري 🦶\nAsk me about wound care or the diabetic foot."
    elif user_text.lower() in {"reset", "مسح", "ابدأ من جديد", "restart"}:
        history.pop(user_number, None)
        reply = "تم مسح المحادثة ✅ | Conversation reset ✅"
    else:
        reply = get_ai_reply(user_number, user_text)

    twiml = MessagingResponse()
    # WhatsApp rejects any single message longer than 1600 chars, so split
    # long replies into multiple messages (each <= 1400 chars, split on newlines).
    for chunk in split_message(reply, 1400):
        twiml.message(chunk)
    # Twilio needs an XML content-type to parse TwiML, so set it explicitly.
    return Response(str(twiml), mimetype="application/xml")


# ---- Telegram bot -----------------------------------------------------------
def send_telegram(chat_id, text):
    """Send one message to a Telegram chat via the Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    except Exception as e:
        print("Telegram send error:", e)


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    """Telegram sends every incoming message here as JSON."""
    if not TELEGRAM_TOKEN:
        return "Telegram token not set", 200

    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    user_text = (message.get("text") or "").strip()

    if not chat_id:
        return "ok", 200  # ignore non-message updates (joins, stickers, etc.)

    if user_text in {"/start", "start"}:
        reply = ("مرحباً! أنا مساعد العناية بالجروح والقدم السكري 🦶\n"
                 "ابعتلي سؤالك بالعربي أو الإنجليزي.\n\n"
                 "Hi! I'm your Wound Care & Diabetic Foot assistant. "
                 "Ask me anything in Arabic or English.")
    elif user_text.lower() in {"/reset", "reset", "مسح"}:
        history.pop(f"tg:{chat_id}", None)
        reply = "تم مسح المحادثة ✅ | Conversation reset ✅"
    elif not user_text:
        reply = "ابعتلي سؤال نصّي عن الجروح أو القدم السكري 🦶 | Please send a text question."
    else:
        reply = get_ai_reply(f"tg:{chat_id}", user_text)

    for chunk in split_message(reply, 3500):  # Telegram limit is 4096 chars
        send_telegram(chat_id, chunk)
    return "ok", 200


@app.route("/", methods=["GET"])
def health():
    return "WoundCare bot is running ✅ (WhatsApp + Telegram)", 200


if __name__ == "__main__":
    # 0.0.0.0 so ngrok can reach it; default port 5000
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
