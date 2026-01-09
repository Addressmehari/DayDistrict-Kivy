from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from diary_manager import DiaryManager
from datetime import datetime

# Initialize Data Manager
dm = DiaryManager()

# Set a darker, "Midnight" theme for distraction-free writing
Window.clearcolor = (0.08, 0.08, 0.1, 1)
Window.size = (360, 740)

kv = """
#:set C_BG (0.08, 0.08, 0.1, 1)
#:set C_CARD (0.15, 0.15, 0.18, 1)
#:set C_ACCENT (0.3, 0.6, 0.8, 1)
#:set C_TEXT (0.9, 0.9, 0.9, 1)
#:set C_TEXT_DIM (0.6, 0.6, 0.6, 1)
#:set C_BUTTON (0.2, 0.25, 0.3, 1)
#:set C_BUTTON_PRESSED (0.3, 0.35, 0.4, 1)
#:import DampedScrollEffect kivy.effects.dampedscroll.DampedScrollEffect

<FlatButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    color: C_TEXT
    font_size: '18sp'
    canvas.before:
        Color:
            rgba: C_ACCENT if self.state == 'normal' else C_BUTTON_PRESSED
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]

<IconButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    color: C_ACCENT
    font_size: '22sp'
    canvas.before:
        Color:
            rgba: (1, 1, 1, 0.05) if self.state == 'down' else (0,0,0,0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

WindowManager:
    HomeScreen:
    DiaryScreen:
    DetailScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: 60
        spacing: 40
        canvas.before:
            Color:
                rgba: C_BG
            Rectangle:
                pos: self.pos
                size: self.size

        Widget: 
            size_hint_y: 0.3

        Label:
            text: "Journal"
            font_size: '64sp'
            font_name: 'Roboto'
            bold: True
            color: C_ACCENT
            size_hint_y: None
            height: self.texture_size[1]
            opacity: 0
            id: title_label

        Label:
            text: "Capture your day, every day."
            font_size: '18sp'
            color: C_TEXT_DIM
            size_hint_y: None
            height: self.texture_size[1]
            opacity: 0
            id: subtitle_label

        Widget: 
            size_hint_y: 0.1

        FlatButton:
            text: "Start Writing"
            size_hint: (None, None)
            size: (200, 60)
            pos_hint: {"center_x": 0.5}
            font_size: '20sp'
            bold: True
            opacity: 0
            id: start_btn
            on_release: 
                app.root.current = "diary"
                app.root.transition.direction = "left"

        Widget: 
            # Filler
            size_hint_y: 0.4

<DiaryScreen>:
    name: "diary"
    on_enter: root.init_view()

    SwipeBox:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: C_BG
            Rectangle:
                pos: self.pos
                size: self.size

        # Top Navigation Bar (Smaller Height)
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            padding: [10, 5]
            spacing: 10
            canvas.before:
                Color:
                    rgba: (0.1, 0.1, 0.12, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            IconButton:
                text: "<"
                size_hint_x: None
                width: '40dp'
                font_size: '20sp'
                on_release: 
                    app.root.current = "home"
                    app.root.transition.direction = "right"

            BoxLayout:
                orientation: "vertical"
                size_hint_x: 1
                
                Label:
                    text: root.current_date_display
                    font_size: '18sp'
                    bold: True
                    color: C_TEXT
                    halign: 'center'
                    valign: 'middle'
                
                Label:
                    text: "Swipe to navigate"
                    font_size: '10sp'
                    color: C_TEXT_DIM
                    halign: 'center'
                    valign: 'middle'

            Widget:
                size_hint_x: None
                width: '40dp'

        # Main Content Area (Nested ScreenManager for sliding days)
        ScreenManager:
            id: day_manager

<DayPage>:
    # This is a Screen representing a single day's grid
    BoxLayout:
        ScrollView:
            id: scroll_view
            do_scroll_x: False
            bar_width: 8
            bar_color: C_ACCENT
            bar_inactive_color: (0.2, 0.2, 0.2, 0)
            effect_cls: DampedScrollEffect
            scroll_type: ['bars', 'content']
            smooth_scroll_end: 10
            
            GridLayout:
                id: grid_layout
                cols: 2
                spacing: 1
                padding: [5, 5, 5, 40]
                size_hint_y: None
                height: self.minimum_height
                canvas.before:
                    Color:
                        rgba: (1, 1, 1, 0.1)  # Lite white lines
                    Rectangle:
                        pos: self.pos
                        size: self.size

<DiaryEntryItemCard>:
    orientation: "vertical"
    size_hint_y: None
    height: 200
    padding: 0
    spacing: 0
    opacity: 1
    
    canvas.before:
        Color:
            rgba: C_CARD
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [3]

    # Question Header
    BoxLayout:
        size_hint_y: None
        height: '40dp' # Smaller Header in Grid Item too potentially? Kept relative.
        padding: [15, 0]
        
        Label:
            text: root.question
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            color: C_ACCENT
            font_size: '13sp'
            bold: True

    Widget:
        size_hint_y: None
        height: 1
        canvas:
            Color:
                rgba: (1, 1, 1, 0.05)
            Rectangle:
                pos: self.pos
                size: self.size

    # Preview Text
    Label:
        text: root.answer if root.answer else "Tap to write..."
        text_size: (self.width - 30, self.height - 20)
        valign: 'top'
        halign: 'left'
        padding: [15, 10]
        color: C_TEXT if root.answer else (0.4, 0.4, 0.4, 1)
        font_size: '12sp'
        size_hint_y: 1

<DetailScreen>:
    name: "detail"
    
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: C_BG
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Detail Header (Smaller)
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            padding: [10, 5]
            spacing: 10
            canvas.before:
                Color:
                    rgba: (0.1, 0.1, 0.12, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            IconButton:
                text: "< Back"
                font_size: '16sp'
                size_hint_x: None
                width: '80dp'
                on_release: root.save_and_close()

            Label:
                text: "Edit Entry"
                font_size: '16sp'
                bold: True
                color: C_TEXT
                halign: 'center'
                valign: 'middle'

            Widget:
                size_hint_x: None
                width: '80dp'

        # Focus Content
        BoxLayout:
            orientation: "vertical"
            padding: 25
            spacing: 15

            Label:
                text: root.question
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
                halign: 'left'
                color: C_ACCENT
                font_size: '22sp'
                bold: True

            TextInput:
                id: detail_input
                text: root.answer
                hint_text: "Write your thoughts here..."
                hint_text_color: (0.4, 0.4, 0.4, 1)
                multiline: True
                background_color: 0, 0, 0, 0
                foreground_color: C_TEXT
                cursor_color: C_ACCENT
                selection_color: (0.3, 0.6, 0.8, 0.3)
                font_size: '18sp'
                size_hint_y: 1
                padding: [0, 10]
"""

