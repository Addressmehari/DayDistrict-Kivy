from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty
from kivy.app import App
from kivy.uix.modalview import ModalView
from kivy.uix.label import Label
from kivy.uix.button import Button
from diary_manager import DiaryManager
from widgets import DiaryEntryItemCard, QuestionEditItem, BottomNavBar, NavButton
from datetime import datetime

# Initialize Data Manager
dm = DiaryManager()

class WindowManager(ScreenManager):
    pass

# ... imports

# ...

class PlaceholderDisplay(Screen):
    text = StringProperty("")

class HomeScreen(Screen):
    def navigate_to(self, screen_name):
        manager = self.ids.content_manager
        # Disable transition for tab switching (instant)
        manager.transition = NoTransition()
        manager.current = screen_name

    def on_enter(self, *args):
        pass # No more animation needed for now


class DayPage(Screen):
    def __init__(self, date_str, **kwargs):
        super().__init__(**kwargs)
        self.name = date_str
        self.date_str = date_str
        self.questions = []
        Clock.schedule_once(self.populate_grid)

    def populate_grid(self, dt):
        self.questions = dm.load_questions_for_date(self.date_str)
        saved_data = dm.load_entry(self.date_str)
        
        grid = self.ids.grid_layout
        if grid:
            grid.cols = 3 if len(self.questions) >= 9 else 2
            grid.clear_widgets()
            for q in self.questions:
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
        # We need to save the FULL schema here to lock it in history
        # (in case we started with defaults but never saved)
        current_screen = self.ids.day_manager.current_screen
        if not current_screen: return
        
        # Determine the full schema currently in use
        active_questions = current_screen.questions
        
        # Load existing partial data
        current_data = dm.load_entry(self.current_date_str)
        
        # Merge: Start with schema (empty answers) -> Update from file -> Update from edit
        full_data = {q: "" for q in active_questions} # Initialize all keys
        for k, v in current_data.items():
            if k in full_data: 
                full_data[k] = v
        
        full_data[question] = new_answer
        dm.save_entry(self.current_date_str, full_data)
        current_screen.populate_grid(0)

def get_diary():
    app = App.get_running_app()
    return app.root.get_screen('home').ids.content_manager.get_screen('diary')

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
        diary_screen = get_diary()
        diary_screen.update_entry_data(self.question, new_ans)
        App.get_running_app().root.transition.direction = 'down'
        # Since DetailScreen covers everything, we just go back to 'home'
        # The home screen is already on 'diary' tab.
        App.get_running_app().root.current = 'home'

class QuestionEditorScreen(Screen):
    questions = ListProperty([])

    def on_enter(self):
        diary_screen = get_diary()
        current_date = diary_screen.current_date_str
        
        # Load questions for that specific date logic
        self.date_target = current_date
        self.questions = dm.load_questions_for_date(current_date)
        self.populate_list()

    def populate_list(self):
        self.ids.q_list.clear_widgets()
        for q in self.questions:
            item = QuestionEditItem(text=q)
            item.remove = lambda x=q: self.remove_question(x)
            self.ids.q_list.add_widget(item)


    def add_question(self):
        # Open simple popup to get text
        # For simplicity, we can use a TextInput in the main layout header
        new_q = self.ids.new_q_input.text.strip()
        if new_q and new_q not in self.questions:
            self.questions.append(new_q)
            self.populate_list()
            self.ids.new_q_input.text = ""

    def remove_question(self, q_text):
        if q_text in self.questions:
            self.questions.remove(q_text)
            self.populate_list()

    def prompt_save(self):
        # Show Modal
        view = ModalView(size_hint=(0.9, 0.4), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        layout.add_widget(Label(text="Apply Changes to?", font_size='18sp', bold=True))
        
        btn_today = Button(text="Apply for Today Only\n(Resets today's answers)", halign='center', background_normal='', background_color=(0.2, 0.6, 0.8, 1))
        btn_today.bind(on_release=lambda x: self.save_today(view))
        
        btn_future = Button(text="Apply from Today Onward\n(Updates defaults)", halign='center', background_normal='', background_color=(0.2, 0.8, 0.2, 1))
        btn_future.bind(on_release=lambda x: self.save_future(view))
        
        layout.add_widget(btn_today)
        layout.add_widget(btn_future)
        
        view.add_widget(layout)
        view.open()

    def save_today(self, view):
        view.dismiss()
        dm.overwrite_entry_schema(self.date_target, self.questions)
        self.go_back()

    def save_future(self, view):
        view.dismiss()
        dm.save_questions_default(self.questions)
        
        # Smart Merge for Today:
        # We want the new schema to apply to today immediately.
        # But we must preserve answers for questions that still exist.
        current_data = dm.load_entry(self.date_target)
        new_entry_data = {}
        for q in self.questions:
            # Preserve existing answer if available, else empty
            new_entry_data[q] = current_data.get(q, "")
            
        # We overwrite today's entry with the new schema + preserved answers
        dm.save_entry(self.date_target, new_entry_data)
        
        self.go_back()

    def go_back(self):
        app = App.get_running_app()
        diary_screen = get_diary()
        
        # Force refresh of the current day view
        diary_screen.load_day_into_view(self.date_target, animate=False)
        
        app.root.transition.direction = 'down'
        # Return to 'home' main screen (which contains the diary)
        app.root.current = 'home'
