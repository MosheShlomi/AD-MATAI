# Release Date Tracker Bot

🌟 **שחרור מתקרב? תן לנו לטפל בספירה לאחור!** 🌟

This Telegram bot helps soldiers track their release dates from service. It provides daily updates on the time remaining until the specified release date and sends special messages on the release date itself.

## Features

- 📅 **Set Release Date**: Soldiers can enter their release date, and the bot will remember it.
- ⏳ **Daily Updates at Custom Time**: The bot sends a daily message showing how much time is left until the release date, at a time chosen by the user.
- 🎉 **Release Day Celebration**: A special message is sent on the release date.

## Commands

- `/start` - Begin tracking your release date or reset if you've already started
- `/setdate` - Set or update your release date
- `/settime` - Set the preferred time to receive daily updates
- `/howlong` - Check how much time is left until your release
- `/reset` - Clear the release date and stop updates
- `/cancel` - Cancel the current input process

## Installation

To set up this project, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MosheShlomi/AD-MATAI.git
   cd AD-MATAI
   ```

2. **Create a Telegram bot with BotFather and get the bot token.**

3. **Create a `.env` file and add the bot token:**
   ```bash
   TELEGRAM_BOT_TOKEN=<your-bot-token>
   ```

4. **Install packages from requirements.txt file:**
   ```bash
   pip install --upgrade pip setuptools wheel  && pip install --prefer-binary -r requirements.txt
   ```

5. **Run the script:**
   ```bash
   python script.py
   ```

You can also try the bot directly: [https://t.me/ad_matai_bot](https://t.me/ad_matai_bot)

