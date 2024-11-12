import os
import datetime
import time
import pytz
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from json_functions import load_user_data, save_user_data
from date_functions import format_remaining_time, calculate_remaining_time, is_valid_date

WELCOME_TEXT = """
🌟 **שחרור מתקרב? תן לנו לטפל בספירה לאחור!** 🌟

אני כאן כדי לעזור לך לעקוב אחרי תאריך השחרור שלך! 
פשוט עקוב אחרי הצעדים הפשוטים הבאים:

1. *הזנת תאריך השחרור שלך* 🗓️: הזן את תאריך השחרור שלך, ואני אזכור אותו עבורך!
2. *קבלת עדכונים יומיים* ⏳: בכל יום, אשלח לך הודעה שתראה כמה זמן נשאר עד לתאריך השחרור שלך! 🎉
3. *שמור על עצמך מעודכן* 📅: אם תאריך השחרור שלך הוא היום, אשלח לך הודעת ברכות מיוחדת! 

כשאתה מוכן או שאתה רוצה להתחיל מחדש, פשוט לחץ על /start! 
אם אתה רוצה לשנות את התאריך שלך, השתמש ב-/setdate. 
ואם אתה רוצה לעצור, פשוט כתוב /cancel.

בוא ניהנה מהספירה לאחור לשחרור שלך! 🚀
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

async def set_date_handler(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    date_input = update.message.text.strip()
    
    if not is_valid_date(date_input):
        await update.message.reply_text(INVALID_DATE_FORMAT_TEXT)
        return SET_DATE
    
    try:
        target_date = datetime.datetime.strptime(date_input, '%d/%m/%Y').date()
        formatted_date = target_date.strftime('%d-%m-%Y')
        
        if target_date <= datetime.date.today():
            await update.message.reply_text(PAST_DATE_TEXT)
            return SET_DATE

        # Save the new date for the user
        if user_id in user_target_dates:
            user_target_dates[user_id]["date"] = target_date
        else:
            user_target_dates[user_id] = {"date": target_date, "notification_time": None}
            
        save_user_data(user_target_dates)

        await update.message.reply_text(UPDATED_DATE_TEXT.format(formatted_date))

        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await update.message.reply_text(REMAINING_TIME_TEXT.format(remaining_time_message, formatted_date))

    except ValueError:
        await update.message.reply_text(INVALID_DATE_FORMAT_TEXT)
        return SET_DATE

    return ConversationHandler.END

async def send_daily_updates(context: CallbackContext):
    now = datetime.datetime.now(jerusalem_tz).time()
    users_to_remove = []

    for user_id, data in user_target_dates.items():
        target_date = data.get("date")
        notification_time = data.get("notification_time", datetime.time(9, 0))  # Default to 9:00 if not set

        # Only send if it's the user's chosen notification time
        if target_date and notification_time == now:
            today = datetime.date.today()

            if target_date == today:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 מזל טוב! הגיע יום השחרור שלך! 🎉"
                )
                users_to_remove.append(user_id)

            elif target_date > today:
                years, months, days = calculate_remaining_time(target_date)
                remaining_time_message = format_remaining_time(years, months, days)
                formatted_date = target_date.strftime('%d-%m-%Y')
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{remaining_time_message} - נשאר עד השחרור ב{formatted_date}"
                )

    for user_id in users_to_remove:
        del user_target_dates[user_id]

    save_user_data(user_target_dates)



# Function to handle time input and validate it
async def set_time_handler(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    time_input = update.message.text.strip()

    try:
        # Parse the time input in HH:MM format
        notification_time = datetime.datetime.strptime(time_input, "%H:%M").time()

        # Save the new notification time for the user
        if user_id in user_target_dates:
            user_target_dates[user_id]["notification_time"] = notification_time
        else:
            user_target_dates[user_id] = {"date": None, "notification_time": notification_time}
        
        save_user_data(user_target_dates)  # Save the updated user data

        # Confirm the update to the user
        await update.message.reply_text(f"שעת העדכון עודכנה ל-{notification_time.strftime('%H:%M')} ⏰")
    except ValueError:
        # Handle invalid time format
        await update.message.reply_text("פורמט שעה לא חוקי. נא להזין את השעה בפורמט HH:MM.")
        return SET_TIME  # Ask for the time input again if invalid

    return ConversationHandler.END


# Function to calculate and display the exact time left until the release date with emojis and without zero components
async def howlong(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    # Check if the user has a release date set
    if user_id not in user_target_dates:
        await update.message.reply_text("אין תאריך שחרור מוגדר. השתמש בפקודה /setdate כדי להגדיר תאריך.")
        return
    
    # Get the target release date
    target_date = user_target_dates[user_id]
    now = datetime.datetime.now(jerusalem_tz)
    release_datetime = datetime.datetime.combine(target_date, datetime.time(0, 0), tzinfo=jerusalem_tz)

    # Calculate the difference between now and the release date
    remaining_time = release_datetime - now
    
    # Check if the release date is in the future
    if remaining_time.total_seconds() <= 0:
        await update.message.reply_text("🎉 מזל טוב! כבר הגעת לתאריך השחרור שלך! 🎉")
        return
    
    # Extract time components
    days = remaining_time.days
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Calculate years and months
    years = days // 365
    months = (days % 365) // 30
    days = days % 30

    # Build the remaining time message without any zero components
    time_parts = []
    if years > 0:
        time_parts.append(f"{years} שנים 🗓️")
    if months > 0:
        time_parts.append(f"{months} חודשים 📅")
    if days > 0:
        time_parts.append(f"{days} ימים 🌞")
    if hours > 0:
        time_parts.append(f"{hours} שעות ⏰")
    if minutes > 0:
        time_parts.append(f"{minutes} דקות ⏳")
    if seconds > 0:
        time_parts.append(f"{seconds} שניות 🕰️")

    # Join the parts with commas
    remaining_time_message = "נשארו לך: " + ", ".join(time_parts) + " עד השחרור! 🚀"

    # Send the remaining time message to the user
    await update.message.reply_text(remaining_time_message)


def main():
    print("Bot is running...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_updates, time=time(hour=9, minute=0, tzinfo=jerusalem_tz))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('setdate', setdate)],
        states={
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)
    
        # Conversation handler for setting the notification time with /settime
    settime_handler = ConversationHandler(
        entry_points=[CommandHandler('settime', settime)],
        states={
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(settime_handler)
    
    application.add_handler(CommandHandler('howlong', howlong))

    application.run_polling()

if __name__ == '__main__':
    main()
