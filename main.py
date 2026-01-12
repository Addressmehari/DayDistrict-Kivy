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
        try:
            # Start Notification Service
            self.notification_service = NotificationService()
            # Check every minute (60 seconds)
            Clock.schedule_interval(self.notification_service.check_and_notify, 60)
            # Check immediately once
            self.notification_service.check_and_notify()
        except Exception as e:
            print(f"Failed to start notification service: {e}")

if __name__ == "__main__":
    try:
        MainApp().run()
    except Exception:
        import traceback
        import textwrap
        error_trace = traceback.format_exc()
        
        # Fallback to simple UI to show error
        from kivy.base import runTouchApp
        from kivy.uix.label import Label
        from kivy.uix.scrollview import ScrollView
        
        print("CRASH CAUGHT:", error_trace)
        
        # Try to wrap text for mobile screen
        wrapped_error = "\n".join(textwrap.wrap(error_trace, width=40))
        
        # Create a scrollable label
        layout = ScrollView()
        label = Label(text=wrapped_error, 
                      size_hint_y=None, 
                      color=(1, 0.2, 0.2, 1),
                      halign='left', valign='top')
        label.bind(texture_size=label.setter('size'))
        # Ensure label width matches parent to wrap text properly
        label.text_size = (Window.width - 20, None)
        
        layout.add_widget(label)
        
        runTouchApp(layout)
