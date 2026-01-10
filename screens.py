from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.app import App
from kivy.uix.modalview import ModalView
from kivy.uix.label import Label
from kivy.uix.button import Button
from diary_manager import DiaryManager
from widgets import DiaryEntryItemCard, QuestionEditItem, BottomNavBar, NavButton, StatCard, RecentEntryItem, HeatmapCell
from datetime import datetime, timedelta
from map_screen import CityMapScreen

# Initialize Data Manager
dm = DiaryManager()

class WindowManager(ScreenManager):
    pass

# ... imports

# ...

class HomeDashboard(Screen):
    date_display = StringProperty("")
    heatmap_year = NumericProperty(datetime.now().year)
    
    def on_enter(self, *args):
        self.date_display = datetime.now().strftime("%A, %d %B")
        # Ensure year is set
        if self.heatmap_year == 0:
            self.heatmap_year = datetime.now().year
        # Schedule update to ensure KV ids are populated
        Clock.schedule_once(lambda dt: self.update_view(), 0)

    def update_view(self):
        # 0. Greeting
        self.update_greeting()

        # 1. Fetch Data
        all_data = dm.get_all_entries()
        
        # 2. Update Stats
        self.calculate_stats(all_data)
        
        # 3. Heatmap
        self.populate_heatmap(all_data)
        
        # 4. Recent Entries
        self.populate_recent_entries(all_data)

        # 5. Write Now Prompter Logic
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_data = all_data.get(today_str, {})
        self.update_prompter(today_data)

    def update_prompter(self, today_data):
        if 'write_now_card' not in self.ids: return
        card = self.ids.write_now_card
        
        # Check if entry is effectively empty
        # If today_data is empty dict OR all values are empty strings
        is_empty = True
        if today_data:
             if any(v.strip() for v in today_data.values()):
                 is_empty = False
        
        if is_empty:
            # Show Prompter
            if card.height == 0:
                anim = Animation(height=80, opacity=1, duration=0.4, t='out_back')
                anim.start(card)
        else:
            # Hide Prompter
            if card.height > 0:
                anim = Animation(height=0, opacity=0, duration=0.3)
                anim.start(card)

    def go_to_today(self):
        app = App.get_running_app()
        if app and app.root:
             home = app.root.get_screen('home')
             home.navigate_to('diary')
             
             diary = home.ids.content_manager.get_screen('diary')
             today = datetime.now().strftime("%Y-%m-%d")
             diary.load_day_into_view(today, animate=False)

    def update_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good Morning,"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon,"
        elif 17 <= hour < 22:
            greeting = "Good Evening,"
        else:
            greeting = "Good Night,"
        
        if 'greeting_label' in self.ids:
            self.ids.greeting_label.text = greeting

    def populate_recent_entries(self, all_data):
        if 'recent_list' not in self.ids: return
        
        container = self.ids.recent_list
        container.clear_widgets()
        
        # Sort dates descending
        sorted_dates = sorted(all_data.keys(), reverse=True)
        
        # Take top 3
        top_3 = sorted_dates[:3]
        
        if not top_3:
            # Show a placeholder or just leave empty?
            # Let's show a "No entries yet" label if empty
            # But for now, just empty is fine or a specific widget
            pass

        for date_str in top_3:
            entry_data = all_data[date_str]
            # Find the first non-empty answer to preview
            preview = "No text..."
            for q, ans in entry_data.items():
                if ans.strip():
                    preview = ans.strip()
                    break
            
            # Format Date: "Jan 10"
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_fmt = dt.strftime("%b %d")
            
            item = RecentEntryItem()
            item.date_text = date_fmt
            item.preview_text = preview
            item.date_ref = date_str
            container.add_widget(item)

    def calculate_stats(self, all_data):
        # Sort dates
        sorted_dates = sorted(all_data.keys())
        total_entries = len(all_data)
        
        # Streak
        streak = 0
        if sorted_dates:
            today = datetime.now().date()
            # Check backwards from today or yesterday
            # Convert keys to date objs
            dates_set = {datetime.strptime(d, "%Y-%m-%d").date() for d in sorted_dates}
            
            check_date = today
            if check_date not in dates_set:
                # If no entry today, check if streak ended yesterday
                check_date = today - timedelta(days=1)
            
            while check_date in dates_set:
                streak += 1
                check_date -= timedelta(days=1)

        # Most Active Day
        # Count entries per weekday
        weekday_counts = {i: 0 for i in range(7)}
        for d_str in all_data:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            weekday_counts[dt.weekday()] += 1
        
        most_active_idx = max(weekday_counts, key=weekday_counts.get)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        most_active_day = days[most_active_idx] if total_entries > 0 else "N/A"

        # Update Stat Cards
        # We assume IDs are accessbile. We'll define them in KV.
        if 'stat_streak' in self.ids:
            self.ids.stat_streak.value = str(streak)
        if 'stat_total' in self.ids:
            self.ids.stat_total.value = str(total_entries)
        if 'stat_active' in self.ids:
            self.ids.stat_active.value = most_active_day
            # Hack to reset text because 'on_value' might not trigger if value is same string
            # but we want standard behavior for non-numeric.
            self.ids.stat_active.ids.val_label.text = most_active_day

        # New Stat: Total Words
        total_words = 0
        for date_key, questions_dict in all_data.items():
            for ans in questions_dict.values():
                total_words += len(ans.split())
        
        if 'stat_words' in self.ids:
            self.ids.stat_words.value = str(total_words)



    def populate_heatmap(self, all_data):
        heatmap = self.ids.heatmap_container
        heatmap.clear_widgets()
        
        # Structure:
        # We need a Main horizontal box.
        # Left: Day Labels (Mon, Wed, Fri)
        # Right: Content (Months + Grid)
        
        # 1. Main Container (already cleared 'heatmap_container')
        # We assume heatmap_container is a BoxLayout (horizontal).
        
        # --- Left Column: Day Labels ---
        # Align with grid (which starts 20px down due to header) -> Top padding 20
        day_labels = BoxLayout(orientation='vertical', size_hint_x=None, width=30, spacing=4, padding=[0, 20, 0, 0])
        
        days_map = {1: "Mon", 3: "Wed", 5: "Fri"}
        for i in range(7):
            txt = days_map.get(i, "")
            # Height must match cell height (12) to stay in sync with grid pitch (12+4=16)
            lbl = Label(text=txt, font_size='10sp', color=(0.5,0.5,0.5,1), size_hint_y=None, height=12) 
            day_labels.add_widget(lbl)
            
        heatmap.add_widget(day_labels)
        
        # --- Right Column: Months + Grid ---
        right_col = BoxLayout(orientation='vertical', size_hint_x=None, spacing=5)
        # This column width will grow as we add weeks.
        
        # Top: Month Labels
        # We need to pre-calculate where months start to place labels correctly.
        # However, a simpler way for standard scrolling is a horizontal layout for months 
        # matching the week columns.
        
        # Grid Container
        grid_box = BoxLayout(orientation='horizontal', spacing=4, size_hint_x=None)
        
        # Use Dynamic Year
        current_year = self.heatmap_year
        start_date = datetime(current_year, 1, 1).date()
        end_date = datetime(current_year, 12, 31).date()
        
        # Calculate how many weeks roughly needed.
        # But we build dynamically:
        # Week 1 might be partial (if Jan 1 is Thursday).
        # We need to fill the first column with empty cells until Thursday.
        
        # Weekday of Jan 1st: Mon=0 ... Sun=6
        # If visual row 0 is Mon, then index matches weekday().
        # If visual row 0 is Sun, then index = (weekday() + 1) % 7.
        # Let's stick to standard GitHub visual: Row 0 = Sunday.
        jan1_weekday_idx = (start_date.weekday() + 1) % 7
        
        current = start_date
        # We need to iterate weeks.
        
        # But iterating by weeks is tricky if we want exact year boundaries.
        # Easier: Iterate days and pack into columns.
        
        # Initialize first week column
        current_week_col = BoxLayout(orientation='vertical', spacing=4, size_hint_x=None, width=16)
        
        # Pad beginning of first week if Jan 1 is not Sunday
        for _ in range(jan1_weekday_idx):
            # Empty invisible widget
            empty = HeatmapCell() # Use cell for sizing
            empty.opacity = 0 # Invisible
            current_week_col.add_widget(empty)
            
        day_in_week_count = jan1_weekday_idx
        
        month_labels = [] # (Month Name, Column Index)
        last_month = None
        # Track X position for labels
        current_x_pos = 0 # PIXELS
        month_start_x = 0
        
        # Loop strictly through the year
        while current <= end_date:
            # Check Month Change
            m = current.strftime("%b")
            
            if m != last_month:
                if last_month is not None:
                    # Month Changed!
                    # 1. Finish previous month's column if partially filled
                    if day_in_week_count > 0:
                        # Fill rest with empty
                        for _ in range(7 - day_in_week_count):
                            empty = HeatmapCell()
                            empty.opacity = 0
                            current_week_col.add_widget(empty)
                        grid_box.add_widget(current_week_col)
                        current_x_pos += 20 # 16 width + 4 spacing
                        # Reset for new column
                        current_week_col = BoxLayout(orientation='vertical', spacing=4, size_hint_x=None, width=16)
                        day_in_week_count = 0
                    
                    # Store Label for Previous Month (centered)
                    width = current_x_pos - month_start_x
                    center_x = month_start_x + (width / 2)
                    month_labels.append((last_month, center_x))

                    # 2. Add Gap (Spacer)
                    grid_box.add_widget(BoxLayout(size_hint_x=None, width=8)) # Gap
                    current_x_pos += 12 # 8 width + 4 spacing
                    
                    month_start_x = current_x_pos # Start of new month
                
                last_month = m
                
                # If we just started a new month, we need to pad the column to the correct weekday again?
                # Leetcode style: Does next month start at top?
                # Or does it continue flow?
                # User said: "if the month ends on the friday or in between week just small gap and staw next"
                # This implies: Break the week, start new column for new month.
                # But we must respect the weekday alignment (rows are Mon-Sun).
                # If we break column, next column starts at row 0 (Sunday).
                # So we must pad empty cells until the weekday of 'current' date.
                
                # Pad for new month start
                weekday_idx = (current.weekday() + 1) % 7
                # If we are in a fresh column (day_in_week_count == 0), we pad.
                # If we just finished a column above, day_in_week_count is 0.
                for _ in range(weekday_idx):
                    empty = HeatmapCell()
                    empty.opacity = 0
                    current_week_col.add_widget(empty)
                day_in_week_count = weekday_idx

            # --- Cell Logic ---
            date_str = current.strftime("%Y-%m-%d")
            answers = all_data.get(date_str, {})
            char_count = sum(len(v) for v in answers.values())
            color = self.get_color_for_activity(char_count)
            
            cell = HeatmapCell()
            cell.color_val = color
            cell.date_ref = date_str
            
            current_week_col.add_widget(cell)
            day_in_week_count += 1
            
            # If week full (7 days), push column and start new
            if day_in_week_count == 7:
                grid_box.add_widget(current_week_col)
                current_x_pos += 20 # 16 + 4
                current_week_col = BoxLayout(orientation='vertical', spacing=4, size_hint_x=None, width=16)
                day_in_week_count = 0
            
            current += timedelta(days=1)
            
        # Finish last week if partial
        if day_in_week_count > 0:
            for _ in range(7 - day_in_week_count):
                empty = HeatmapCell()
                empty.opacity = 0
                current_week_col.add_widget(empty)
            grid_box.add_widget(current_week_col)
            current_x_pos += 20
        
        # Add Label for the Final Month
        if last_month:
            width = current_x_pos - month_start_x
            center_x = month_start_x + (width / 2)
            month_labels.append((last_month, center_x))

        # Set exact width of grid_box
        total_width = current_x_pos 
        
        grid_box.width = total_width
        right_col.width = total_width
        
        # --- Month Labels Layer ---
        from kivy.uix.relativelayout import RelativeLayout
        header_rel = RelativeLayout(size_hint_x=None, width=total_width, size_hint_y=None, height=20)
        
        for m_text, center_x in month_labels:
            # Center the label at center_x
            # We assume label width is 40. pos = center_x - 20
            lbl = Label(
                text=m_text, 
                font_size='10sp', 
                color=(0.5,0.5,0.5,1), 
                size_hint= (None, None),
                size=(40, 20),
                pos=(center_x - 20, 0),
                halign='center', valign='bottom'
            )
            header_rel.add_widget(lbl)
            
        right_col.add_widget(header_rel)
        right_col.add_widget(grid_box)
        
        heatmap.add_widget(right_col)

    def get_color_for_activity(self, count):
        # Dark theme base: (0.15, 0.17, 0.20, 1) -> Empty
        # Accent is Blueish (0.345, 0.651, 1.0, 1)
        # We interpolate alph or mix
        if count == 0:
            return (0.15, 0.17, 0.20, 1)
        elif count < 100:
             return (0.19, 0.35, 0.55, 1)
        elif count < 500:
             return (0.26, 0.50, 0.77, 1)
        else:
             return (0.345, 0.651, 1.0, 1)


