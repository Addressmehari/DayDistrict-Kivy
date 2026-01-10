import json
import os
import subprocess
from datetime import datetime, timedelta

DATA_FILE = "diary_data.json"
QUESTIONS_FILE = "questions.json"
TAGS_FILE = "tags.json"
RESERVED_KEYS = ["tags"]

class DiaryManager:
    def __init__(self):
        self.ensure_files_exist()

    def ensure_files_exist(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)
        
        if not os.path.exists(TAGS_FILE):
            with open(TAGS_FILE, "w") as f:
                json.dump([], f)
        
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
        
        # Check if entry is effectively empty (ignoring reserved keys if present in answers)
        # However, save_entry is usually called with just questions.
        # We must preserve existing tags if they exist in the file but not in 'answers'.
        
        # 1. Get existing tags
        existing_entry = data.get(date_str, {})
        existing_tags = existing_entry.get("tags", [])
        
        # 2. Add tags to answers to form the full object to save
        # We make a copy to avoid mutating the passed 'answers' object if the caller reuses it
        full_entry = answers.copy()
        if existing_tags:
            full_entry["tags"] = existing_tags
            
        # 3. Check emptiness (ignoring tags and reserved keys for the "ghost entry" logic)
        # If we have tags, it's NOT empty.
        has_content = False
        
        if existing_tags:
             has_content = True
        else:
            # Check text answers
            for k, v in answers.items():
                if k not in RESERVED_KEYS and str(v).strip():
                    has_content = True
                    break
        
        if not has_content:
            # Check if schema matches defaults (only if we have no content)
            defaults = self.load_questions()
            # Keys in answers (excluding reserved) vs defaults
            answer_keys = {k for k in answers.keys() if k not in RESERVED_KEYS}
            default_keys = set(defaults)
            
            if answer_keys == default_keys:
                # Ghost entry. Delete if exists.
                if date_str in data:
                    del data[date_str]
                    with open(DATA_FILE, "w") as f:
                        json.dump(data, f, indent=4)
                    self.update_city_visualizer()
                return

        # Normal save
        data[date_str] = full_entry
        
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
        # Preserve tags
        if "tags" in current_data:
            new_data["tags"] = current_data["tags"]
            
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
        - If data exists for that date, return its keys (legacy/historic mode), excluding reserved keys.
        - If no data, return current global defaults.
        """
        entry = self.load_entry(date_str)
        if entry and len(entry) > 0:
            # Filter out reserved keys
            keys = [k for k in entry.keys() if k not in RESERVED_KEYS]
            if keys:
                return keys
        return self.load_questions()

    def get_tags(self, date_str):
        entry = self.load_entry(date_str)
        return entry.get("tags", [])

    def save_tags(self, date_str, tags_list):
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except:
                data = {}
        
        if date_str not in data:
            data[date_str] = {}
        
        data[date_str]["tags"] = tags_list
        
        # Verify emptiness for cleanup
        entry = data[date_str]
        all_empty = True
        
        if entry.get("tags"): # If tags list is not empty
            all_empty = False
        else:
             # Check other keys
             for k, v in entry.items():
                 if k != "tags" and str(v).strip():
                     all_empty = False
                     break
        
        if all_empty:
             # Check default schema... (ghost check)
             defaults = self.load_questions()
             keys = [k for k in entry.keys() if k != "tags"]
             if set(keys) == set(defaults):
                 if date_str in data:
                    del data[date_str]
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_global_tags(self):
        if os.path.exists(TAGS_FILE):
            try:
                with open(TAGS_FILE, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_global_tags(self, tags_list):
        with open(TAGS_FILE, "w") as f:
            json.dump(tags_list, f, indent=4)

    def add_global_tag(self, tag_text):
        tags = self.load_global_tags()
        if tag_text not in tags:
            tags.append(tag_text)
            self.save_global_tags(tags)

    def remove_global_tag(self, tag_text):
        tags = self.load_global_tags()
        if tag_text in tags:
            tags.remove(tag_text)
            self.save_global_tags(tags)

    def search_entries(self, query):
        """
        Search for query string in all answers.
        Returns a list of dicts: [{'date': '2025-01-01', 'question': '...', 'answer': '...'}, ...]
        """
        query = query.lower().strip()
        if not query:
            return []
            
        all_data = self.get_all_entries()
        results = []
        
        for date_str, entries in all_data.items():
            # Check matches in answers
            for q, ans in entries.items():
                if q == "tags": continue # Skip checking tags for now, or maybe include them?
                
                if isinstance(ans, str) and query in ans.lower():
                    results.append({
                        'date': date_str,
                        'question': q,
                        'answer': ans
                    })
        
        # Sort by date descending
        results.sort(key=lambda x: x['date'], reverse=True)
        return results
