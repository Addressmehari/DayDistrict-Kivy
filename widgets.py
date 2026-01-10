from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ColorProperty
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.behaviors import ToggleButtonBehavior
# Note: DetailScreen logic is invoked via App.get_running_app() which is resolved at runtime.

class SwipeBox(BoxLayout):
    def on_touch_down(self, touch):
        self._touch_start_x = touch.x
        self._touch_start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if super().on_touch_up(touch):
            return True
        try:
            dx = touch.x - self._touch_start_x
            dy = touch.y - self._touch_start_y
        except AttributeError:
             # Case where touch down didn't happen on this widget or was consumed? 
             # Though typically on_touch_down sets it. 
             # Safeguard just in case.
             return False

        if abs(dx) > 80 and abs(dy) < 60:
            app = App.get_running_app()
            if app and app.root:
                # DiaryScreen is now nested: Home -> Content_Manager -> Diary
                home = app.root.get_screen('home')
                # Check if we are actually ON the diary tab before swiping
                if home.ids.content_manager.current == 'diary':
                    screen = home.ids.content_manager.get_screen('diary')
                    if dx > 0: 
                        # Swipe Right -> Previous Day (Left)
                        screen.change_day(-1, direction='right')
                    else:
                        # Swipe Left -> Next Day (Right)
                        screen.change_day(1, direction='left')
                    return True
        return False

class WriteNowPrompter(ButtonBehavior, BoxLayout):
    pass

class DiaryEntryItemCard(ButtonBehavior, BoxLayout):
    question = StringProperty("")
    answer = StringProperty("")
    
    def on_release(self):
        app = App.get_running_app()
        if app and app.root:
            detail_screen = app.root.get_screen('detail')
            detail_screen.setup_entry(self.question, self.answer)
            app.root.transition.direction = 'up'
            app.root.current = 'detail'

class QuestionEditItem(BoxLayout):
    text = StringProperty("")
    # Signal removal to parent or controller
    def remove(self):
        pass

class NavButton(ToggleButtonBehavior, BoxLayout):
    icon_type = StringProperty("home")
    icon_size = NumericProperty(28) # Base size

    def on_icon_type(self, instance, value):
        # Set distinct base size for center button
        if value == 'center':
            self.icon_size = 32
        else:
            self.icon_size = 28

    def on_state(self, instance, value):
        if value == 'down':
            # Active: Pop effect (scale up)
            target = 34 if self.icon_type == 'center' else 32
            # Small overshoot for "bounce" feel
            anim = Animation(icon_size=target, duration=0.2, t='out_back')
            anim.start(self)
        else:
            # Inactive: Return to normal
            target = 32 if self.icon_type == 'center' else 28
            anim = Animation(icon_size=target, duration=0.15)
            anim.start(self)
    
    def on_release(self):
        # Logic handled by KV binding to navigate_to
        pass

class BottomNavBar(BoxLayout):
    pass

# --- Dashboard Widgets ---

class StatCard(BoxLayout):
    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("")
    # Accent color for the icon/stats
    accent_color = ColorProperty((0.345, 0.651, 1.0, 1)) 
    stroke_color = ColorProperty((0, 0, 0, 0))
    glow_color = ColorProperty((0, 0, 0, 0))

    def on_accent_color(self, instance, value):
        # Calculate derived colors
        # Stroke: darker version (50%) + 0.3 alpha
        self.stroke_color = (value[0]*0.5, value[1]*0.5, value[2]*0.5, 0.3)
        # Glow: normal color + 0.1 alpha
        self.glow_color = (value[0], value[1], value[2], 0.1)

    def on_value(self, instance, new_value):
        # animate check: if numeric, animate
        # We strip non-numeric chars for animation logic if needed, 
        # but for simplicity, we'll try to animate if it's a pure number.
        try:
            target = int(new_value)
            self._animate_value(target)
        except ValueError:
            pass # Not a number (e.g. "Mon"), just set it normally (KV binding does this)

    def _animate_value(self, target):
        self.current_anim_val = 0
        anim = Animation(current_anim_val=target, duration=1.5, t='out_expo')
        anim.start(self)

    current_anim_val = NumericProperty(0)
    
    def on_current_anim_val(self, instance, val):
        # Update the display text only while animating if the final target was numeric
        # This might conflict with the string bound 'value'.
        # Solution: Use a separate display property or just formatting logic.
        # Simpler approach: We update a separate property 'display_text'
        self.ids.val_label.text = str(int(val)) 

class RecentEntryItem(ButtonBehavior, BoxLayout):
    date_text = StringProperty("")
    preview_text = StringProperty("")
    date_ref = StringProperty("") # YYYY-MM-DD
    
    def on_release(self):
        app = App.get_running_app()
        # Navigate to diary and load this date
        if app and app.root:
             # We need to access get_diary helper or manually traverse
             home = app.root.get_screen('home')
             diary = home.ids.content_manager.get_screen('diary')
             
             # Switch to diary tab
             home.navigate_to('diary')
             # Force load date
             diary.load_day_into_view(self.date_ref, animate=False)


class HeatmapCell(ButtonBehavior, BoxLayout):
    color_val = ColorProperty((0.15, 0.17, 0.20, 1)) # Default empty cell
    date_ref = StringProperty("")
    
    def on_release(self):
        # Open Calendar View for the specific year
        if not self.date_ref: return
        
        from datetime import datetime
        try:
            dt = datetime.strptime(self.date_ref, "%Y-%m-%d")
            year = dt.year
            
            app = App.get_running_app()
            if app and app.root:
                cal_screen = app.root.get_screen('calendar')
                cal_screen.setup_view(year)
                app.root.transition.direction = 'up'
                app.root.current = 'calendar'
        except ValueError:
            pass

class CalendarDayCell(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    color_bg = ColorProperty((0.15, 0.17, 0.20, 1))
    text_color = ColorProperty((0.5, 0.5, 0.5, 1))
    date_ref = StringProperty("")
    
    def on_release(self):
        if not self.date_ref: return
        
        app = App.get_running_app()
        if app and app.root:
            # 1. Get Home Screen
            home = app.root.get_screen('home')
            
            # 2. Switch Home internal tab to Diary
            home.navigate_to('diary')
            
            # 3. Load specific date in Diary
            diary = home.ids.content_manager.get_screen('diary')
            diary.load_day_into_view(self.date_ref, animate=False)
            
            # 4. Navigate WindowManager back to Home
            app.root.transition.direction = 'down'
            app.root.current = 'home'

class TagChip(BoxLayout):
    text = StringProperty("")
    
    def remove(self):
        # Override in implementor or bind on creation
        pass

class ChecklistItem(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    is_checked = False
    
    def on_release(self):
        # Toggle check
        self.is_checked = not self.is_checked
        self.update_icon()
        self.on_toggle(self.text, self.is_checked)
        
    def update_icon(self):
        self.ids.icon.text = u"\ue834" if self.is_checked else u"\ue835"
        self.ids.icon.color = (0.2, 0.6, 0.8, 1) if self.is_checked else (0.5, 0.5, 0.5, 1)

    def on_toggle(self, text, val):
        pass
