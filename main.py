from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
import screens
import widgets
from kivy.clock import Clock
from notification_service import NotificationService

from kivy.utils import platform

# GitHub Dark Theme Background
# 0d1117 -> (13/255, 17/255, 23/255, 1) = (0.05, 0.066, 0.09, 1)
Window.clearcolor = (0.05, 0.066, 0.09, 1)

# Set window size only for desktop testing
if platform not in ['android', 'ios']:
    Window.size = (360, 640)

class MainApp(App):
    def build(self):
        try:
            # Load the external KV file
            return Builder.load_file("diary.kv")
        except Exception:
            import traceback
            import textwrap
            error_trace = traceback.format_exc()
            
            # Fallback to simple UI to show error
            from kivy.base import runTouchApp
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            
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
            return layout

    def on_start(self):
        # Bind back button for Android
        Window.bind(on_keyboard=self.hook_keyboard)
        try:
            # Start Notification Service
            self.notification_service = NotificationService()
            # Check every minute (60 seconds)
            Clock.schedule_interval(self.notification_service.check_and_notify, 60)
            # Check immediately once
            self.notification_service.check_and_notify()
        except Exception as e:
            print(f"Failed to start notification service: {e}")

    def hook_keyboard(self, window, key, *args):
        # Key 27 is Escape/Back on Android
        if key == 27:
            screen_manager = self.root
            current_screen = screen_manager.current
            
            # 1. Level 2 Screens (Detail, Calendar, Editors) -> Go back to Home
            if current_screen in ['detail', 'calendar', 'question_editor', 'tag_manager']:
                screen_manager.transition.direction = 'down'
                screen_manager.current = 'home'
                return True # Consume event
            
            # 2. Level 1 (Home Screen Tabs)
            if current_screen == 'home':
                # Access internal ScreenManager
                home_screen = screen_manager.get_screen('home')
                internal_manager = home_screen.ids.content_manager
                current_tab = internal_manager.current
                
                # If on internal tabs (Diary, Map, Profile...), go back to Dashboard
                if current_tab != 'home_tab':
                    # Manually update Nav bar state if needed, or just switch
                    # Note: We should ideally update the toggle buttons' state too, 
                    # but switching screens is the primary action.
                    # We can find the nav button and trigger it, or just switch content.
                    
                    # Switch to Dashboard
                    home_screen.navigate_to('home_tab')
                    
                    # Update Nav Bar Visuals (Hack: Find the home button and trigger down)
                    # For simplicty, just switching view is enough for UX.
                    return True
                
                # If already on Dashboard, let default happen (Exit/Minimize)
                return False 
                
        return False

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