class PlaceholderDisplay(Screen):
    text = StringProperty("")

class HomeScreen(Screen):
    pass # Defined in KV mostly
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
        Clock.schedule_once(self.populate_grid, 0)

    def populate_grid(self, dt):
        print(f"DEBUG: Populating grid for {self.date_str}")
        if 'grid_layout' not in self.ids:
            print("DEBUG: grid_layout not found in self.ids, retrying...")
            # KV rule might not have applied yet?
            # Or ids not populated. Retry.
            Clock.schedule_once(self.populate_grid, 0.05)
            return

        self.questions = dm.load_questions_for_date(self.date_str)
        print(f"DEBUG: Questions loaded: {self.questions}")
        
        saved_data = dm.load_entry(self.date_str)
        
        grid = self.ids.grid_layout
        if grid:
            grid.cols = 3 if len(self.questions) >= 9 else 2
            grid.clear_widgets()
            
            if not self.questions:
                print("DEBUG: No questions found!")
                # Optional: Add a label saying "No questions configured."
                
            for q in self.questions:
                ans = saved_data.get(q, "")
                item = DiaryEntryItemCard(question=q, answer=ans)
                grid.add_widget(item)
            print("DEBUG: Grid populated with widgets")

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
        self.load_day_into_view(new_date, animate=True, direction=direction)

    def load_day_into_view(self, date_str, animate=True, direction='left'):
        # Sync state property
        self.current_date_str = date_str
        
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if date_str == today:
            self.current_date_display_day = "TODAY"
        else:
            self.current_date_display_day = dt.strftime("%A").upper()
            
        self.current_date_display_date = dt.strftime("%b %d, %Y")
        
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

