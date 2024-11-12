from datetime import datetime, date, time
import pytz

# Timezone
jerusalem_tz = pytz.timezone('Asia/Jerusalem')

# Function to format the remaining time message (ignores 0 values)
def format_remaining_time(years, months, days):
    time_parts = []
    if years > 0:
        time_parts.append(f"{years} שנים")
    if months > 0:
        time_parts.append(f"{months} חודשים")
    if days > 0:
        time_parts.append(f"{days} ימים")
    
    return ", ".join(time_parts)

# Function to calculate time remaining
def calculate_remaining_time(date):
    today = date.today()
    remaining = date - today
    years, months, days = remaining.days // 365, (remaining.days % 365) // 30, (remaining.days % 365) % 30
    return years, months, days

def is_valid_date(date_string):
    try:
        day, month, year = map(int, date_string.split('/'))
        # Check if the date is valid (this automatically handles month and day limits)
        date(year, month, day)
        return True
    except ValueError:
        return False
    
def get_remain_time(target_date: date) -> str: 
    now = datetime.now(jerusalem_tz)
    release_datetime = datetime.combine(target_date, time(0, 0), tzinfo=jerusalem_tz)

    remaining_time = release_datetime - now
    
    days = remaining_time.days
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    years = days // 365
    months = (days % 365) // 30
    days = days % 30

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

    remaining_time_message = "נשארו לך: " + ", ".join(time_parts) + " עד השחרור! 🚀"

    return remaining_time_message
