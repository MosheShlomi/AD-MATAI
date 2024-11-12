import json
import os
import datetime

# Load user data from a JSON file
def load_user_data(file_path='user_data.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            user_data = json.load(file)
            # Convert string dates and times back to datetime objects
            return {
                int(user_id): {
                    "date": datetime.datetime.strptime(data.get("date"), '%Y-%m-%d').date() if data.get("date") else None,
                    "notification_time": datetime.datetime.strptime(data.get("notification_time"), '%H:%M').time() if data.get("notification_time") else None
                }
                for user_id, data in user_data.items()
            }
    return {}

# Save user data to a JSON file
def save_user_data(user_data, file_path='user_data.json'):
    # Convert date and time objects to strings for serialization
    user_data_serializable = {
        user_id: {
            "date": data["date"].isoformat() if data["date"] else None,
            "notification_time": data["notification_time"].strftime('%H:%M') if data["notification_time"] else None
        }
        for user_id, data in user_data.items()
    }
    
    with open(file_path, 'w') as file:
        json.dump(user_data_serializable, file, indent=4)