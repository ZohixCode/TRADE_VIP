import os
import telebot
from flask import Flask, request, abort
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@YourChannel")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/YourChannel")
SUPPORT_USERNAME = os.environ.get("SUPPORT_USERNAME", "YourSupport")

if not BOT_TOKEN or not WEBHOOK_SECRET:
    raise RuntimeError("BOT_TOKEN and WEBHOOK_SECRET must be configured.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎯 چالش 10 برابری", callback_data="challenge"),
        InlineKeyboardButton("💎 عضویت رایگان در Vip", callback_data="free_vip"),
        InlineKeyboardButton("📚 راهنما و قوانین", callback_data="rules"),
        InlineKeyboardButton("📞 ارتباط با پشتیبانی", callback_data="support"),
    )
    return keyboard


def join_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_URL),
        InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join"),
    )
    return keyboard


def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("creator", "administrator", "member", "restricted")
    except Exception:
        return False


@bot.message_handler(commands=["start"])
def start(message):
    if not is_member(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "برای استفاده از ربات، ابتدا عضو کانال شوید و سپس روی بررسی عضویت بزنید.",
            reply_markup=join_keyboard(),
        )
        return

    bot.send_message(
        message.chat.id,
        f"""💎 به ربات اختصاصی Nobody VIP خوش آمدید

درود {message.from_user.first_name} عزیز 👋

اینجا دروازه ورود شما به دنیای حرفه‌ای ترید است. در کانال VIP نوبادی، ما کیفیت را فدای کمیت نمی‌کنیم.

🚀 خدمات ویژه اعضا:
├ 🎯 سیگنال‌های اسپات و فیوچرز
├ 📊 تحلیل‌های تکنیکال و فاندامنتال
├ 🛡 مدیریت سرمایه و روانشناسی بازار
└ 📚 آموزش‌های اختصاصی و پشتیبانی

برای شروع، از منوی زیر اقدام کنید 👇""",
        reply_markup=main_menu(),
    )


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "check_join":
        if is_member(call.from_user.id):
            bot.answer_callback_query(call.id, "عضویت شما تأیید شد ✅")
            bot.send_message(
                call.message.chat.id,
                "خوش آمدید! 👋",
                reply_markup=main_menu(),
            )
        else:
            bot.answer_callback_query(
                call.id,
                "ابتدا عضو کانال شوید و دوباره بررسی کنید.",
                show_alert=True,
            )
        return

    if not is_member(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "ابتدا باید عضو کانال شوید.",
            show_alert=True,
        )
        bot.send_message(
            call.message.chat.id,
            "برای استفاده از ربات، ابتدا عضو کانال شوید.",
            reply_markup=join_keyboard(),
        )
        return

    responses = {
        "challenge": "🎯 بخش چالش 10 برابری\n\nجزئیات این بخش پس از مشخص شدن شرایط چالش اضافه می‌شود.",
        "free_vip": "💎 عضویت رایگان در VIP\n\nشرایط عضویت را از پشتیبانی بپرسید.",
        "rules": "📚 راهنما و قوانین\n\n۱. قوانین کانال را رعایت کنید.\n۲. مدیریت سرمایه را جدی بگیرید.\n۳. هیچ سودی در بازار تضمین‌شده نیست.",
        "support": f"📞 برای ارتباط با پشتیبانی به آیدی زیر مراجعه کنید:\n@{SUPPORT_USERNAME.lstrip('@')}",
    }

    text = responses.get(call.data)
    if text:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text)
    else:
        bot.answer_callback_query(call.id, "این گزینه هنوز تنظیم نشده است.")


@app.route("/", methods=["GET"])
def home():
    return "Nobody VIP bot is running.", 200


@app.route("/api/webhook", methods=["POST"])
def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        abort(403)

    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    except Exception:
        app.logger.exception("Webhook processing failed")
        return "Internal Server Error", 500
