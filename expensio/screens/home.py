from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse
from kivy.app import App
from kivy.utils import get_color_from_hex
from datetime import datetime
import json
import os

# Category icon mapping
CATEGORY_ICONS = {
    'food': 'assets/food.png',
    'transport': 'assets/transport.png',
    'shopping': 'assets/shopping.png',
    'bills': 'assets/drop.png',
    'other': 'assets/settings.png'
}

# Category colors for icon backgrounds
CATEGORY_COLORS = {
    'food': (0.6, 0.4, 0.2, 1),
    'transport': (0, 0, 0, 1),
    'shopping': get_color_from_hex("#07344E"),
    'bills': (0.2, 0.4, 0.6, 1),
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
        
        # Draw circular background - use bind to update when positioned
        def draw_circle(instance):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*icon_color)
                Ellipse(pos=instance.pos, size=instance.size)
        
        # Bind to update circle when widget is positioned
        icon_layout.bind(pos=lambda inst, pos: draw_circle(inst), 
                        size=lambda inst, size: draw_circle(inst))
        
        # Schedule initial draw after widget is added
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
    
    def on_enter(self):
        """Called when screen is entered - refresh data"""
        self.load_transactions()
        self.update_balance_card()
    
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
        
        # Clear existing transaction widgets (except the first one which might be a placeholder)
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
        
        # Calculate totals
        total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        total_expenses = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        total_balance = total_income - total_expenses
        
        # Get savings (if set by user, otherwise use a default or calculate)
        savings = user_data.get('savings', 0)
        if savings == 0 and total_balance > 0:
            savings = total_balance * 0.3  # Default to 30% of balance as savings
        
        # Update labels if they exist
        if hasattr(self, 'ids'):
            if 'total_balance_label' in self.ids:
                self.ids.total_balance_label.text = f"₱ {total_balance:,.2f}"
            
            if 'savings_label' in self.ids:
                self.ids.savings_label.text = f"₱ {savings:,.2f}"
            
            if 'expenses_label' in self.ids:
                self.ids.expenses_label.text = f"₱ {total_expenses:,.2f}"