class CalendarViewScreen(Screen):
    target_year = NumericProperty(datetime.now().year)
    
    def setup_view(self, year):
        self.target_year = year
        self.populate_calendar()

    def populate_calendar(self):
        container = self.ids.calendar_container
        container.clear_widgets()
        
        all_data = dm.get_all_entries()
        
        # We'll render 12 months for self.target_year
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        
        for i, month_name in enumerate(months):
            m_idx = i + 1
            
            # Month Header
            from kivy.uix.label import Label
            header = Label(text=f"{month_name} {self.target_year}", font_size='20sp', 
                           color=(0.788, 0.82, 0.851, 1), size_hint_y=None, height='40dp', bold=True)
            container.add_widget(header)
            
            # Days Header (Mo Tu We ...)
            days_header = GridLayout(cols=7, size_hint_y=None, height='30dp', spacing=5)
            for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                lbl = Label(text=d, color=(0.545, 0.58, 0.62, 1), font_size='12sp')
                days_header.add_widget(lbl)
            container.add_widget(days_header)
            
            # Days Grid
            # Calculate gridrows
            # First day of month
            start_date = datetime(self.target_year, m_idx, 1).date()
            if m_idx == 12:
                end_date = datetime(self.target_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(self.target_year, m_idx + 1, 1).date() - timedelta(days=1)
                
            days_in_month = (end_date - start_date).days + 1
            start_weekday = start_date.weekday() # 0=Mon
            
            # Total cells = start_padding + days
            # We need explicit grid layout
            grid = GridLayout(cols=7, size_hint_y=None, spacing=5, padding=[0, 0, 0, 20])
            # Bind height to minimum height
            grid.bind(minimum_height=grid.setter('height'))
            
            # Padding
            from widgets import CalendarDayCell
            for _ in range(start_weekday):
                empty = CalendarDayCell(text="", color_bg=(0,0,0,0))
                grid.add_widget(empty)
                
            # Days
            current_d = start_date
            for _ in range(days_in_month):
                d_str = current_d.strftime("%Y-%m-%d")
                
                # Check Data
                has_entry = d_str in all_data
                
                # Colors
                # Green: (0.137, 0.525, 0.211, 1) or similar accent
                bg_color = (0.15, 0.17, 0.20, 1) # Default Surface
                txt_color = (0.788, 0.82, 0.851, 1) # Main Text
                
                if has_entry:
                    bg_color = (0.2, 0.6, 0.3, 1) # Active Green
                    txt_color = (1, 1, 1, 1)
                
                cell = CalendarDayCell(text=str(current_d.day), color_bg=bg_color, text_color=txt_color, date_ref=d_str)
                grid.add_widget(cell)
                
                current_d += timedelta(days=1)
                
            container.add_widget(grid)


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
