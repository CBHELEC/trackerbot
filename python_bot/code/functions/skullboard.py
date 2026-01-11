import json
from functions import static_var

SKULL_EMOJI = {"💀"}  
REACTION_THRESHOLD = 3 
SKULLBOARD_DATA_FILE = static_var.DATA_DIR / "skullboarded_messages.json"  

def load_skullboarded_messages():
    try:
        with open(SKULLBOARD_DATA_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return list(data.keys())  
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_skullboarded_messages(message_ids):
    with open(SKULLBOARD_DATA_FILE, "w") as f:
        json.dump(message_ids, f)

skullboarded_messages = load_skullboarded_messages()