from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
import json
import os

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

# Category definitions with icons and colors
CATEGORIES = {
    'food': {
        'icon': 'assets/food-2.png',
        'color': get_color_from_hex("#FF6813"),
        'name': 'Food'
    },
    'transport': {
        'icon': 'assets/public-transport.png',
        'color': get_color_from_hex("#7395EC"),
        'name': 'Transport'
    },
    'shopping': {
        'icon': 'assets/shopping-2.png',
        'color': get_color_from_hex("#FF6813"),
        'name': 'Shopping'
    },
   
    
    'skincare': {
        'icon': 'assets/skincare.png',
        'color': get_color_from_hex("#FF6813"),
        'name': 'Skincare'
    },
    'travel': {
        'icon': 'assets/travel.png',
        'color': get_color_from_hex("#7395EC"),
        'name': 'Travel'
    },
    'water': {
        'icon': 'assets/drop.png',
        'color': get_color_from_hex("#1E45A9"),
        'name': 'Water'
    },
    'electricity': {
        'icon': 'assets/electrical.png',
        'color': get_color_from_hex("#0D4B59"),
        'name': 'Electricity'
    },
    'insurance': {
        'icon': 'assets/insurance.png',
        'color': get_color_from_hex("#275926"),
        'name': 'Insurance'
    }
}

class CategoryCard(BoxLayout):
    """Widget for displaying a category card"""
    def __init__(self, category_key, category_info, transaction_count, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (110, 130)
        self.spacing = 8
        self.padding = [12, 12, 12, 12]
        
        # Background - white card with border
        def update_background(instance, value=None):
            if instance.width == 0 or instance.height == 0:
                return
            instance.canvas.before.clear()
            with instance.canvas.before:
                # White background
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[12])
                # Border
                Color(0, 0, 0, 0.1)
                Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)
        
        self.bind(pos=update_background, size=update_background)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: update_background(self), 0.1)
        
        # Icon container - centered
        icon_container = AnchorLayout(
            size_hint_y=None,
            height=50,
            anchor_x='center',
            anchor_y='center'
        )
        
        icon = Image(
            source=category_info['icon'],
            size_hint=(None, None),
            size=(40, 40),
            allow_stretch=True
        )
        icon_container.add_widget(icon)
        self.add_widget(icon_container)
        
        # Category name
        name_label = Label(
            text=category_info['name'],
            font_size=12,
            color=(0, 0, 0, 1),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=20,
            text_size=(None, None)
        )
        self.add_widget(name_label)
        
        # View button
        view_btn = Button(
            text="View",
            background_color=(0, 0, 0, 0),
            background_normal='',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(70, 25),
            font_size=11,
            bold=True,
            pos_hint={"center_x": 0.5}
        )
        view_btn.bind(on_press=lambda btn: self.view_category(category_key))
        
        # Draw button background with category color
        def update_btn_bg(instance, value=None):
            if instance.width == 0 or instance.height == 0:
                return
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*category_info['color'])
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        view_btn.bind(pos=update_btn_bg, size=update_btn_bg)
        Clock.schedule_once(lambda dt: update_btn_bg(view_btn), 0.1)
        
        self.add_widget(view_btn)
    
    def view_category(self, category_key):
        """Handle view category button press"""
        app = App.get_running_app()
        if app and app.root:
            # Navigate to category detail screen
            if 'category_detail' in app.root.screen_names:
                detail_screen = app.root.get_screen('category_detail')
                detail_screen.load_category(category_key)
                app.root.current = 'category_detail'

class CategoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_filter = 'all'  # 'all', 'personal', 'bills'
        self.search_text = ''
    
    def on_enter(self):
        """Called when screen is entered - refresh data"""
        Clock.schedule_once(lambda dt: self.load_categories(), 0.1)
    
    def load_categories(self):
        """Load and display categories from transactions"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        transactions = user_data.get('transactions', [])
        
        # Count transactions by category
        category_counts = {}
        for trans in transactions:
            if trans.get('type') == 'expense':  # Only count expenses
                category = trans.get('category', 'other')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get all available categories (show all by default, filter buttons are just for organization)
        filtered_categories = {}
        all_cats = set(category_counts.keys()) | set(CATEGORIES.keys())
        for cat in all_cats:
            if cat in CATEGORIES:
                filtered_categories[cat] = CATEGORIES[cat]
        
        # Apply search filter
        if self.search_text:
            search_lower = self.search_text.lower()
            filtered_categories = {
                k: v for k, v in filtered_categories.items()
                if search_lower in v['name'].lower() or search_lower in k.lower()
            }
        
        # Separate into Personal and Bills categories
        personal_cats = ['food', 'transport', 'shopping', 'skincare', 'travel', 'other']
        bill_cats = ['bills', 'water', 'electricity', 'insurance']
        
        personal_categories = {k: v for k, v in filtered_categories.items() if k in personal_cats}
        bills_categories = {k: v for k, v in filtered_categories.items() if k in bill_cats}
        
        # Update Personal section
        if hasattr(self, 'ids') and 'category_scroll' in self.ids:
            scroll_view = self.ids['category_scroll']
            if scroll_view:
                container = None
                for child in scroll_view.children:
                    if isinstance(child, BoxLayout) and child.orientation == 'horizontal':
                        container = child
                        break
                
                if container:
                    container.clear_widgets()
                    
                    # Add personal category cards
                    for category_key, category_info in personal_categories.items():
                        count = category_counts.get(category_key, 0)
                        card = CategoryCard(category_key, category_info, count)
                        container.add_widget(card)
        
        # Update Bills section
        if hasattr(self, 'ids') and 'bills_scroll' in self.ids:
            scroll_view = self.ids['bills_scroll']
            if scroll_view:
                container = None
                for child in scroll_view.children:
                    if isinstance(child, BoxLayout) and child.orientation == 'horizontal':
                        container = child
                        break
                
                if container:
                    container.clear_widgets()
                    
                    # Add bills category cards
                    for category_key, category_info in bills_categories.items():
                        count = category_counts.get(category_key, 0)
                        card = CategoryCard(category_key, category_info, count)
                        container.add_widget(card)
    
    def on_search_text(self, instance, value):
        """Handle search text changes"""
        self.search_text = value
        self.load_categories()
    
    def filter_personal(self):
        """Filter to show personal categories"""
        self.current_filter = 'personal'
        self.load_categories()
    
    def filter_bills(self):
        """Filter to show bill categories"""
        self.current_filter = 'bills'
        self.load_categories()
    
    def filter_all(self):
        """Show all categories"""
        self.current_filter = 'all'
        self.load_categories()

class CategoryDetailScreen(Screen):
    """Screen for displaying category details and transactions"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_category = None
    
    def on_enter(self):
        """Called when screen is entered"""
        if self.current_category:
            self.load_category(self.current_category)
    
    def load_category(self, category_key):
        """Load and display category details"""
        self.current_category = category_key
        
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        transactions = user_data.get('transactions', [])
        
        # Get category info
        category_info = CATEGORIES.get(category_key, CATEGORIES.get('other', {}))
        
        # Filter transactions for this category
        category_transactions = [
            t for t in transactions 
            if t.get('category') == category_key and t.get('type') == 'expense'
        ]
        
        # Calculate total
        total = sum(t.get('amount', 0) for t in category_transactions)
        
        # Update UI
        if hasattr(self, 'ids'):
            # Update category icon and name
            if 'category_icon' in self.ids:
                self.ids.category_icon.source = category_info.get('icon', 'assets/settings.png')
            
            if 'category_name_label' in self.ids:
                self.ids.category_name_label.text = category_info.get('name', 'Category')
            
            if 'category_total_label' in self.ids:
                self.ids.category_total_label.text = f"Total: ₱ {total:,.2f}"
            
            # Update transactions list
            if 'transactions_scroll' in self.ids:
                scroll_view = self.ids.transactions_scroll
                if scroll_view:
                    container = None
                    for child in scroll_view.children:
                        if isinstance(child, BoxLayout) and child.orientation == 'vertical':
                            container = child
                            break
                    
                    if container:
                        container.clear_widgets()
                        
                        # Sort transactions by date (newest first)
                        category_transactions.sort(
                            key=lambda x: x.get('timestamp', '') or x.get('date', ''),
                            reverse=True
                        )
                        
                        # Add transaction items
                        for trans in category_transactions:
                            trans_item = self.create_transaction_item(trans)
                            container.add_widget(trans_item)
                        
                        # If no transactions, show message
                        if not category_transactions:
                            no_trans_label = Label(
                                text="No transactions in this category yet.",
                                color=(0.5, 0.5, 0.5, 1),
                                font_size=14,
                                halign="center",
                                valign="middle",
                                size_hint_y=None,
                                height=50,
                                text_size=(None, None)
                            )
                            container.add_widget(no_trans_label)
    
    def create_transaction_item(self, transaction):
        """Create a transaction item widget"""
        from kivy.uix.label import Label
        from datetime import datetime
        
        item = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=15,
            padding=[0, 5, 0, 5]
        )
        
        # Background
        def update_item_bg(instance, value=None):
            if instance.width == 0 or instance.height == 0:
                return
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10])
                Color(0, 0, 0, 0.05)
                Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)
        
        item.bind(pos=update_item_bg, size=update_item_bg)
        Clock.schedule_once(lambda dt: update_item_bg(item), 0.1)
        
        # Left side - Description and date
        left_layout = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=3
        )
        
        description = transaction.get('description', 'No description')
        desc_label = Label(
            text=description,
            color=(0, 0, 0, 1),
            font_size=14,
            bold=True,
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=25,
            text_size=(None, None)
        )
        left_layout.add_widget(desc_label)
        
        # Date
        date_str = transaction.get('date', '')
        date_label = Label(
            text=date_str,
            color=(0.5, 0.5, 0.5, 1),
            font_size=11,
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=20,
            text_size=(None, None)
        )
        left_layout.add_widget(date_label)
        item.add_widget(left_layout)
        
        # Right side - Amount
        amount = transaction.get('amount', 0)
        amount_label = Label(
            text=f"₱{amount:,.2f}",
            color=(0, 0, 0, 1),
            font_size=16,
            bold=True,
            halign='right',
            valign='middle',
            size_hint_x=None,
            width=100,
            text_size=(None, None)
        )
        item.add_widget(amount_label)
        
        return item

