import os
import datetime
import time
import pytz
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from json_functions import load_user_data, save_user_data
from date_functions import format_remaining_time,calculate_remaining_time, is_valid_date

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


jerusalem_tz = pytz.timezone('Asia/Jerusalem')
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Step identifiers for conversation
SET_DATE = 1

user_target_dates = load_user_data()

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(WELCOME_TEXT)
    
    user_id = update.message.from_user.id
    if user_id in user_target_dates:
        await update.message.reply_text("כבר יש לך תאריך שחרור, אבל הוא אופס. יש להזין תאריך השחרור חדש בפורמט DD/MM/YYYY:")
        del user_target_dates[user_id]
        save_user_data(user_target_dates)
    else:    
        await update.message.reply_text('על מנת להתחיל יש להזין תאריך השחרור בפורמט DD/MM/YYYY:')
    return SET_DATE  # Move to the next step to get the date


async def setdate(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('יש להזין תאריך השחרור בפורמט DD/MM/YYYY:')
    return SET_DATE  # Move to the next step to get the date


# Function to cancel the conversation (in case user wants to stop)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("הזנת תאריך בוטלה.")
    return ConversationHandler.END


# Function to handle the input date and immediately send the remaining time
async def set_date_handler(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    date_input = update.message.text.strip()
    
    if not is_valid_date(date_input):
        await update.message.reply_text('פורמט תאריך לא חוקי. יש להשתמש בפורמט DD/MM/YYYY ויש לוודא שהתאריך תקף.')
        return SET_DATE
    
    try:
        # Parse date in DD/MM/YYYY format
        target_date = datetime.datetime.strptime(update.message.text, '%d/%m/%Y').date()
        # To display it in DD-MM-YYYY format:
        formatted_date = target_date.strftime('%d-%m-%Y')
        
        # Check if the date is in the future
        if target_date <= datetime.date.today():
            await update.message.reply_text('התאריך חייב להיות בעתיד. נא להזין תאריך עתידי חוקי.')
            return SET_DATE

        user_target_dates[user_id] = target_date
        save_user_data(user_target_dates)

        await update.message.reply_text(f'תאריך שחרור המעודכן הוא: {formatted_date}')

        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await update.message.reply_text(f"{remaining_time_message} - נשאר עד השחרור ב{formatted_date}")

    except ValueError:
        await update.message.reply_text('פורמט תאריך לא חוקי. אנא השתמש ב-DD/MM/YYYY.')
        return SET_DATE  

    return ConversationHandler.END


async def send_daily_updates(context: CallbackContext):
    users_to_remove = []

    for user_id, target_date in user_target_dates.items():
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


def main():
    print("Bot is running...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Create the job queue to send daily updates
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_updates, time=time(hour=9, minute=0, tzinfo=jerusalem_tz))

    # Conversation handler for setting the date after /start command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('setdate', setdate)],
        states={
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    application.run_polling()
    
# MY COMMANDS
# start
# setdate
# cancel

#Timezone that used is Asia/Jerusalem



if __name__ == '__main__':
    main()