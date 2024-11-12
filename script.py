import os
import pytz
from dotenv import load_dotenv
from telegram import Update
from datetime import datetime, time, date
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from json_functions import load_user_data, save_user_data
from date_functions import is_valid_date, get_remain_time

WELCOME_TEXT = """
🌟 **שחרור מתקרב? תן לנו לטפל בספירה לאחור!** 🌟

אני כאן כדי לעזור לך לעקוב אחרי תאריך השחרור שלך ולהישאר מעודכן! 
עקוב אחרי הצעדים הבאים כדי להתחיל:

1. הגדרת תאריך השחרור שלך 🗓️: הזן את תאריך השחרור שלך, ואני אזכור אותו עבורך!
2. עדכונים יומיים מותאמים אישית ⏳: בכל יום, תקבל הודעה שתראה כמה זמן נשאר עד לתאריך השחרור, בשעה הנוחה לך! 
3. שמר על תאריך השחרור שלך מעודכן 📅: אם תאריך השחרור הגיע, תקבל הודעת ברכה מיוחדת! 🎉

פשוט השתמש בפקודות הבאות:

- /start - כדי להתחיל או להתחיל מחדש
- /setdate - לעדכון תאריך השחרור
- /settime - להגדרת השעה המועדפת לעדכון יומי
- /howlong - לקבלת מידע על הזמן שנותר עד לשחרור שלך
- /reset - ביטול תאריך שחרור אם תרצה להפסיק את העדכונים
- /cancel - ביטול תהליך הזנת התאריך

הספירה לאחור לשחרור מתחילה כאן! 🚀
"""

EXISTING_DATE_TEXT = "כבר יש לך תאריך שחרור, אבל הוא אופס. יש להזין תאריך השחרור חדש בפורמט DD/MM/YYYY:"
ENTER_DATE_TEXT = "על מנת להתחיל יש להזין תאריך השחרור בפורמט DD/MM/YYYY:"
SET_DATE_PROMPT_TEXT = "יש להזין תאריך השחרור בפורמט DD/MM/YYYY:"
SET_NOTIFICATION_TIME_PROMPT_TEXT = "נא להזין את השעה לקבלת העדכונים בפורמט HH:MM (למשל, 09:00):"
CANCEL_TEXT = "הזנת תאריך בוטלה."
INVALID_DATE_FORMAT_TEXT = "פורמט תאריך לא חוקי. יש להשתמש בפורמט DD/MM/YYYY ויש לוודא שהתאריך תקף."
PAST_DATE_TEXT = "התאריך חייב להיות בעתיד. נא להזין תאריך עתידי חוקי."
UPDATED_DATE_TEXT = "תאריך שחרור המעודכן הוא: {}"
REMAINING_TIME_TEXT = "{} - נשאר עד השחרור ב{}"
RELEASE_TODAY_TEXT = "🎉 מזל טוב! הגיע יום השחרור שלך! 🎉"
RESET_TEXT = "תאריך השחרור שלך אופס! מכאן ולהבא לא יהיה יותר עדכונים עד שלא יוזן תאריך שחרור חדש."
NO_RESET_TEXT = "לא קיים תאריך שחרור."

# Timezone
jerusalem_tz = pytz.timezone('Asia/Jerusalem')

# Environment variable for the bot token
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Step identifiers for conversation
SET_DATE = 1
SET_TIME = 2

# Load user target dates from JSON
user_target_dates = load_user_data()

# Command handlers
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(WELCOME_TEXT)
    
    user_id = update.message.from_user.id
    if user_id in user_target_dates:
        await update.message.reply_text(EXISTING_DATE_TEXT)
        del user_target_dates[user_id]
        save_user_data(user_target_dates)
    else:    
        await update.message.reply_text(ENTER_DATE_TEXT)
    return SET_DATE


