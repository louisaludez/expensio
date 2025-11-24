from kivy.uix.screenmanager import Screen
from kivy.app import App
from datetime import datetime, timedelta
import json
import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, PushMatrix, PopMatrix, Translate
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
        self._instruction_group.add(Color(0.027, 0.204, 0.306, 1))  # Dark teal #07344E
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
        monthly_budget = user_data.get('monthly_budget', 20000)  # Default budget
        current_expenses = sum(t.get('amount', 0) for t in current_transactions if t.get('type') == 'expense')
        current_income = sum(t.get('amount', 0) for t in current_transactions if t.get('type') == 'income')
        
        # Calculate progress (expenses / budget)
        progress = min(1.0, current_expenses / monthly_budget) if monthly_budget > 0 else 0.0
        
        # Calculate last month budget
        last_month_expenses = sum(t.get('amount', 0) for t in last_transactions if t.get('type') == 'expense')
        last_month_budget = user_data.get('last_month_budget', last_month_expenses)
        
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
                'food': 'food_count_label',
                'transport': 'transport_count_label',
                'shopping': 'shopping_count_label'
            }
            
            for category, label_id in category_mapping.items():
                if label_id in self.ids:
                    count = category_totals.get(category, 0)
                    self.ids[label_id].text = f"{count:,.0f}" if count > 0 else "0"
