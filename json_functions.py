import json
import os
import datetime
import aiofiles
import json

# Load user data from a JSON file
def load_user_data(file_path='user_data.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            user_data = json.load(file)
            # Convert string dates back to datetime.date objects
            return {int(user_id): datetime.datetime.strptime(date_str, '%Y-%m-%d').date() for user_id, date_str in user_data.items()}
    return {}


# Save user data to a JSON file
def save_user_data(user_data, file_path='user_data.json'):
    # Convert date objects to strings in the format 'YYYY-MM-DD'
    user_data_serializable = {user_id: target_date.isoformat() for user_id, target_date in user_data.items()}
    
    with open(file_path, 'w') as file:
        json.dump(user_data_serializable, file)
