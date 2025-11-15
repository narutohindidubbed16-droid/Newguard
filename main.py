import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
import re
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# GLOBAL BANWORD LIST
banwords = set()

# ---------------------- START COMMAND ----------------------
@bot.message_handler(commands=['start'])
def start_msg(msg):
    kb = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(
        "➕ Add Me To Your Group",
        url="https://t.me/GuardAntiAIBot?startgroup&admin=delete_messages+restrict_members+invite_users+manage_video_chats"
    )
    kb.add(btn)

    bot.reply_to(
        msg,
        "👋 <b>GUARD ANTI-AI — GOD MODE READY</b>\n"
        "I protect your groups with ultra-aggressive AI scanning.",
        reply_markup=kb
    )

# ---------------------- ADMIN CHECK ------------------------
def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

# ---------------------- ADD BANWORD ------------------------
@bot.message_handler(commands=['banword'])
def add_banword(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        return bot.reply_to(msg, "⚠ Only admins can use this.")

    word = msg.text.replace("/banword", "").strip()
    if not word:
        return bot.reply_to(msg, "📌 Type a word: /banword <word>")

    banwords.add(word.lower())
    bot.reply_to(msg, f"🚫 Banword added: <b>{word}</b>")

# ---------------------- REMOVE BANWORD ----------------------
@bot.message_handler(commands=['unbanword'])
def remove_banword(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        return bot.reply_to(msg, "⚠ Only admins can use this.")

    word = msg.text.replace("/unbanword", "").strip()
    if not word:
        return bot.reply_to(msg, "📌 Type: /unbanword <word>")

    try:
        banwords.remove(word.lower())
        bot.reply_to(msg, f"✅ Removed: <b>{word}</b>")
    except:
        bot.reply_to(msg, "❌ Word not found.")

# ---------------------- SPAM SCAN ENGINE ----------------------
def is_spam(text):
    if not text:
        return False

    for w in banwords:
        if w in text.lower():
            return True

    if re.search(r"(http|https|t\.me|\.com|www\.)", text):
        return True

    if len(re.findall(r"[^\w\s,.!?]", text)) > 6:
        return True

    if sum(1 for c in text if c.isupper()) > 20:
        return True

    if re.search(r"(.)\1{5,}", text):
        return True

    if re.search(r"[\u0336\u0335\u034f\u202e\u202d\u2066\u2067\u2068]", text):
        return True

    return False

# ---------------------- MAIN MODERATION ----------------------
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'document'])
def moder(msg):
    # block forwarded messages
    if msg.forward_from or msg.forward_from_chat:
        bot.delete_message(msg.chat.id, msg.id)
        return
    
    # block spam content
    if msg.text and is_spam(msg.text):
        try:
            bot.delete_message(msg.chat.id, msg.id)
            bot.restrict_chat_member(msg.chat.id, msg.from_user.id, until_date=3600 * 12)
        except:
            pass


# ---------------------- FLASK WEBHOOK SERVER ----------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT IS RUNNING"

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode())
    bot.process_new_updates([update])
    return "OK", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(f"https://newguard.onrender.com/{BOT_TOKEN}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
