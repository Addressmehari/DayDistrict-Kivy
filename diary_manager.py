import json
import os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.utils import platform

# Import logic for generator
import sys
# Ensure GitVille is in path to import
app_dir = os.path.dirname(os.path.abspath(__file__))
gitville_dir = os.path.join(app_dir, "GitVille")
if gitville_dir not in sys.path:
    sys.path.append(gitville_dir)

try:
    from GitVille import generate_diary_city
except ImportError:
    generate_diary_city = None

class DiaryManager:
    def __init__(self):
        self.data_dir = self.get_data_dir()
        
        self.DATA_FILE = os.path.join(self.data_dir, "diary_data.json")
        self.QUESTIONS_FILE = os.path.join(self.data_dir, "questions.json")
        self.TAGS_FILE = os.path.join(self.data_dir, "tags.json")
        self.CONFIG_FILE = os.path.join(self.data_dir, "user_config.json")
        
        self.ensure_files_exist()
        self.ensure_config_exists()

    def get_data_dir(self):
        if platform == 'android':
            app = App.get_running_app()
            if app:
                return app.user_data_dir
            # Fallback for service context if app is None (unlikely for main app)
            return "/data/data/org.test.diaryapp/files"
        return os.path.dirname(os.path.abspath(__file__))

    def ensure_config_exists(self):
        if not os.path.exists(self.CONFIG_FILE):
             default_config = {
                "username": "User",
                "joined_date": datetime.now().strftime("%Y-%m-%d"),
                "daily_reminder": False,
                "reminder_time": "20:00",
                "theme_mode": "dark",
                "profile_pic": "",
                "favorite_photo": "",
                "favorite_music": "",
                "bio": ""
             }
             with open(self.CONFIG_FILE, "w") as f:
                 json.dump(default_config, f, indent=4)


    def ensure_files_exist(self):
        if not os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, "w") as f:
                json.dump({}, f)
        
        if not os.path.exists(self.TAGS_FILE):
            with open(self.TAGS_FILE, "w") as f:
                json.dump([], f)
        
        if not os.path.exists(self.QUESTIONS_FILE):
            # Create default questions if missing
            default_questions = [
                "What was the highlight of your day?",
                "What challenged you today?",
                "What are you grateful for?"
            ]
            with open(self.QUESTIONS_FILE, "w") as f:
                json.dump(default_questions, f, indent=4)

    def load_questions(self):
        if os.path.exists(self.QUESTIONS_FILE):
            with open(self.QUESTIONS_FILE, "r") as f:
                return json.load(f)
        return []

    def load_entry(self, date_str):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    data = json.load(f)
                    return data.get(date_str, {})
            except json.JSONDecodeError:
                return {}
        return {}

    def save_entry(self, date_str, answers):
        data = {}
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        
        existing_entry = data.get(date_str, {})
        existing_tags = existing_entry.get("tags", [])
        
        full_entry = answers.copy()
        if existing_tags:
            full_entry["tags"] = existing_tags
            
        has_content = False
        if existing_tags:
             has_content = True
        else:
            for k, v in answers.items():
                if k != "tags" and str(v).strip():
                    has_content = True
                    break
        
        if not has_content:
            defaults = self.load_questions()
            answer_keys = {k for k in answers.keys() if k != "tags"}
            default_keys = set(defaults)
            
            if answer_keys == default_keys:
                if date_str in data:
                    del data[date_str]
                    with open(self.DATA_FILE, "w") as f:
                        json.dump(data, f, indent=4)
                    self.update_city_visualizer()
                return

        data[date_str] = full_entry
        
        with open(self.DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        self.update_city_visualizer()

    def update_city_visualizer(self):
        try:
            if generate_diary_city:
                # We need to decide where the visualizer output goes.
                # It should go to a folder inside user_data_dir that the web server serves.
                # Let's call it "GitVille_www"
                www_dir = os.path.join(self.data_dir, "GitVille_www")
                
                # We generate the data files there.
                generate_diary_city.generate(self.DATA_FILE, www_dir)
            else:
                print("Generator module not found")
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

    def get_user_profile(self):
        CONFIG_FILE = "user_config.json"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_user_profile(self, profile_data):
        CONFIG_FILE = "user_config.json"
        current_data = self.get_user_profile()
        current_data.update(profile_data)
        with open(CONFIG_FILE, "w") as f:
            json.dump(current_data, f, indent=4)

