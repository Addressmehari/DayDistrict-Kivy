from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty
from kivy.app import App
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
                screen = app.root.get_screen('diary')
                if dx > 0: 
                    # Swipe Right -> Previous Day (Left)
                    screen.change_day(-1, direction='right')
                else:
                    # Swipe Left -> Next Day (Right)
                    screen.change_day(1, direction='left')
                return True
        return False

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
