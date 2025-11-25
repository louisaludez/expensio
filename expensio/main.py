from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, TransitionBase
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale
import ctypes
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
import json
import os
import hashlib
import secrets
from datetime import datetime
from screens.chart import CircularBudgetWidget, ChartScreen
from components.topbar import TopBar
from components.bottomnav import BottomNavBar
from components.popup import show_message, show_error, show_success
from kivy.uix.behaviors import ButtonBehavior

# Set window properties
Window.size = (300, 600)
Window.clearcolor = (1, 1, 1, 1)

# Load component KV files first
Builder.load_file("components/topbar.kv")
Builder.load_file("components/bottomnav.kv")

# Load all screen KV files
Builder.load_file("welcome.kv")
Builder.load_file("login.kv")
Builder.load_file("signup.kv")
Builder.load_file("home.kv")
Builder.load_file("notif.kv")
Builder.load_file("category.kv")
Builder.load_file("category_detail.kv")
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

def hash_password(password):
    """Hash a password using SHA-256 with a salt"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Combine password and salt
    password_salt = password + salt
    # Hash the combined string
    hashed = hashlib.sha256(password_salt.encode()).hexdigest()
    # Return salt and hash combined (salt:hash format)
    return f"{salt}:{hashed}"

def verify_password(password, stored_hash):
    """Verify a password against a stored hash"""
    try:
        # Check if it's a legacy plain text password
        if ':' not in stored_hash:
            # Legacy plain text - compare directly
            return password == stored_hash
        # Split salt and hash
        salt, hashed = stored_hash.split(':', 1)
        # Hash the password with the stored salt
        password_salt = password + salt
        computed_hash = hashlib.sha256(password_salt.encode()).hexdigest()
        # Compare hashes
        return computed_hash == hashed
    except:
        return False

# Custom Pop-up Transition
class PopUpTransition(TransitionBase):
    """Custom transition that creates a pop-up effect with scale and fade"""
    
    def start(self, manager):
        # Store manager reference
        self.manager = manager
        
        # Set initial state for incoming screen
        self.screen_in.pos = manager.pos
        self.screen_in.size = manager.size
        self.screen_in.opacity = 0
        
        # Calculate center point for scaling
        center_x = manager.center_x
        center_y = manager.center_y
        
        # Store canvas instructions for cleanup
        self.canvas_instructions = []
        
        # Add canvas instructions for scaling
        with self.screen_in.canvas.before:
            push = PushMatrix()
            self.canvas_instructions.append(push)
            
            # Translate to center, scale, then translate back
            translate1 = Translate(x=-center_x, y=-center_y)
            self.canvas_instructions.append(translate1)
            
            self.scale_instruction = Scale()
            self.scale_instruction.x = 0.5
            self.scale_instruction.y = 0.5
            self.canvas_instructions.append(self.scale_instruction)
            
            translate2 = Translate(x=center_x, y=center_y)
            self.canvas_instructions.append(translate2)
            
            pop = PopMatrix()
            self.canvas_instructions.append(pop)
            self.pop_matrix = pop
        
        # Fade out the outgoing screen
        if self.screen_out:
            anim_out = Animation(
                opacity=0,
                duration=self.duration * 0.3,
                transition='in_quad'
            )
            anim_out.start(self.screen_out)
        
        # Animate the pop-up effect (scale up and fade in)
        self.scale_anim = Animation(
            opacity=1,
            duration=self.duration,
            transition='out_back'
        )
        self.scale_anim.bind(on_progress=self._on_progress)
        self.scale_anim.bind(on_complete=self._on_anim_complete)
        self.scale_anim.start(self.screen_in)
        
        return super().start(manager)
    
    def _on_progress(self, anim, widget, progress):
        """Update scale during animation"""
        if hasattr(self, 'scale_instruction'):
            # Scale from 0.5 to 1.0 with a bounce effect
            # Using out_back transition creates the pop effect
            scale_value = 0.5 + (1.0 - 0.5) * progress
            self.scale_instruction.x = scale_value
            self.scale_instruction.y = scale_value
    
    def _on_anim_complete(self, anim, widget):
        """Clean up canvas instructions when animation completes"""
        if hasattr(self, 'canvas_instructions') and self.screen_in:
            try:
                # Remove all canvas instructions in reverse order
                for instruction in reversed(self.canvas_instructions):
                    self.screen_in.canvas.before.remove(instruction)
            except:
                pass
        self.on_complete()
    
    def on_complete(self):
        # Ensure final state is correct
        if self.screen_in:
            self.screen_in.opacity = 1
        if self.screen_out:
            self.screen_out.opacity = 0
        return super().on_complete()

# Screen classes
class WelcomeScreen(Screen):
    def go_to_sign_up(self):
        self.manager.current = 'sign_up'
    
    def go_to_login(self):
        self.manager.current = 'login'

from screens.home import HomeScreen
from screens.notif import NotifScreen
from screens.category import CategoryScreen, CategoryDetailScreen
# ChartScreen imported from screens.chart
class CategoryButton(ButtonBehavior, BoxLayout):
    """Clickable category button widget"""
    pass

class AddTransactionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_type = 'expense'  # Default to expense
        self.selected_category = None
    
    def on_enter(self):
        """Called when screen is entered - reset form"""
        # Set default transaction type to expense
        self.set_transaction_type('expense')
        # Clear inputs
        if hasattr(self, 'ids'):
            if 'amount_input' in self.ids:
                self.ids.amount_input.text = ""
            if 'description_input' in self.ids:
                self.ids.description_input.text = ""
            if 'date_input' in self.ids:
                # Set today's date as default
                today = datetime.now().strftime("%m/%d/%Y")
                self.ids.date_input.text = today
            self.selected_category = None
    
    def set_transaction_type(self, type_name):
        """Set the transaction type (income or expense) with visual feedback"""
        self.transaction_type = type_name
        
        if not hasattr(self, 'ids'):
            return
        
        # Update button styles
        income_btn = self.ids.get('income_btn')
        expense_btn = self.ids.get('expense_btn')
        
        if income_btn and expense_btn:
            from kivy.graphics import Color, RoundedRectangle
            if type_name == 'income':
                # Highlight income button
                income_btn.canvas.before.clear()
                with income_btn.canvas.before:
                    Color(0, 0.831, 0.667, 1)  
                    RoundedRectangle(pos=income_btn.pos, size=income_btn.size, radius=[8])
                # Dim expense button
                expense_btn.canvas.before.clear()
                with expense_btn.canvas.before:
                    Color(0.678, 0.349, 0.047, 0.5) 
                    RoundedRectangle(pos=expense_btn.pos, size=expense_btn.size, radius=[8])
            else:  # expense
                # Highlight expense button
                expense_btn.canvas.before.clear()
                with expense_btn.canvas.before:
                    Color(0.678, 0.349, 0.047, 1)  
                    RoundedRectangle(pos=expense_btn.pos, size=expense_btn.size, radius=[8])
                # Dim income button
                income_btn.canvas.before.clear()
                with income_btn.canvas.before:
                    Color(0, 0.831, 0.667, 0.5)  
                    RoundedRectangle(pos=income_btn.pos, size=income_btn.size, radius=[8])
    
    def set_category(self, category_name):
        """Set the selected category with visual feedback"""
        self.selected_category = category_name
        
        if not hasattr(self, 'ids'):
            return
        
        from kivy.graphics import Color, Line, RoundedRectangle
        
        # Reset all category buttons
        category_ids = ['category_transport', 'category_shopping', 'category_travel', 'category_skincare', 'category_food', 'category_insurance', 'category_water', 'category_electricity']
        
        for cat_id in category_ids:
            btn = self.ids.get(cat_id)
            if btn:
                # Reset to default style
                btn.canvas.before.clear()
                with btn.canvas.before:
                    Color(0, 0, 0, 0.1)
                    Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=1)
                    Color(1, 1, 1, 1)
                    RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
        
        # Highlight selected category
        category_mapping = {
            'transport': 'category_transport',
            'shopping': 'category_shopping',
            'travel': 'category_travel',
            'skincare': 'category_skincare',
            'food': 'category_food',
            'insurance': 'category_insurance',
            'water': 'category_water',
            'electricity': 'category_electricity'
        }
        
        selected_id = category_mapping.get(category_name)
        if selected_id:
            btn = self.ids.get(selected_id)
            if btn:
                btn.canvas.before.clear()
                with btn.canvas.before:
                    Color(0.027, 0.204, 0.306, 0.3)  # #07344E with transparency for highlight
                    RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
                    Color(0, 0, 0, 0.2)
                    Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)
                    Color(1, 1, 1, 1)
                    RoundedRectangle(pos=(btn.x + 1, btn.y + 1), size=(btn.width - 2, btn.height - 2), radius=[9])
    
    def add_transaction(self):
        """Add the transaction"""
        if not hasattr(self, 'ids'):
            return
        
        # Get input values
        amount_text = self.ids.amount_input.text.strip() if 'amount_input' in self.ids else ""
        description = self.ids.description_input.text.strip() if 'description_input' in self.ids else ""
        date = self.ids.date_input.text.strip() if 'date_input' in self.ids else ""
        
        # Validate amount
        if not amount_text:
            show_error("Please enter an amount")
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                show_error("Amount must be greater than 0")
                return
        except ValueError:
            show_error("Please enter a valid amount")
            return
        
        # Validate category
        if not self.selected_category:
            show_error("Please select a category")
            return
        
        # Get logged-in user
        app = App.get_running_app()
        if not app.current_user:
            show_error("No user logged in. Please log in again.")
            self.manager.current = 'login'
            return
        
        # Create transaction data with timestamp
        transaction = {
            'id': datetime.now().strftime("%Y%m%d%H%M%S%f"),  # Unique ID based on timestamp
            'type': self.transaction_type,
            'amount': amount,
            'category': self.selected_category,
            'description': description if description else f"{self.selected_category.title()} transaction",
            'date': date if date else datetime.now().strftime("%m/%d/%Y"),
            'timestamp': datetime.now().isoformat()  # For sorting/filtering
        }
        
        # Load users and add transaction
        users = load_users()
        
        # Initialize transactions array if it doesn't exist (for existing users)
        if app.current_user not in users:
            show_error("User not found in database. Please log in again.")
            self.manager.current = 'login'
            return
        
        if 'transactions' not in users[app.current_user]:
            users[app.current_user]['transactions'] = []
        
        # Add transaction to user's transactions
        users[app.current_user]['transactions'].append(transaction)
        
        # Save updated users data
        save_users(users)
        
        # Show success message
        show_success("Transaction added successfully!")
        
        # Navigate back to home after a short delay and refresh home screen
        from kivy.clock import Clock
        def navigate_and_refresh(dt):
            self.manager.current = 'home'
            # Refresh home screen data
            home_screen = self.manager.get_screen('home')
            if hasattr(home_screen, 'on_enter'):
                home_screen.on_enter()
        Clock.schedule_once(navigate_and_refresh, 0.5)

class LoginScreen(Screen):
    def login(self):
        username = self.ids.login_username.text.strip()
        password = self.ids.login_password.text.strip()
        
        if not username or not password:
            show_error("Please fill in all fields")
            return
        
        users = load_users()
        
        if username in users and verify_password(password, users[username]['password']):
            # Migrate legacy plain text password to hashed on successful login
            stored_password = users[username]['password']
            if ':' not in stored_password:
                # This is a legacy plain text password - hash it now
                users[username]['password'] = hash_password(password)
                save_users(users)
            
            # Store the logged-in username in the app
            app = App.get_running_app()
            app.current_user = username
            self.ids.login_username.text = ""
            self.ids.login_password.text = ""
            show_success(f"Welcome back, {username}!")
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'home'), 0.5)
        else:
            show_error("Invalid username or password")
            self.ids.login_password.text = ""
    
    def go_to_sign_up(self):
        self.manager.current = 'sign_up'

class SignUpScreen(Screen):
    def sign_up(self):
        username = self.ids.signup_username.text.strip()
        password = self.ids.signup_password.text.strip()
        confirm_password = self.ids.signup_confirm_password.text.strip()
        
        if not username or not password or not confirm_password:
            show_error("Please fill in all fields")
            return
        
        if len(username) < 3:
            show_error("Username must be at least 3 characters long")
            return
        
        if len(password) < 3:
            show_error("Password must be at least 3 characters long")
            return
        
        if password != confirm_password:
            show_error("Passwords do not match")
            self.ids.signup_password.text = ""
            self.ids.signup_confirm_password.text = ""
            return
        
        users = load_users()
        
        if username in users:
            show_error("Username already exists. Please choose a different username.")
            self.ids.signup_username.text = ""
            return
        
        # Save new user with empty transactions list
        # Hash the password before storing
        hashed_password = hash_password(password)
        users[username] = {
            'password': hashed_password,
            'transactions': [],
            'monthly_budget': 0  # Default monthly budget
        }
        save_users(users)
        
        # Store the logged-in username in the app
        app = App.get_running_app()
        app.current_user = username
        self.ids.signup_username.text = ""
        self.ids.signup_password.text = ""
        self.ids.signup_confirm_password.text = ""
        show_success(f"Account created successfully! Welcome, {username}!")
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'home'), 0.5)
    
    def go_to_login(self):
        self.manager.current = 'login'

class ExpensioApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None  # Store the logged-in username
    
    def build(self):
        self.get_color_from_hex = get_color_from_hex
        sm = ScreenManager(transition=PopUpTransition(duration=0.4))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(ChartScreen(name='chart'))
        sm.add_widget(CategoryScreen(name='category'))
        sm.add_widget(CategoryDetailScreen(name='category_detail'))
        sm.add_widget(NotifScreen(name='notif'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(AddTransactionScreen(name='add_transaction'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SignUpScreen(name='sign_up'))
        sm.current = 'welcome'  # Start with welcome screen
        return sm


if __name__ == '__main__':
    ExpensioApp().run()
