"""
WhatsApp Wound Care & Diabetic Foot bot.
Stack (all free to start): Flask + Twilio WhatsApp Sandbox + Groq (Llama 3.3 70B).

How it works:
  WhatsApp user -> Twilio -> POST /whatsapp (this app) -> Groq LLM -> reply back on WhatsApp

Run:  python app.py   (see README.md for full setup)
"""

import os
from collections import defaultdict, deque

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
from dotenv import load_dotenv

from system_prompt import SYSTEM_PROMPT

load_dotenv()

# ---- Config -----------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TURNS = 6  # how many recent user+bot exchanges to remember per number

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Copy .env.example to .env and fill it in.")

client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# Simple in-memory conversation history, keyed by the sender's WhatsApp number.
# (For production use a real database like SQLite/Redis instead.)
history = defaultdict(lambda: deque(maxlen=MAX_TURNS * 2))


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
            max_tokens=700,
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
    twiml.message(reply)
    return str(twiml)


@app.route("/", methods=["GET"])
def health():
    return "WoundCare WhatsApp bot is running ✅", 200


if __name__ == "__main__":
    # 0.0.0.0 so ngrok can reach it; default port 5000
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
