import os
import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from json_functions import load_user_data, save_user_data

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Step identifiers for conversation
SET_DATE = 1

# Dictionary to store the target dates for each user
user_target_dates = load_user_data()

# Function to calculate time remaining
def calculate_remaining_time(date):
    today = datetime.date.today()
    remaining = date - today
    years, months, days = remaining.days // 365, (remaining.days % 365) // 30, (remaining.days % 365) % 30
    return years, months, days

# Function to format the remaining time message (ignores 0 values)
def format_remaining_time(years, months, days):
    time_parts = []
    if years > 0:
        time_parts.append(f"{years} years")
    if months > 0:
        time_parts.append(f"{months} months")
    if days > 0:
        time_parts.append(f"{days} days")
    
    return ", ".join(time_parts)

# Start command: prompts the user to enter the date
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Please enter a date in the format DD/MM/YYYY:')
    return SET_DATE  # Move to the next step to get the date

def is_valid_date(date_string):
    try:
        day, month, year = map(int, date_string.split('/'))
        # Check if the date is valid (this automatically handles month and day limits)
        datetime.date(year, month, day)
        return True
    except ValueError:
        return False
    
# Function to handle the input date and immediately send the remaining time
async def set_date(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    date_input = update.message.text.strip()
    
    if not is_valid_date(date_input):
        await update.message.reply_text('Invalid date format. Please use DD/MM/YYYY and ensure the date is valid.')
        return SET_DATE  # Ask the user to enter the date again
    
    try:
        # Parse date in DD/MM/YYYY format
        target_date = datetime.datetime.strptime(update.message.text, '%d/%m/%Y').date()

        # Check if the date is in the future
        if target_date <= datetime.date.today():
            await update.message.reply_text('The date must be in the future. Please enter a valid future date.')
            return SET_DATE  # Ask the user to enter the date again

        # Store date for this user
        user_target_dates[user_id] = target_date
        save_user_data(user_target_dates)

        # Send a confirmation message
        await update.message.reply_text(f'Target date set to: {target_date}')

        # Immediately calculate and send the remaining time
        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await update.message.reply_text(f"{remaining_time_message} left until {target_date}")

    except ValueError:
        await update.message.reply_text('Invalid date format. Please use DD/MM/YYYY.')
        return SET_DATE  # Ask the user to enter the date again

    return ConversationHandler.END  # End the conversation

# New /setdate command handler to directly set the date
async def setdate(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Please enter a date in the format DD/MM/YYYY:')

# Function to send daily messages
async def send_daily_message(context: CallbackContext):
    user_id = context.job.context
    if user_id in user_target_dates:
        target_date = user_target_dates[user_id]
        years, months, days = calculate_remaining_time(target_date)
        remaining_time_message = format_remaining_time(years, months, days)
        await context.bot.send_message(chat_id=user_id, text=f"{remaining_time_message} left until {target_date}")

# Function to cancel the conversation (in case user wants to stop)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Date input cancelled.")
    return ConversationHandler.END

def main():
    # Indication that the bot is starting successfully
    print("Bot is running...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for setting the date after /start command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    # Handler for the /setdate command
    application.add_handler(CommandHandler('setdate', setdate))

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
