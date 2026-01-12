from plyer import notification
from datetime import datetime
from diary_manager import DiaryManager
from kivy.utils import platform

class NotificationService:
    def __init__(self):
        try:
            self.dm = DiaryManager()
            self.last_notified_morning = ""
            self.last_notified_night = ""
        except Exception as e:
            print(f"NotificationService Update Error: {e}")

    def check_and_notify(self, dt=None):
        try:
            # Current time
            now = datetime.now()
            current_hour = now.hour
            today_str = now.strftime("%Y-%m-%d")

            # Check if entry exists for today
            entry = self.dm.load_entry(today_str)
            
            # Determine if entry is "written" (has meaningful content)
            # Entry is a dict. If empty or all values are empty string -> not written.
            # We ignore 'tags' if present alone.
            has_content = False
            for key, value in entry.items():
                if key != "tags" and str(value).strip():
                    has_content = True
                    break
            
            if has_content:
                return # Already written!

            # Morning Reminder (9 AM)
            if current_hour == 9:
                # Check if we already notified today for morning
                if self.last_notified_morning != today_str:
                    self.send_morning_notification()
                    self.last_notified_morning = today_str

            # Night Reminder (9 PM or 10 PM)
            elif current_hour in [21, 22]: # 9 PM or 10 PM
                # Check if we already notified today for night
                if self.last_notified_night != today_str:
                    self.send_night_notification()
                    self.last_notified_night = today_str
        except Exception as e:
             print(f"Notification service error: {e}")

    def send_morning_notification(self):
        self.send_notification(
            title="Good Morning! 🌞",
            message="The canvas of today awaits directly. Capture your morning thoughts!"
        )

    def send_night_notification(self):
        self.send_notification(
            title="Sweet Dreams! 🌙",
            message="Before the day fades, preserve your memories in your diary."
        )

    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Diary App",
                app_icon="assets/icon.png" if platform == 'android' else None,
                timeout=10
            )
            print(f"Notification Sent: {title}")
        except Exception as e:
            print(f"Failed to send notification: {e}")
