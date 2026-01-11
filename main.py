from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
import screens
import widgets
from kivy.clock import Clock
from notification_service import NotificationService

# GitHub Dark Theme Background
# 0d1117 -> (13/255, 17/255, 23/255, 1) = (0.05, 0.066, 0.09, 1)
Window.clearcolor = (0.05, 0.066, 0.09, 1)
Window.size = (360, 640)

class MainApp(App):
    def build(self):
        # Load the external KV file
        return Builder.load_file("diary.kv")

    def on_start(self):
        # Start Notification Service
        self.notification_service = NotificationService()
        # Check every minute (60 seconds)
        Clock.schedule_interval(self.notification_service.check_and_notify, 60)
        # Check immediately once
        self.notification_service.check_and_notify()

if __name__ == "__main__":
    MainApp().run()
