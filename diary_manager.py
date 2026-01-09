import json
import os
from datetime import datetime, timedelta

DATA_FILE = "diary_data.json"
QUESTIONS_FILE = "questions.json"

class DiaryManager:
    def __init__(self):
        self.ensure_files_exist()

    def ensure_files_exist(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)
        
        # We assume questions.json exists as we created it, 
        # but for robustness one could check or create default.

    def load_questions(self):
        if os.path.exists(QUESTIONS_FILE):
            with open(QUESTIONS_FILE, "r") as f:
                return json.load(f)
        return []

    def load_entry(self, date_str):
        """
        Loads the entry for a specific date (YYYY-MM-DD).
        Returns a dict of {question: answer}.
        """
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    return data.get(date_str, {})
            except json.JSONDecodeError:
                return {}
        return {}

    def save_entry(self, date_str, answers):
        """
        Saves answers for a specific date.
        answers: dict of {question: answer}
        """
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        
        data[date_str] = answers
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_date_offset(self, date_str, offset):
        """
        Returns a date string with the given offset (days) from the input date_str.
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        new_dt = dt + timedelta(days=offset)
        return new_dt.strftime("%Y-%m-%d")

    def get_today_date(self):
        return datetime.now().strftime("%Y-%m-%d")
