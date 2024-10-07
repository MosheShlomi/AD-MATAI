import datetime

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
    today = datetime.date.today()
    remaining = date - today
    years, months, days = remaining.days // 365, (remaining.days % 365) // 30, (remaining.days % 365) % 30
    return years, months, days

def is_valid_date(date_string):
    try:
        day, month, year = map(int, date_string.split('/'))
        # Check if the date is valid (this automatically handles month and day limits)
        datetime.date(year, month, day)
        return True
    except ValueError:
        return False