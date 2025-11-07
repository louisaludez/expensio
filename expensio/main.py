from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
import ctypes
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
import json
import os

# Set window properties
Window.size = (300, 600)
Window.clearcolor = (1, 1, 1, 1)

# Load all KV files
Builder.load_file("welcome.kv")
Builder.load_file("login.kv")
Builder.load_file("signup.kv")
Builder.load_file("home.kv")
Builder.load_file("notif.kv")
Builder.load_file("category.kv")
Builder.load_file("chart.kv")
Builder.load_file("add_transaction.kv")

# Center window
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)
Window.left = int((screen_width - Window.size[0]) / 2)
Window.top = int((screen_height - Window.size[1]) / 2)

# JSON file path for user data
USERS_FILE = "users.json"

def load_users():
    #Load users from JSON file
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    # Save users to JSON file
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Screen classes
class WelcomeScreen(Screen):
    def go_to_sign_up(self):
        self.manager.current = 'sign_up'
    
    def go_to_login(self):
        self.manager.current = 'login'

class HomeScreen(Screen): pass
class NotifScreen(Screen): pass
class CategoryScreen(Screen): pass
class ChartScreen(Screen): pass
class AddTransactionScreen(Screen): pass

class LoginScreen(Screen):
    def login(self):
        username = self.ids.login_username.text.strip()
        password = self.ids.login_password.text.strip()
        
        if not username or not password:
            print("Please fill in all fields")
            return
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            print(f"Login successful for {username}")
            # Store the logged-in username in the app
            app = App.get_running_app()
            app.current_user = username
            self.ids.login_username.text = ""
            self.ids.login_password.text = ""
            self.manager.current = 'home'
        else:
            print("Invalid username or password")
            self.ids.login_password.text = ""
    
    def go_to_sign_up(self):
        self.manager.current = 'sign_up'

class SignUpScreen(Screen):
    def sign_up(self):
        username = self.ids.signup_username.text.strip()
        password = self.ids.signup_password.text.strip()
        confirm_password = self.ids.signup_confirm_password.text.strip()
        
        if not username or not password or not confirm_password:
            print("Please fill in all fields")
            return
        
        if password != confirm_password:
            print("Passwords do not match")
            self.ids.signup_password.text = ""
            self.ids.signup_confirm_password.text = ""
            return
        
        users = load_users()
        
        if username in users:
            print("Username already exists")
            self.ids.signup_username.text = ""
            return
        
        # Save new user
        users[username] = {
            'password': password
        }
        save_users(users)
        
        print(f"Sign up successful for {username}")
        # Store the logged-in username in the app
        app = App.get_running_app()
        app.current_user = username
        self.ids.signup_username.text = ""
        self.ids.signup_password.text = ""
        self.ids.signup_confirm_password.text = ""
        self.manager.current = 'home'
    
    def go_to_login(self):
        self.manager.current = 'login'

class ExpensioApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None  # Store the logged-in username
    
    def build(self):
        self.get_color_from_hex = get_color_from_hex
        sm = ScreenManager()

        sm.add_widget(NotifScreen(name='notif'))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(HomeScreen(name='home'))
        
        sm.add_widget(CategoryScreen(name='category'))
        sm.add_widget(ChartScreen(name='chart'))
        sm.add_widget(AddTransactionScreen(name='add_transaction'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SignUpScreen(name='sign_up'))
        return sm


if __name__ == '__main__':
    ExpensioApp().run()
