from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.app import App
from kivy.utils import get_color_from_hex
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
        'icon': 'assets/food.png',
        'color': get_color_from_hex("#FF6813"),
        'name': 'Food'
    },
    'transport': {
        'icon': 'assets/transport.png',
        'color': get_color_from_hex("#7395EC"),
        'name': 'Transport'
    },
    'shopping': {
        'icon': 'assets/shopping.png',
        'color': get_color_from_hex("#FF6813"),
        'name': 'Shopping'
    },
    'bills': {
        'icon': 'assets/drop.png',
        'color': get_color_from_hex("#1E45A9"),
        'name': 'Bills'
    },
    'other': {
        'icon': 'assets/settings.png',
        'color': get_color_from_hex("#275926"),
        'name': 'Other'
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
        self.size = (100, 120)
        self.spacing = 5
        self.padding = [10, 10, 10, 10]
        
        # Background
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0, 0, 0, 0.1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
            Color(1, 1, 1, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        
        # Icon
        icon = Image(
            source=category_info['icon'],
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True
        )
        self.add_widget(icon)
        
        # Category name
        name_label = Label(
            text=category_info['name'],
            font_size=12,
            color=(0, 0, 0, 1),
            bold=True,
            size_hint_y=None,
            height=20
        )
        self.add_widget(name_label)
        
        # View button
        view_btn = Button(
            text="View",
            background_color=(0, 0, 0, 0),
            background_normal='',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(60, 20),
            font_size=10,
            bold=True,
            pos_hint={"center_x": 0.5}
        )
        view_btn.bind(on_press=lambda btn: self.view_category(category_key))
        
        with view_btn.canvas.before:
            Color(*category_info['color'])
            RoundedRectangle(pos=view_btn.pos, size=view_btn.size, radius=[10])
        
        self.add_widget(view_btn)
    
    def view_category(self, category_key):
        """Handle view category button press"""
        print(f"View category: {category_key}")
        # Could navigate to a detailed category view screen

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
        
        # Filter categories based on current filter
        filtered_categories = {}
        if self.current_filter == 'personal':
            # Personal categories
            personal_cats = ['food', 'transport', 'shopping', 'skincare', 'travel', 'other']
            for cat in personal_cats:
                if cat in category_counts or cat in CATEGORIES:
                    filtered_categories[cat] = CATEGORIES.get(cat, CATEGORIES['other'])
        elif self.current_filter == 'bills':
            # Bill categories
            bill_cats = ['bills', 'water', 'electricity', 'insurance']
            for cat in bill_cats:
                if cat in category_counts or cat in CATEGORIES:
                    filtered_categories[cat] = CATEGORIES.get(cat, CATEGORIES['other'])
        else:
            # All categories
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
        
        # Update UI - find the appropriate container based on filter
        scroll_id = 'category_scroll' if self.current_filter == 'personal' or self.current_filter == 'all' else 'bills_scroll'
        
        if not hasattr(self, 'ids') or scroll_id not in self.ids:
            return
        
        scroll_view = self.ids[scroll_id]
        if not scroll_view:
            return
        
        # Get the horizontal BoxLayout inside ScrollView
        container = None
        for child in scroll_view.children:
            if isinstance(child, BoxLayout) and child.orientation == 'horizontal':
                container = child
                break
        
        if not container:
            return
        
        # Clear existing cards
        container.clear_widgets()
        
        # Add category cards
        for category_key, category_info in filtered_categories.items():
            count = category_counts.get(category_key, 0)
            card = CategoryCard(category_key, category_info, count)
            container.add_widget(card)
        
        # If no categories, show message
        if not filtered_categories:
            no_cat_label = Label(
                text="No categories found",
                color=(0.5, 0.5, 0.5, 1),
                font_size=14,
                size_hint=(None, None),
                size=(200, 30)
            )
            container.add_widget(no_cat_label)
    
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

