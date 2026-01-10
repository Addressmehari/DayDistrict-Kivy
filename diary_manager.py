import json
import os
import subprocess
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
        
        Cleanup Logic: 
        If an entry has NO content (all empty values) AND its questions (keys) 
        match the current global defaults, we do NOT save it (we delete it).
        This prevents 'ghost' entries from cluttering the file.
        """
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        
        # Check if entry is effectively empty
        all_empty = all(not v.strip() for v in answers.values())
        
        if all_empty:
            # Check if schema matches defaults
            defaults = self.load_questions()
            # We use set comparison for schema matching
            if set(answers.keys()) == set(defaults):
                # It's an empty default entry. Remove it if it exists.
                if date_str in data:
                    del data[date_str]
                
                # Write back changes (removal) and return
                with open(DATA_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                
                self.update_city_visualizer()
                return

        # Normal save
        data[date_str] = answers
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        self.update_city_visualizer()

    def update_city_visualizer(self):
        try:
            # Run the generator script in the background
            # We use absolute path to ensure it finds the script
            # Assumes GitVille folder is in the same directory as this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(base_dir, "GitVille", "generate_diary_city.py")
            
            if os.path.exists(script_path):
                # We need to run python. 'python' command assumed to be in path.
                # set cwd to GitVille so it writes files there
                subprocess.Popen(["python", script_path], cwd=os.path.dirname(script_path), 
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e:
            print(f"Failed to update city visualizer: {e}")

    def get_date_offset(self, date_str, offset):
        """
        Returns a date string with the given offset (days) from the input date_str.
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        new_dt = dt + timedelta(days=offset)
        return new_dt.strftime("%Y-%m-%d")

    def get_today_date(self):
        return datetime.now().strftime("%Y-%m-%d")

    def save_questions_default(self, questions_list):
        """
        Updates the global default questions (questions.json).
        """
        with open(QUESTIONS_FILE, "w") as f:
            json.dump(questions_list, f, indent=4)

    def overwrite_entry_schema(self, date_str, questions_list):
        """
        Overwrites the questions for a specific day while trying to preserve answers.
        """
        current_data = self.load_entry(date_str)
        new_data = {}
        for q in questions_list:
            new_data[q] = current_data.get(q, "")
        self.save_entry(date_str, new_data)

    def get_all_entries(self):
        """
        Returns the entire dictionary of entries {date_str: {question: answer}}.
        """
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}


    def load_questions_for_date(self, date_str):
        """
        Determines the questions to display for a given date.
        - If data exists for that date, return its keys (legacy/historic mode).
        - If no data, return current global defaults.
        """
        entry = self.load_entry(date_str)
        if entry and len(entry) > 0:
            return list(entry.keys())
        return self.load_questions()
