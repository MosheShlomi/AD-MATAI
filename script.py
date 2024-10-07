import os
import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from json_functions import load_user_data, save_user_data
from date_functions import format_remaining_time,calculate_remaining_time, is_valid_date

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Step identifiers for conversation
SET_DATE = 1

user_target_dates = load_user_data()

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('על מנת להתחיל יש להזין תאריך השחרור בפורמט DD/MM/YYYY:')
    return SET_DATE  # Move to the next step to get the date

async def setdate(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('יש להזין תאריך השחרור בפורמט DD/MM/YYYY:')
    return SET_DATE  # Move to the next step to get the date

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

        # Immediately calculate and send the remaining time
        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await update.message.reply_text(f"{remaining_time_message} - נשאר עד השחרור ב{formatted_date}")

    except ValueError:
        await update.message.reply_text('פורמט תאריך לא חוקי. אנא השתמש ב-DD/MM/YYYY.')
        return SET_DATE  # Ask the user to enter the date again

    return ConversationHandler.END  # End the conversation



# Function to send daily messages
async def send_daily_message(context: CallbackContext):
    user_id = context.job.context
    if user_id in user_target_dates:
        target_date = user_target_dates[user_id]
        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await context.bot.send_message(chat_id=user_id, text=f"{remaining_time_message} left until {target_date.strftime('%d/%m/%Y')}")

async def schedule_daily_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Schedule a daily job
    context.job_queue.run_daily(send_daily_message, time=datetime.time(hour=9, minute=0), context=user_id)

    await update.message.reply_text("Daily reminders have been scheduled for 9:00 AM.")

async def view_date(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_target_dates:
        target_date = user_target_dates[user_id]
        await update.message.reply_text(f'Your target date is set to: {target_date.strftime("%d/%m/%Y")}')
    else:
        await update.message.reply_text("You have not set a target date yet.")

async def set_reminder(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_target_dates:
        await update.message.reply_text("You need to set a target date first using /setdate.")
        return

    # Example interval: 1 week before the target date
    interval = datetime.timedelta(days=7)
    target_date = user_target_dates[user_id]
    reminder_date = target_date - interval

    # Schedule a job to send a reminder
    context.job_queue.run_once(send_reminder_message, reminder_date, context=user_id)

    await update.message.reply_text(f"Reminder set for {reminder_date.strftime('%d/%m/%Y')} - You will be notified then.")

async def send_reminder_message(context: CallbackContext):
    user_id = context.job.context
    await context.bot.send_message(chat_id=user_id, text="This is your reminder for your target date!")


# Function to cancel the conversation (in case user wants to stop)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("הזנת תאריך בוטלה.")
    return ConversationHandler.END

def main():
    # Indication that the bot is starting successfully
    print("Bot is running...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for setting the date after /start command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('setdate', setdate)],
        states={
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler('schedule', schedule_daily_message))

    # Inside the main function
    application.add_handler(CommandHandler('viewdate', view_date))
    application.add_handler(CommandHandler('remind', set_reminder))

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
