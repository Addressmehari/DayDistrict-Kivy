from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.app import App
from diary_manager import DiaryManager
from widgets import DiaryEntryItemCard
from datetime import datetime

# Initialize Data Manager
dm = DiaryManager()

class WindowManager(ScreenManager):
    pass

class HomeScreen(Screen):
    def on_enter(self, *args):
        Clock.schedule_once(self._animate_entrance)
    
    def _animate_entrance(self, dt):
        if 'title_label' not in self.ids: return
        Animation(opacity=1, pos_hint={'center_x': 0.5}, duration=0.8, t='out_cubic').start(self.ids.title_label)
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.8).start(self.ids.subtitle_label), 0.2)
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.6, t='out_back').start(self.ids.start_btn), 0.5)

    def on_leave(self, *args):
        self.ids.title_label.opacity = 0
        self.ids.subtitle_label.opacity = 0
        self.ids.start_btn.opacity = 0

class DayPage(Screen):
    def __init__(self, date_str, **kwargs):
        super().__init__(**kwargs)
        self.name = date_str
        self.date_str = date_str
        Clock.schedule_once(self.populate_grid)

    def populate_grid(self, dt):
        questions = dm.load_questions()
        saved_data = dm.load_entry(self.date_str)
        grid = self.ids.grid_layout
        if grid:
            grid.cols = 3 if len(questions) >= 9 else 2
            grid.clear_widgets()
            for q in questions:
                ans = saved_data.get(q, "")
                item = DiaryEntryItemCard(question=q, answer=ans)
                grid.add_widget(item)

class DiaryScreen(Screen):
    current_date_str = StringProperty("")
    current_date_display_day = StringProperty("")
    current_date_display_date = StringProperty("")
    
    def init_view(self):
        if not self.current_date_str:
            self.current_date_str = dm.get_today_date()
            self.load_day_into_view(self.current_date_str, animate=False)

    def change_day(self, offset, direction='left'):
        new_date = dm.get_date_offset(self.current_date_str, offset)
        self.current_date_str = new_date
        self.load_day_into_view(new_date, animate=True, direction=direction)

    def load_day_into_view(self, date_str, animate=True, direction='left'):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.current_date_display_day = dt.strftime("%A").upper()
        if date_str == today:
             self.current_date_display_date = "Today"
        else:
            self.current_date_display_date = dt.strftime("%b %d")
        
        manager = self.ids.day_manager
        if manager.has_screen(date_str):
            manager.remove_widget(manager.get_screen(date_str))
        new_page = DayPage(date_str=date_str)
        manager.add_widget(new_page)
        
        manager.transition = SlideTransition(direction=direction) if animate else SlideTransition(duration=0)
        manager.current = date_str
        Clock.schedule_once(lambda dt: self.cleanup_screens(manager, date_str), 1)

    def cleanup_screens(self, manager, current_name):
        for screen in manager.screens[:]:
            if screen.name != current_name:
                manager.remove_widget(screen)

    def update_entry_data(self, question, new_answer):
        current_data = dm.load_entry(self.current_date_str)
        current_data[question] = new_answer
        dm.save_entry(self.current_date_str, current_data)
        if self.ids.day_manager.current_screen:
            self.ids.day_manager.current_screen.populate_grid(0)

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
