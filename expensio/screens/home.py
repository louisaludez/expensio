from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.clock import Clock
from components.popup import show_error, show_success
from datetime import datetime
import json
import os
import secrets
import hashlib

# Category icon mapping
CATEGORY_ICONS = {
    'transport': 'assets/public-transport.png',
    'shopping': 'assets/shopping-2.png',
    'travel': 'assets/travel.png',
    'skincare': 'assets/skincare.png',
    'food': 'assets/food-2.png',
    'insurance': 'assets/insurance.png',
    'water': 'assets/drop.png',
    'electricity': 'assets/electrical.png',
    'other': 'assets/settings.png'
}

# Category colors for icon backgrounds
CATEGORY_COLORS = {
    'transport': (0, 0, 0, 1),
    'shopping': get_color_from_hex("#07344E"),
    'travel': (0, 0, 0, 1),
    'skincare': (0.6, 0.4, 0.2, 1),
    'food': (0.6, 0.4, 0.2, 1),
    'insurance': (0.2, 0.4, 0.2, 1),
    'water': (0.2, 0.4, 0.6, 1),
    'electricity': (0.2, 0.4, 0.6, 1),
    'other': (0.5, 0.5, 0.5, 1)
}

USERS_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

class TransactionItem(BoxLayout):
    """Widget for displaying a single transaction"""
    def __init__(self, transaction, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 55
        self.spacing = 12
        
        # Category icon
        category = transaction.get('category', 'other')
        icon_path = CATEGORY_ICONS.get(category, CATEGORY_ICONS['other'])
        icon_color = CATEGORY_COLORS.get(category, CATEGORY_COLORS['other'])
        
        # Create icon container with circular background
        icon_layout = FloatLayout()
        icon_layout.size_hint_x = None
        icon_layout.width = 40
        icon_layout.height = 40
        
       
        def draw_circle(instance):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*icon_color)
                Ellipse(pos=instance.pos, size=instance.size)
        
       
        icon_layout.bind(pos=lambda inst, pos: draw_circle(inst), 
                        size=lambda inst, size: draw_circle(inst))
        
      
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: draw_circle(icon_layout), 0.1)
        
        # Create icon image
        icon_img = Image(
            source=icon_path,
            size_hint=(None, None),
            size=(24, 24),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True
        )
        icon_layout.add_widget(icon_img)
        self.add_widget(icon_layout)
        
        # Transaction details
        details_layout = BoxLayout(orientation="vertical", size_hint_x=1, spacing=3)
        
        category_label = Label(
            text=f"[b]{category.title()}[/b]",
            markup=True,
            color=(0, 0, 0, 1),
            font_size=14,
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=details_layout.texture_size[1] if hasattr(details_layout, 'texture_size') else 20,
            text_size=(None, None)
        )
        details_layout.add_widget(category_label)
        
        description = transaction.get('description', 'No description')
        desc_label = Label(
            text=description,
            color=(0.5, 0.5, 0.5, 1),
            font_size=11,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=details_layout.texture_size[1] if hasattr(details_layout, 'texture_size') else 15,
            text_size=(None, None)
        )
        details_layout.add_widget(desc_label)
        self.add_widget(details_layout)
        
        # Amount and date
        amount_layout = BoxLayout(orientation="vertical", size_hint_x=None, width=90, spacing=3)
        
        amount = transaction.get('amount', 0)
        trans_type = transaction.get('type', 'expense')
        amount_color = (0, 0, 0, 1) if trans_type == 'expense' else get_color_from_hex("#00D4AA")
        amount_prefix = "-" if trans_type == 'expense' else "+"
        
        amount_label = Label(
            text=f"[b]{amount_prefix}₱{amount:,.2f}[/b]",
            markup=True,
            color=amount_color,
            font_size=14,
            bold=True,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=amount_layout.texture_size[1] if hasattr(amount_layout, 'texture_size') else 20,
            text_size=(None, None)
        )
        amount_layout.add_widget(amount_label)
        
        # Format date
        date_str = transaction.get('date', '')
        date_label = Label(
            text=date_str,
            color=(0.5, 0.5, 0.5, 1),
            font_size=10,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=amount_layout.texture_size[1] if hasattr(amount_layout, 'texture_size') else 15,
            text_size=(None, None)
        )
        amount_layout.add_widget(date_label)
        self.add_widget(amount_layout)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transactions_container = None
        self.drawer_open = False
        Clock.schedule_once(lambda dt: self._update_drawer_position(), 0)
    
    def on_enter(self):
        """Called when screen is entered - refresh data"""
        self.load_transactions()
        self.update_balance_card()
        self._update_drawer_position()
        self._update_drawer_username()
    
    def on_size(self, *args):
        """Ensure drawer stays aligned when screen resizes"""
        self._update_drawer_position()
    
    def _update_drawer_position(self):
        drawer = self.ids.get('settings_drawer') if hasattr(self, 'ids') else None
        if drawer:
            drawer.x = self.width - drawer.width if self.drawer_open else self.width
        backdrop = self.ids.get('drawer_backdrop') if hasattr(self, 'ids') else None
        username_label = self.ids.get('drawer_username_label') if hasattr(self, 'ids') else None
        app = App.get_running_app()
        if backdrop:
            if self.drawer_open:
                backdrop.size_hint = (1, 1)
                backdrop.size = self.size
                backdrop.disabled = False
                backdrop.opacity = 0.4
            else:
                backdrop.size_hint = (None, None)
                backdrop.size = (0, 0)
                backdrop.opacity = 0
                backdrop.disabled = True
        if username_label and app and app.current_user:
            username_label.text = app.current_user
        elif username_label:
            username_label.text = ""
    
    def _update_drawer_username(self):
        if hasattr(self, 'ids') and 'drawer_username_label' in self.ids:
            app = App.get_running_app()
            if app and app.current_user:
                self.ids.drawer_username_label.text = app.current_user
            else:
                self.ids.drawer_username_label.text = ""
    
    def toggle_drawer(self):
        """Slide the navigation drawer in/out"""
        if not hasattr(self, 'ids'):
            return
        drawer = self.ids.get('settings_drawer')
        backdrop = self.ids.get('drawer_backdrop')
        if not drawer or not backdrop:
            return
        
        target_x = self.width - drawer.width if not self.drawer_open else self.width
        Animation(x=target_x, d=0.25, t='out_quad').start(drawer)
        
        if self.drawer_open:
            anim_bg = Animation(opacity=0, d=0.25)
            anim_bg.bind(on_complete=lambda *args: self._disable_backdrop(backdrop))
            anim_bg.start(backdrop)
        else:
            backdrop.size_hint = (1, 1)
            backdrop.size = self.size
            backdrop.disabled = False
            Animation(opacity=0.4, d=0.25).start(backdrop)
        
        self.drawer_open = not self.drawer_open
    
    def _disable_backdrop(self, backdrop):
        backdrop.size_hint = (None, None)
        backdrop.size = (0, 0)
        backdrop.opacity = 0
        backdrop.disabled = True
    
    def open_change_password_popup(self):
        """Show popup with change password form"""
        if self.drawer_open:
            self.toggle_drawer()
        
        app = App.get_running_app()
        if not app or not app.current_user:
            show_error("Please log in again.")
            return
        
        content = BoxLayout(orientation="vertical", padding=20, spacing=12)
        
        current_container, current_input = self._create_password_input("Current Password")
        new_container, new_input = self._create_password_input("New Password")
        confirm_container, confirm_input = self._create_password_input("Confirm New Password")
        
        input_fields = [current_input, new_input, confirm_input]
        for container, field in [
            (current_container, current_input),
            (new_container, new_input),
            (confirm_container, confirm_input)
        ]:
            self._setup_placeholder_behavior(field)
            content.add_widget(container)
        
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        
        cancel_btn = Button(
            text="Cancel",
            color=(0, 0, 0, 1),
            background_color=(0, 0, 0, 0),
            background_normal=""
        )
        save_btn = Button(
            text="Save",
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal=""
        )
        
        self._style_button(cancel_btn, (1, 1, 1, 1))
        self._style_button(save_btn, get_color_from_hex("#AD590C"))
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.45),
            auto_dismiss=False,
            background="",
            background_color=(1, 1, 1, 0),
            separator_color=(0, 0, 0, 0)
        )
        
        def draw_popup_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*get_color_from_hex("#26536d"))
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[20])
        
        popup.bind(pos=draw_popup_bg, size=draw_popup_bg)
        Clock.schedule_once(lambda dt: draw_popup_bg(popup), 0.1)
        
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
        save_btn.bind(on_release=lambda *_: self.change_password(
            popup,
            current_input.text.strip(),
            new_input.text.strip(),
            confirm_input.text.strip()
        ))
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        content.add_widget(button_layout)
        
        popup.open()
        Clock.schedule_once(lambda dt: setattr(current_input, 'focus', True), 0.15)
    
    def _setup_placeholder_behavior(self, field):
        """Hide hint text while focused for clearer typing"""
        original_hint = field.hint_text
        
        def handle_focus(instance, value):
            if value:
                instance.hint_text = ""
            elif not instance.text:
                instance.hint_text = original_hint
        
        field.bind(focus=handle_focus)
    
    def _create_password_input(self, hint_text):
        """Create a styled container + password input"""
        container = BoxLayout(size_hint_y=None, height=46, padding=(0, 0, 0, 0))
        
        def draw_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10])
        
        container.bind(pos=draw_bg, size=draw_bg)
        Clock.schedule_once(lambda dt: draw_bg(container), 0.05)
        
        text_input = TextInput(
            hint_text=hint_text,
            password=True,
            multiline=False,
            padding=(12, 12),
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            cursor_width=2,
            hint_text_color=(0.4, 0.4, 0.4, 1),
            background_normal="",
            background_active="",
            size_hint=(1, 1),
            write_tab=False
        )
        container.add_widget(text_input)
        return container, text_input
    
    def navigate_to(self, screen_name):
        """Navigate to another screen from the drawer"""
        if self.drawer_open:
            self.toggle_drawer()
        Clock.schedule_once(lambda dt: self._switch_screen(screen_name), 0.25)
    
    def _switch_screen(self, screen_name):
        app = App.get_running_app()
        if not app or not hasattr(app, 'root') or not app.root:
            return
        screen_manager = app.root
        try:
            if screen_manager.has_screen(screen_name):
                screen_manager.current = screen_name
        except:
            pass
    
    def open_budget_editor(self):
        """Go to chart screen and open the budget editor"""
        if self.drawer_open:
            self.toggle_drawer()
        
        def _open_budget(dt):
            app = App.get_running_app()
            if not app or not hasattr(app, 'root') or not app.root:
                return
            manager = app.root
            if not manager.has_screen('chart'):
                return
            manager.current = 'chart'
            try:
                chart_screen = manager.get_screen('chart')
                if hasattr(chart_screen, 'edit_monthly_budget'):
                    Clock.schedule_once(lambda _dt: chart_screen.edit_monthly_budget(), 0.2)
            except:
                pass
        
        Clock.schedule_once(_open_budget, 0.3)
    
    def _style_input_field(self, field):
        def draw_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        field.bind(pos=draw_bg, size=draw_bg)
        Clock.schedule_once(lambda dt: draw_bg(field), 0.1)
    
    def _style_button(self, button, bg_color):
        def draw_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                if isinstance(bg_color, tuple):
                    Color(*bg_color)
                else:
                    Color(*bg_color)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        button.bind(pos=draw_bg, size=draw_bg)
        Clock.schedule_once(lambda dt: draw_bg(button), 0.1)
    
    def change_password(self, popup, current_password, new_password, confirm_password):
        """Validate and update the user's password"""
        if not current_password or not new_password or not confirm_password:
            show_error("Please fill in all fields.")
            return
        if len(new_password) < 6:
            show_error("Password must be at least 6 characters.")
            return
        if new_password != confirm_password:
            show_error("New passwords do not match.")
            return
        
        app = App.get_running_app()
        if not app or not app.current_user:
            show_error("Please log in again.")
            return
        
        users = load_users()
        if app.current_user not in users:
            show_error("User not found.")
            return
        
        stored_password = users[app.current_user].get('password', '')
        if not self._verify_password(current_password, stored_password):
            show_error("Current password is incorrect.")
            return
        
        users[app.current_user]['password'] = self._hash_password(new_password)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        show_success("Password updated successfully.")
        popup.dismiss()
    
    def load_transactions(self):
        """Load and display transactions from users.json"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        transactions = user_data.get('transactions', [])
        
        # Sort transactions by timestamp (newest first)
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Get the transactions container from KV
        if not hasattr(self, 'ids') or 'transactions_scroll' not in self.ids:
            return
        
        # Find the container inside ScrollView
        scroll_view = self.ids.transactions_scroll
        if not scroll_view:
            return
        
        # Get the BoxLayout container inside ScrollView
        container = None
        for child in scroll_view.children:
            if isinstance(child, BoxLayout):
                container = child
                break
        
        if not container:
            return
        
       
        container.clear_widgets()
        
        # Add transaction items (limit to 10 most recent for home screen)
        for transaction in transactions[:10]:
            transaction_item = TransactionItem(transaction)
            container.add_widget(transaction_item)
        
        # If no transactions, show a message
        if not transactions:
            no_trans_label = Label(
                text="No transactions yet.\nAdd your first transaction!",
                color=(0.5, 0.5, 0.5, 1),
                font_size=14,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=100,
                text_size=(None, None)
            )
            container.add_widget(no_trans_label)
    
    def update_balance_card(self):
        """Update the balance card with calculated values"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        transactions = user_data.get('transactions', [])
        monthly_budget = user_data.get('monthly_budget', 0)  # Default budget
        
        # Get current month info
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        current_month_key = f"{now.year}-{now.month:02d}" 
        
        # Get last processed month from user data
        last_processed_month = user_data.get('last_processed_month', None)
        
        
        if last_processed_month is None:
            user_data['savings'] = 0
            user_data['last_processed_month'] = current_month_key
            users[app.current_user] = user_data
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=4)
      
        elif last_processed_month != current_month_key:
            # Check if we need to roll over previous month's balance to savings
            last_month_end = current_month_start
            if now.month == 1:
                last_month_start = datetime(now.year - 1, 12, 1)
            else:
                last_month_start = datetime(now.year, now.month - 1, 1)
            
            # Calculate previous month's expenses
            last_month_expenses = 0
            for trans in transactions:
                try:
                    if 'timestamp' in trans:
                        trans_date = datetime.fromisoformat(trans['timestamp'])
                    else:
                        date_str = trans.get('date', '')
                        if date_str:
                            trans_date = datetime.strptime(date_str, "%m/%d/%Y")
                        else:
                            continue
                    
                    if last_month_start <= trans_date < last_month_end and trans.get('type') == 'expense':
                        last_month_expenses += trans.get('amount', 0)
                except:
                    continue
            
            # Calculate previous month's remaining balance
            last_month_remaining = max(0, monthly_budget - last_month_expenses)
            
            # Add to savings
            current_savings = user_data.get('savings', 0)
            new_savings = current_savings + last_month_remaining
            
            # Save the previous month's budget before updating
            # This will be used to display "last month budget" in chart screen
            user_data['last_month_budget'] = monthly_budget
            
            # Update user data
            user_data['savings'] = new_savings
            user_data['last_processed_month'] = current_month_key
            
            # Save updated data
            users[app.current_user] = user_data
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=4)
        
        # Calculate current month expenses
        current_month_expenses = 0
        for trans in transactions:
            try:
                if 'timestamp' in trans:
                    trans_date = datetime.fromisoformat(trans['timestamp'])
                else:
                    date_str = trans.get('date', '')
                    if date_str:
                        trans_date = datetime.strptime(date_str, "%m/%d/%Y")
                    else:
                        continue
                
                if trans_date >= current_month_start and trans.get('type') == 'expense':
                    current_month_expenses += trans.get('amount', 0)
            except:
                continue
        
        # Calculate available balance (monthly budget - current month expenses)
        available_balance = monthly_budget - current_month_expenses
        
        # Calculate totals for expenses display
        total_expenses = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        
        # Get accumulated savings from user data (only from previous months, not current month)
        
        savings = user_data.get('savings', 0)
        
        # Update labels if they exist
        if hasattr(self, 'ids'):
            if 'total_balance_label' in self.ids:
                self.ids.total_balance_label.text = f"₱ {available_balance:,.2f}"
            
            if 'savings_label' in self.ids:
                self.ids.savings_label.text = f"₱ {savings:,.2f}"
            
            if 'expenses_label' in self.ids:
                self.ids.expenses_label.text = f"₱ {total_expenses:,.2f}"

    def _hash_password(self, password):
        """Hash a password using SHA-256 with a salt"""
        salt = secrets.token_hex(16)
        password_salt = password + salt
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    def _verify_password(self, password, stored_hash):
        """Verify password against stored hash (supports legacy plain text)"""
        try:
            if ':' not in stored_hash:
                return password == stored_hash
            salt, hashed = stored_hash.split(':', 1)
            password_salt = password + salt
            computed_hash = hashlib.sha256(password_salt.encode()).hexdigest()
            return computed_hash == hashed
        except:
            return False