async def setdate(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(SET_DATE_PROMPT_TEXT)
    return SET_DATE


async def settime(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(SET_NOTIFICATION_TIME_PROMPT_TEXT)
    return SET_TIME


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(CANCEL_TEXT)
    return ConversationHandler.END

async def reset(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in user_target_dates:
        del user_target_dates[user_id]
        save_user_data(user_target_dates)
        await update.message.reply_text(RESET_TEXT)
    else:    
        await update.message.reply_text(NO_RESET_TEXT)
    return ConversationHandler.END


async def set_date_handler(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    date_input = update.message.text.strip()
    
    if not is_valid_date(date_input):
        await update.message.reply_text(INVALID_DATE_FORMAT_TEXT)
        return SET_DATE
    
    try:
        target_date = datetime.strptime(date_input, '%d/%m/%Y').date()
        formatted_date = target_date.strftime('%d-%m-%Y')
        
        if target_date <= date.today():
            await update.message.reply_text(PAST_DATE_TEXT)
            return SET_DATE

        # Save the new date for the user
        if user_id in user_target_dates:
            user_target_dates[user_id]["date"] = target_date
        else:
            user_target_dates[user_id] = {"date": target_date, "notification_time": None}
            
        save_user_data(user_target_dates)

        await update.message.reply_text(UPDATED_DATE_TEXT.format(formatted_date))
        await update.message.reply_text(get_remain_time(target_date))


    except ValueError:
        await update.message.reply_text(INVALID_DATE_FORMAT_TEXT)
        return SET_DATE

    return ConversationHandler.END


async def set_time_handler(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    time_input = update.message.text.strip()

    try:
        # Parse the time input in HH:MM format
        notification_time = datetime.strptime(time_input, "%H:%M").time()

        # Save the new notification time for the user
        if user_id in user_target_dates:
            user_target_dates[user_id]["notification_time"] = notification_time
        else:
            user_target_dates[user_id] = {"date": None, "notification_time": notification_time}
        
        save_user_data(user_target_dates)

        await update.message.reply_text(f"שעת העדכון עודכנה ל-{notification_time.strftime('%H:%M')} ⏰")
    except ValueError:
        await update.message.reply_text("פורמט שעה לא חוקי. נא להזין את השעה בפורמט HH:MM.")
        return SET_TIME

    return ConversationHandler.END


async def howlong(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    # Check if the user has a release date set
    if user_id not in user_target_dates:
        await update.message.reply_text("אין תאריך שחרור מוגדר. השתמש בפקודה /setdate כדי להגדיר תאריך.")
        return
    
    target_date = user_target_dates[user_id]["date"]
    now = datetime.now(jerusalem_tz)
    release_datetime = datetime.combine(target_date, time(0, 0), tzinfo=jerusalem_tz)

    remaining_time = release_datetime - now
    
    # Check if the release date is in the future
    if remaining_time.total_seconds() <= 0:
        await update.message.reply_text("🎉 מזל טוב! כבר הגעת לתאריך השחרור שלך! 🎉")
        return
    
    await update.message.reply_text(get_remain_time(target_date))
    

async def send_daily_updates(context: CallbackContext):
    now = datetime.now(jerusalem_tz).time()
    users_to_remove = []

    for user_id, data in user_target_dates.items():
        target_date = data.get("date")
        notification_time = data.get("notification_time", time(9, 0))  # Default to 9:00 if not set

        # Only send if it's the user's chosen notification time
        if target_date and notification_time is not None:
            # Only send if it's the user's chosen notification time
            if notification_time.hour == now.hour and notification_time.minute == now.minute:
                today = date.today()

                if target_date == today:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 מזל טוב! הגיע יום השחרור שלך! 🎉"
                    )
                    users_to_remove.append(user_id)

                elif target_date > today:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=get_remain_time(target_date)
                    )

    for user_id in users_to_remove:
        del user_target_dates[user_id]

    save_user_data(user_target_dates)
    

def main():
    print("Bot is running...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    job_queue = application.job_queue
    # job_queue.run_daily(send_daily_updates, time=time(hour=9, minute=0, tzinfo=jerusalem_tz))
    job_queue.run_repeating(send_daily_updates, interval=60, first=0)

    # Organize all conversation handlers into one single handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('setdate', setdate),
            CommandHandler('settime', settime),
        ],
        states={
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date_handler)],
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    # Add the howlong command separately
    application.add_handler(CommandHandler('howlong', howlong))
    
    application.add_handler(CommandHandler('reset', reset))

    application.run_polling()

if __name__ == '__main__':
    main()