class SwipeBox(BoxLayout):
    def on_touch_down(self, touch):
        self._touch_start_x = touch.x
        self._touch_start_y = touch.y
        # Propagate touch to children first (important for scrolling!)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        # Allow children to handle touch up (clicks, scroll stops)
        if super().on_touch_up(touch):
            return True
        
        # If not handled, check swipe on Screen
        dx = touch.x - self._touch_start_x
        dy = touch.y - self._touch_start_y
        
        # Horizontal swipe detection
        if abs(dx) > 80 and abs(dy) < 60:
            screen = App.get_running_app().root.get_screen('diary')
            if dx > 0: 
                # Swipe Right
                screen.change_day(1, direction='right')
            else:
                # Swipe Left
                screen.change_day(-1, direction='left')
            return True
        return False

class DiaryEntryItemCard(ButtonBehavior, BoxLayout):
    question = StringProperty("")
    answer = StringProperty("")
    
    def on_release(self):
        app = App.get_running_app()
        detail_screen = app.root.get_screen('detail')
        detail_screen.setup_entry(self.question, self.answer)
        app.root.transition.direction = 'up'
        app.root.current = 'detail'

class WindowManager(ScreenManager):
    pass

class HomeScreen(Screen):
    def on_enter(self, *args):
        Clock.schedule_once(self._animate_entrance)

    def _animate_entrance(self, dt):
        if 'title_label' not in self.ids:
            return
        anim = Animation(opacity=1, duration=0.8, t='out_quad')
        anim.start(self.ids.title_label)
        anim_sub = Animation(opacity=1, duration=0.8, t='out_quad')
        Clock.schedule_once(lambda dt: anim_sub.start(self.ids.subtitle_label), 0.3)
        anim_btn = Animation(opacity=1, duration=0.5, t='out_back')
        Clock.schedule_once(lambda dt: anim_btn.start(self.ids.start_btn), 0.6)

    def on_leave(self, *args):
        self.ids.title_label.opacity = 0
        self.ids.subtitle_label.opacity = 0
        self.ids.start_btn.opacity = 0

