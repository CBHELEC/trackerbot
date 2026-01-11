import json
from datetime import date
from functions import static_var

POLL_JSON_FILE = static_var.DATA_DIR / "poll_dates.json"

def load_poll_date() -> date:
    """Load the last poll date from a JSON file."""
    try:
        with open(POLL_JSON_FILE, "r") as f:
            data = json.load(f)
            if "last_poll_date" in data:
                return date.fromisoformat(data["last_poll_date"])
            return None
    except FileNotFoundError:
        return None

def save_poll_date(date: date):
    """Save the current poll date to a JSON file."""
    with open(POLL_JSON_FILE, "w") as f:
        json.dump({"last_poll_date": date.isoformat()}, f)

last_poll_date = load_poll_date()