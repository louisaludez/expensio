from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from datetime import datetime, timedelta
import json
import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, PushMatrix, PopMatrix, Translate, RoundedRectangle
from kivy.graphics.instructions import InstructionGroup
import math

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

class CircularBudgetWidget(Widget):
    def __init__(self, **kwargs):
        self.progress = kwargs.pop('progress', 0.0)  # Progress as decimal (0.0 to 1.0)
        super().__init__(**kwargs)
        self._instruction_group = None
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        # Schedule initial update after widget is fully initialized
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._update_canvas(), 0.1)
    
    def set_progress(self, progress):
        """Update progress value"""
        self.progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
        self._update_canvas()
    
    def _update_canvas(self, *args):
        if self.width == 0 or self.height == 0:
            return
        
        # Remove old instructions
        if self._instruction_group:
            self.canvas.remove(self._instruction_group)
        
        # Create new instruction group
        self._instruction_group = InstructionGroup()
        
        # Use widget's own coordinate system (0,0 is bottom-left of widget)
        center_x = self.width / 2
        center_y = self.height / 2
        radius = min(self.width, self.height) / 2 - 10
        inner_radius = radius - 20  # Thickness of ring
        
        # Shadow
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0, 0, 0, 0.12))
        shadow_size = radius * 2 + 20
        self._instruction_group.add(Ellipse(size=(shadow_size, shadow_size), pos=(-radius - 10 + 3, -radius - 10 - 3)))
        self._instruction_group.add(PopMatrix())
        
        # Thick outer ring (light beige/cream)
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0.96, 0.94, 0.90, 1))  # Light beige/cream
        outer_size = radius * 2 + 20
        self._instruction_group.add(Ellipse(size=(outer_size, outer_size), pos=(-radius - 10, -radius - 10)))
        # Inner circle to create ring
        self._instruction_group.add(Color(0.98, 0.98, 0.97, 1))  # Light off-white
        inner_size = inner_radius * 2
        self._instruction_group.add(Ellipse(size=(inner_size, inner_size), pos=(-inner_radius, -inner_radius)))
        self._instruction_group.add(PopMatrix())
        
        # Background wavy graph area (light orange/peach)
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y - 15))
        self._instruction_group.add(Color(1, 0.85, 0.7, 0.25))  # Light orange/peach
        graph_w = inner_radius * 1.7
        graph_h = inner_radius * 0.9
        self._instruction_group.add(Ellipse(size=(graph_w, graph_h), pos=(-inner_radius * 0.85, -inner_radius * 0.45)))
        self._instruction_group.add(PopMatrix())
        
        # Ring borders for definition
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        # Outer edge
        self._instruction_group.add(Color(0.90, 0.88, 0.83, 1))
        self._instruction_group.add(Line(circle=(0, 0, radius + 10, 0, 360), width=1.5))
        # Inner edge
        self._instruction_group.add(Color(0.95, 0.93, 0.88, 1))
        self._instruction_group.add(Line(circle=(0, 0, inner_radius, 0, 360), width=1))
        self._instruction_group.add(PopMatrix())
        
        # Dotted progress line (dark teal)
        # Draw dots along progress percentage of the circle
        progress_degrees = 360 * self.progress
        start_angle = -90  # Start from top
        num_dots = int(progress_degrees / 8) if progress_degrees > 0 else 0  # Approximately one dot every 8 degrees
        dot_radius = 3
        
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0.027, 0.204, 0.306, 1))  
        for i in range(num_dots):
            angle_rad = math.radians(start_angle + (progress_degrees * i / num_dots) if num_dots > 0 else start_angle)
            x = (radius + 10) * math.cos(angle_rad)
            y = (radius + 10) * math.sin(angle_rad)
            self._instruction_group.add(Ellipse(size=(dot_radius * 2, dot_radius * 2), pos=(x - dot_radius, y - dot_radius)))
        self._instruction_group.add(PopMatrix())
        
        # Add instruction group to canvas
        self.canvas.add(self._instruction_group)

class ChartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def on_enter(self):
        """Called when screen is entered - refresh data"""
        self.update_chart_data()
    
    def get_current_month_transactions(self, transactions):
        """Get transactions for the current month"""
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        current_month_end = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
        
        current_transactions = []
        for trans in transactions:
            try:
                # Try parsing timestamp first
                if 'timestamp' in trans:
                    trans_date = datetime.fromisoformat(trans['timestamp'])
                else:
                    # Fallback to date field
                    date_str = trans.get('date', '')
                    if date_str:
                        trans_date = datetime.strptime(date_str, "%m/%d/%Y")
                    else:
                        continue
                
                if current_month_start <= trans_date < current_month_end:
                    current_transactions.append(trans)
            except:
                continue
        
        return current_transactions
    
    def get_last_month_transactions(self, transactions):
        """Get transactions for the last month"""
        now = datetime.now()
        if now.month == 1:
            last_month_start = datetime(now.year - 1, 12, 1)
            last_month_end = datetime(now.year, 1, 1)
        else:
            last_month_start = datetime(now.year, now.month - 1, 1)
            last_month_end = datetime(now.year, now.month, 1)
        
        last_transactions = []
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
                
                if last_month_start <= trans_date < last_month_end:
                    last_transactions.append(trans)
            except:
                continue
        
        return last_transactions
    
    def update_chart_data(self):
        """Update chart with calculated data"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        all_transactions = user_data.get('transactions', [])
        
        # Get current month transactions
        current_transactions = self.get_current_month_transactions(all_transactions)
        last_transactions = self.get_last_month_transactions(all_transactions)
        
        # Calculate current month budget and expenses
        monthly_budget = user_data.get('monthly_budget', 0)  # Default budget
        current_expenses = sum(t.get('amount', 0) for t in current_transactions if t.get('type') == 'expense')
        current_income = sum(t.get('amount', 0) for t in current_transactions if t.get('type') == 'income')
        
        # Calculate progress (expenses / budget)
        progress = min(1.0, current_expenses / monthly_budget) if monthly_budget > 0 else 0.0
        
        # Calculate last month budget
        # Get the budget that was saved for last month
       
        last_month_expenses = sum(t.get('amount', 0) for t in last_transactions if t.get('type') == 'expense')
        
        # Check if we have a saved last month budget (only exists after month change)
        last_month_budget = user_data.get('last_month_budget', None)
        
      
      
        if last_month_budget is None:
           
            last_month_budget = 0
        
        # Calculate category totals for current month
        category_totals = {}
        for trans in current_transactions:
            if trans.get('type') == 'expense':
                category = trans.get('category', 'other')
                category_totals[category] = category_totals.get(category, 0) + trans.get('amount', 0)
        
        # Update UI elements if they exist
        if hasattr(self, 'ids'):
            # Update circular progress widget
            if 'budget_widget' in self.ids:
                widget = self.ids.budget_widget
                if hasattr(widget, 'set_progress'):
                    widget.set_progress(progress)
            
            # Update budget amount (show total monthly budget)
            if 'budget_amount_label' in self.ids:
                self.ids.budget_amount_label.text = f"₱ {monthly_budget:,.0f}"
            
            # Update last month budget text
            if 'last_month_budget_label' in self.ids:
                self.ids.last_month_budget_label.text = f"₱ {last_month_budget:,.0f} was your previous budget."
            
            # Update motivational message
            if 'motivational_label' in self.ids:
                if progress < 0.5:
                    message = "[b][i][color=#AD590C]You are doing well in keeping on track with your budget![/color][/i][/b]"
                elif progress < 0.8:
                    message = "[b][i][color=#FF8C00]You're getting close to your budget limit. Spend wisely![/color][/i][/b]"
                else:
                    message = "[b][i][color=#FF4444]Warning: You've exceeded your budget![/color][/i][/b]"
                self.ids.motivational_label.text = message
            
            # Update category cards
            category_mapping = {
                'transport': 'transport_count_label',
                'shopping': 'shopping_count_label',
                'travel': 'travel_count_label',
                'skincare': 'skincare_count_label',
                'food': 'food_count_label',
                'insurance': 'insurance_count_label',
                'water': 'water_count_label',
                'electricity': 'electricity_count_label'
            }
            
            for category, label_id in category_mapping.items():
                if label_id in self.ids:
                    count = category_totals.get(category, 0)
                    self.ids[label_id].text = f"{count:,.0f}" if count > 0 else "0"
    
    def edit_monthly_budget(self):
        """Open popup to edit monthly budget"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        current_budget = user_data.get('monthly_budget', 0)
        
        # Create popup content
        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        # Title
        title_label = Label(
            text="Edit Monthly Budget",
            font_size=18,
            bold=True,
            size_hint_y=None,
            height=30,
            color=(1, 1, 1, 1) 
        )
        content.add_widget(title_label)
        
        # Budget input container
        input_container = BoxLayout(orientation="vertical", size_hint_y=None, height=50)
        
        # Create input layout with background
        input_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10, padding=[10, 0])
        
        # Draw background for input
        def draw_input_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*get_color_from_hex("#E0E0E0"))
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        input_layout.bind(pos=draw_input_bg, size=draw_input_bg)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: draw_input_bg(input_layout), 0.1)
        
        budget_input = TextInput(
            text=str(int(current_budget)),
            font_size=16,
            multiline=False,
            input_filter="int",
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10],
            size_hint_x=1,
            background_normal="",
            background_active=""
        )
        input_layout.add_widget(budget_input)
        input_container.add_widget(input_layout)
        content.add_widget(input_container)
        
        # Buttons
        button_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        
        cancel_btn = Button(
            text="Cancel",
            background_color=(0, 0, 0, 0),  
            color=(0, 0, 0, 1), 
            size_hint_x=0.5,
            background_normal=""
        )
        
        # Draw rounded background for cancel button
        def draw_cancel_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1) 
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        cancel_btn.bind(pos=draw_cancel_bg, size=draw_cancel_bg)
        Clock.schedule_once(lambda dt: draw_cancel_bg(cancel_btn), 0.1)
        
        save_btn = Button(
            text="Save",
            background_color=(0, 0, 0, 0),  
            color=(1, 1, 1, 1), 
            size_hint_x=0.5,
            background_normal=""
        )
        
        # Draw rounded background for save button
        def draw_save_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*get_color_from_hex("#AD590C"))
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        save_btn.bind(pos=draw_save_bg, size=draw_save_bg)
        Clock.schedule_once(lambda dt: draw_save_bg(save_btn), 0.1)
        
        def save_budget(instance):
            try:
                new_budget = float(budget_input.text)
                if new_budget < 0:
                    return
                
                # Update budget
                users = load_users()
                if app.current_user in users:
                    users[app.current_user]['monthly_budget'] = new_budget
                    # Save to file
                    with open(USERS_FILE, 'w') as f:
                        json.dump(users, f, indent=4)
                    
                    # Refresh chart data
                    self.update_chart_data()
                    # Refresh home screen if it exists
                    home_screen = app.root.get_screen('home')
                    if hasattr(home_screen, 'update_balance_card'):
                        home_screen.update_balance_card()
                
                popup.dismiss()
            except ValueError:
                pass
        
        save_btn.bind(on_press=save_budget)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        content.add_widget(button_layout)
        
        # Create and show popup
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
            background="",
            background_color=(1, 1, 1, 0),
            separator_color=(0, 0, 0, 0)
        )
        
        # Draw rounded background
        def draw_popup_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*get_color_from_hex("#26536d"))
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[20])
        
        popup.bind(pos=draw_popup_bg, size=draw_popup_bg)
        Clock.schedule_once(lambda dt: draw_popup_bg(popup), 0.1)
        
        popup.open()