class DayPage(Screen):
    # Holds the grid for a specific date
    def __init__(self, date_str, **kwargs):
        super().__init__(**kwargs)
        self.name = date_str # Unique name for ScreenManager
        self.date_str = date_str
        Clock.schedule_once(self.populate_grid)

    def populate_grid(self, dt):
        questions = dm.load_questions()
        saved_data = dm.load_entry(self.date_str)
        
        grid = self.ids.grid_layout
        if len(questions) >= 9:
            grid.cols = 3
        else:
            grid.cols = 2
            
        grid.clear_widgets()
        
        # Add items
        # To optimize animation, we can cascade them here too, or just show them.
        # Since we are sliding the WHOLE page, cascading might be too much movement.
        # Let's just show them static, the SlideTransition is the star now.
        for q in questions:
            ans = saved_data.get(q, "")
            item = DiaryEntryItemCard(question=q, answer=ans)
            grid.add_widget(item)

class DiaryScreen(Screen):
    current_date_str = StringProperty("")
    current_date_display = StringProperty("")
    
    def init_view(self):
        # Initialize with today if empty
        if not self.current_date_str:
            self.current_date_str = dm.get_today_date()
            self.load_day_into_view(self.current_date_str, animate=False)

    def change_day(self, offset, direction='left'):
        # Calculate new date
        new_date = dm.get_date_offset(self.current_date_str, offset)
        self.current_date_str = new_date
        self.load_day_into_view(new_date, animate=True, direction=direction)

    def load_day_into_view(self, date_str, animate=True, direction='left'):
        # Update Header Label
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        if date_str == today:
             self.current_date_display = f"Today, {dt.strftime('%b %d')}"
        else:
            self.current_date_display = dt.strftime("%A, %b %d")
        
        # Manage Day Pages
        manager = self.ids.day_manager
        
        # Create new screen if not exists (or always recreate to ensure freshness)
        # Recreating is safer for data updates
        if manager.has_screen(date_str):
            manager.remove_widget(manager.get_screen(date_str))
            
        new_page = DayPage(date_str=date_str)
        manager.add_widget(new_page)
        
        if animate:
            manager.transition = SlideTransition(direction=direction)
        else:
             manager.transition = SlideTransition(duration=0) # Instant
             
        manager.current = date_str
        
        # Cleanup old screens to save memory (keep current + maybe 1 prev/next?)
        # Simple cleanup: remove all except current after transition
        # But we can't delete immediately. Schedule it.
        Clock.schedule_once(lambda dt: self.cleanup_screens(manager, date_str), 1)

    def cleanup_screens(self, manager, current_name):
        for screen in manager.screens[:]:
            if screen.name != current_name:
                manager.remove_widget(screen)

    def update_entry_data(self, question, new_answer):
        # Save data
        current_data = dm.load_entry(self.current_date_str)
        current_data[question] = new_answer
        dm.save_entry(self.current_date_str, current_data)
        
        # Refresh current page
        manager = self.ids.day_manager
        if manager.current_screen:
            # Re-populate
            manager.current_screen.populate_grid(0)

class DetailScreen(Screen):
    question = StringProperty("")
    answer = StringProperty("")

    def setup_entry(self, question, current_answer):
        self.question = question
        self.answer = current_answer
        self.ids.detail_input.text = current_answer
        Clock.schedule_once(self.focus_input, 0.5)

    def focus_input(self, dt):
        self.ids.detail_input.focus = True

    def save_and_close(self):
        new_ans = self.ids.detail_input.text
        diary_screen = App.get_running_app().root.get_screen('diary')
        diary_screen.update_entry_data(self.question, new_ans)
        
        App.get_running_app().root.transition.direction = 'down'
        App.get_running_app().root.current = 'diary'

class MainApp(App):
    def build(self):
        return Builder.load_string(kv)

if __name__ == "__main__":
    MainApp().run()
