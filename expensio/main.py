from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
import ctypes
from kivy.utils import get_color_from_hex
from kivy.lang import Builder

# Set window properties
Window.size = (300, 600)
Window.clearcolor = (1, 1, 1, 1)

Builder.load_file("expensio.kv")

# Center window
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)
Window.left = int((screen_width - Window.size[0]) / 2)
Window.top = int((screen_height - Window.size[1]) / 2)


# Screen placeholders
class WelcomeScreen(Screen): pass
class HomeScreen(Screen): pass
class NotifScreen(Screen): pass
class CategoryScreen(Screen): pass
class ChartScreen(Screen): pass
class AddTransactionScreen(Screen): pass


class ExpensioApp(App):
    def build(self):
        self.get_color_from_hex = get_color_from_hex
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(NotifScreen(name='notif'))
        sm.add_widget(CategoryScreen(name='category'))
        sm.add_widget(ChartScreen(name='chart'))
        sm.add_widget(AddTransactionScreen(name='add_transaction'))
        return sm


if __name__ == '__main__':
    ExpensioApp().run()
