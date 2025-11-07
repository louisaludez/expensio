from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
import ctypes

# Set window properties
Window.size = (329, 769)
Window.clearcolor = (1, 1, 1, 1)

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
