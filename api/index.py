import os
import telebot
from flask import Flask, request, abort
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

CHANNEL_ID = int(os.environ.get("CHANNEL_USERNAME", "-1004449141283"))
CHANNEL_URL = os.environ.get(
    "CHANNEL_URL",
    "https://t.me/+b0pOJ1W-F_4xMjM0"
)
SUPPORT_USERNAME = os.environ.get("SUPPORT_USERNAME", "YourSupport")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "🎯 چالش 10 برابری",
            callback_data="challenge"
        ),
        InlineKeyboardButton(
            "💎 عضویت رایگان در Vip",
            callback_data="free_vip"
        ),
        InlineKeyboardButton(
            "📚 راهنما و قوانین",
            callback_data="rules"
        ),
        InlineKeyboardButton(
            "📞 ارتباط با پشتیبانی",
            callback_data="support"
        )
    )

    return keyboard


def join_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "📢 عضویت در کانال",
            url=CHANNEL_URL
        ),
        InlineKeyboardButton(
            "✅ بررسی عضویت",
            callback_data="check_join"
        )
    )

    return keyboard


def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)

        return member.status in (
            "creator",
            "administrator",
            "member",
            "restricted"
        ) and getattr(member, "is_member", True)

    except Exception:
        app.logger.exception("Could not check channel membership")
        return False


def send_welcome(chat_id, first_name):
    text = f"""💎 به ربات اختصاصی Nobody VIP خوش آمدید

درود {first_name} عزیز 👋

اینجا دروازه ورود شما به دنیای حرفه‌ای ترید است. در کانال VIP نوبادی، ما کیفیت را فدای کمیت نمی‌کنیم.

🚀 خدمات ویژه اعضا:
├ 🎯 سیگنال‌های اسپات و فیوچرز
├ 📊 تحلیل‌های تکنیکال و فاندامنتال روزانه
├ 🛡 مدیریت سرمایه و روانشناسی بازار
└ 📚 آموزش‌های اختصاصی و پشتیبانی

برای شروع، از منوی زیر اقدام کنید 👇"""

    bot.send_message(
        chat_id,
        text,
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["start"])
def start(message):
    if not is_member(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "سلام! 👋\n\nبرای استفاده از ربات، ابتدا عضو کانال شوید و سپس روی دکمه بررسی عضویت بزنید.",
            reply_markup=join_keyboard()
        )
        return

    send_welcome(
        message.chat.id,
        message.from_user.first_name or "دوست عزیز"
    )


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "check_join":
        if is_member(call.from_user.id):
            bot.answer_callback_query(
                call.id,
                "عضویت شما تأیید شد ✅"
            )

            send_welcome(
                call.message.chat.id,
                call.from_user.first_name or "دوست عزیز"
            )
        else:
            bot.answer_callback_query(
                call.id,
                "هنوز عضویت شما تأیید نشده است. ابتدا عضو کانال شوید.",
                show_alert=True
            )

        return

    if not is_member(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "برای استفاده از این بخش ابتدا عضو کانال شوید.",
            show_alert=True
        )

        bot.send_message(
            call.message.chat.id,
            "ابتدا عضو کانال شوید:",
            reply_markup=join_keyboard()
        )

        return

    responses = {
        "challenge": (
            "🎯 چالش 10 برابری\n\n"
            "برای اطلاع از شرایط و قوانین این چالش، "
            "با پشتیبانی ارتباط بگیرید.\n\n"
            "توجه: هیچ سودی در بازارهای مالی تضمین‌شده نیست."
        ),

        "free_vip": (
            "💎 عضویت رایگان در VIP\n\n"
            "برای اطلاع از شرایط عضویت، "
            "با پشتیبانی ارتباط بگیرید."
        ),

        "rules": (
            "📚 راهنما و قوانین\n\n"
            "۱. قوانین کانال را رعایت کنید.\n"
            "۲. مدیریت سرمایه را جدی بگیرید.\n"
            "۳. اطلاعات حساب و رمزهای خود را در اختیار دیگران نگذارید.\n"
            "۴. فعالیت در بازارهای مالی با ریسک همراه است.\n"
            "۵. هیچ سودی تضمین‌شده نیست."
        ),

        "support": (
            "📞 ارتباط با پشتیبانی\n\n"
            f"آیدی پشتیبانی: @{SUPPORT_USERNAME.lstrip('@')}"
        )
    }

    response = responses.get(call.data)

    if response:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, response)
    else:
        bot.answer_callback_query(
            call.id,
            "این گزینه هنوز تنظیم نشده است."
        )


@app.route("/", methods=["GET"])
def home():
    return "Nobody VIP bot is running.", 200


@app.route("/api/webhook", methods=["POST"])
def webhook():
    provided_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        ""
    )

    if provided_secret != WEBHOOK_SECRET:
        abort(403)

    try:
        update = telebot.types.Update.de_json(
            request.get_data().decode("utf-8")
        )

        bot.process_new_updates([update])

        return "OK", 200

    except Exception:
        app.logger.exception("Webhook processing failed")
        return "Internal Server Error", 500
