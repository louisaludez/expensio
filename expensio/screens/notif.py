from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.app import App
from kivy.utils import get_color_from_hex
from datetime import datetime, timedelta
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

class NotificationCard(BoxLayout):
    """Widget for displaying a notification"""
    def __init__(self, message, time_ago, icon, color, notification_type=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [12, 12, 12, 12]
        self.spacing = 8
        
        # Store color for canvas updates
        self.card_color = color
        
        # Background with colored border - bind to position changes
        def update_background(instance, value=None):
            if instance.width == 0 or instance.height == 0:
                return
            instance.canvas.before.clear()
            with instance.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                # White background
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(instance.x, instance.y), size=(instance.width, instance.height), radius=[12])
        
        self.bind(pos=update_background, size=update_background)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: update_background(self), 0.2)
        
        # Icon and message row - horizontal layout
        icon_row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=12)
        
        # Icon aligned to top
        icon_img = Image(
            source=icon,
            size_hint=(None, None),
            size=(20, 20),
            allow_stretch=True
        )
        icon_row.add_widget(icon_img)
        
        # Message label with multiline support
        message_label = Label(
            text=message,
            markup=True,
            color=(0, 0, 0, 1),
            font_size=14,
            halign="left",
            valign="top",
            size_hint_x=1,
            size_hint_y=None,
            text_size=(None, None)  # Will be set dynamically for wrapping
        )
        
        # Function to update text_size for multiline wrapping
        def update_message_layout(instance, value=None):
            if instance.width == 0:
                return
            # Calculate available width: card width - left padding - right padding - icon width - spacing
            available_width = instance.width - 12 - 12 - 20 - 12  # 12px left pad, 12px right pad, 20px icon, 12px spacing
            if available_width > 0:
                message_label.text_size = (available_width, None)
        
        # Function to update icon_row height when message text wraps
        def update_row_height(instance, size):
            if size[1] > 0:
                icon_row.height = max(20, size[1] + 4)
        
        # Bind to update layout when card is positioned
        self.bind(size=update_message_layout)
        message_label.bind(texture_size=update_row_height)
        
        icon_row.add_widget(message_label)
        self.add_widget(icon_row)
        
        # Schedule initial layout update
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: update_message_layout(self), 0.1)
        
        # Time ago label
        time_label = Label(
            text=time_ago,
            color=(0.6, 0.6, 0.6, 1),
            font_size=11,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=18,
            text_size=(None, None)
        )
        self.add_widget(time_label)
        
        # Bind to update height
        self.bind(minimum_height=self.setter('height'))

class NotifScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notifications = []
    
    def on_enter(self):
        """Called when screen is entered - refresh notifications"""
        # Update date label
        from datetime import datetime
        if hasattr(self, 'ids') and 'date_label' in self.ids:
            now = datetime.now()
            day_name = now.strftime("%A")
            month_name = now.strftime("%b")
            day_num = now.strftime("%d")
            self.ids.date_label.text = f"{day_name}, {month_name} {day_num}"
        self.load_notifications()
    
    def get_time_ago(self, timestamp_str):
        """Calculate time ago string from timestamp"""
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                return "Recently"
            
            now = datetime.now()
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Recently"
    
    def load_notifications(self):
        """Load and display notifications"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        transactions = user_data.get('transactions', [])
        monthly_budget = user_data.get('monthly_budget', 20000)
        
        # Generate notifications
        notifications = []
        
        # Calculate current month expenses
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        current_expenses = 0
        recent_transactions = []
        
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
                    current_expenses += trans.get('amount', 0)
                    if trans_date >= now - timedelta(days=1):
                        recent_transactions.append((trans, trans_date))
            except:
                continue
        
        # Budget warning notifications
        budget_percentage = (current_expenses / monthly_budget * 100) if monthly_budget > 0 else 0
        
        if budget_percentage >= 100:
            notifications.append({
                'type': 'warning',
                'message': '[b][color=#FF4444]Budget Exceeded![/color][/b] You\'ve exceeded your monthly budget.',
                'time_ago': 'Just now',
                'icon': 'assets/increase.png',
                'color': get_color_from_hex("#FF8C00")
            })
        elif budget_percentage >= 80:
            notifications.append({
                'type': 'warning',
                'message': f'[b][color=#FF8C00]You\'ve reached {int(budget_percentage)}% of your budget:[/color][/b] spend wisely!',
                'time_ago': 'Just now',
                'icon': 'assets/increase.png',
                'color': get_color_from_hex("#FF8C00")
            })
        
        # Savings achievement notification
        total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        total_expenses_all = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        savings = total_income - total_expenses_all
        
        if savings > 0:
            # Compare with last week
            last_week = now - timedelta(days=7)
            last_week_income = sum(
                t.get('amount', 0) for t in transactions
                if t.get('type') == 'income' and
                (datetime.fromisoformat(t.get('timestamp', '')) if 'timestamp' in t else datetime.now()) >= last_week
            )
            last_week_expenses = sum(
                t.get('amount', 0) for t in transactions
                if t.get('type') == 'expense' and
                (datetime.fromisoformat(t.get('timestamp', '')) if 'timestamp' in t else datetime.now()) >= last_week
            )
            last_week_savings = last_week_income - last_week_expenses
            
            if last_week_savings > 500:
                notifications.append({
                    'type': 'success',
                    'message': f'[b][color=#32CD32]Great job![/color][/b] You saved [b][color=#32CD32]₱{last_week_savings:,.0f}[/color][/b] more this week than last.',
                    'time_ago': '2 hours ago',
                    'icon': 'assets/like.png',
                    'color': get_color_from_hex("#32CD32")
                })
        
        # Daily tip notification
        notifications.append({
            'type': 'tip',
            'message': '[b][color=#FF8C00]Tip:[/color][/b] Try logging your expenses daily to stay on track.',
            'time_ago': '1 hour ago',
            'icon': 'assets/lightbulb.png',
            'color': get_color_from_hex("#FFA500")
        })
        
        # Recent transaction notifications
        for trans, trans_date in recent_transactions[:3]:  # Limit to 3 most recent
            time_ago = self.get_time_ago(trans_date.isoformat() if isinstance(trans_date, datetime) else str(trans_date))
            notifications.append({
                'type': 'transaction',
                'message': f'Expense added: {trans.get("category", "Unknown")} - ₱{trans.get("amount", 0):,.2f}',
                'time_ago': time_ago,
                'icon': 'assets/smartphone.png',
                'color': get_color_from_hex("#4169E1")
            })
        
        # Update UI
        if not hasattr(self, 'ids') or 'notifications_scroll' not in self.ids:
            return
        
        scroll_view = self.ids.notifications_scroll
        if not scroll_view:
            return
        
        # Get the container inside ScrollView
        container = None
        for child in scroll_view.children:
            if isinstance(child, BoxLayout) and child.orientation == 'vertical':
                container = child
                break
        
        if not container:
            return
        
        # Clear existing notifications
        container.clear_widgets()
        
        # Group notifications by time (Today, Yesterday, etc.)
        today_notifications = []
        yesterday_notifications = []
        older_notifications = []
        
        for notif in notifications:
            time_str = notif.get('time_ago', '')
            if 'hour' in time_str or 'minute' in time_str or 'Just now' in time_str:
                today_notifications.append(notif)
            elif 'day' in time_str and '1 day' in time_str:
                yesterday_notifications.append(notif)
            else:
                older_notifications.append(notif)
        
        # Add Today section
        if today_notifications:
            today_label = Label(
                text="Today",
                color=get_color_from_hex("#07344E"),
                font_size=16,
                bold=True,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=25,
                text_size=(None, None),
                padding=[0, 0, 0, 8]
            )
            container.add_widget(today_label)
            
            for notif in today_notifications:
                card = NotificationCard(
                    message=notif.get('message', ''),
                    time_ago=notif.get('time_ago', ''),
                    icon=notif.get('icon', ''),
                    color=notif.get('color', (1, 1, 1, 1)),
                    notification_type=notif.get('type', 'info')
                )
                container.add_widget(card)
        
        # Add Yesterday section
        if yesterday_notifications:
            yesterday_label = Label(
                text="Yesterday",
                color=get_color_from_hex("#07344E"),
                font_size=16,
                bold=True,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=25,
                text_size=(None, None),
                padding=[0, 8, 0, 8]
            )
            container.add_widget(yesterday_label)
            
            for notif in yesterday_notifications:
                card = NotificationCard(
                    message=notif.get('message', ''),
                    time_ago=notif.get('time_ago', ''),
                    icon=notif.get('icon', ''),
                    color=notif.get('color', (1, 1, 1, 1)),
                    notification_type=notif.get('type', 'info')
                )
                container.add_widget(card)
        
        # If no notifications, show message
        if not notifications:
            no_notif_label = Label(
                text="No notifications",
                color=(0.5, 0.5, 0.5, 1),
                font_size=14,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=50,
                text_size=(None, None)
            )
            container.add_widget(no_notif_label)
    
    def clear_all_notifications(self):
        """Clear all notifications"""
        if not hasattr(self, 'ids') or 'notifications_scroll' not in self.ids:
            return
        
        scroll_view = self.ids.notifications_scroll
        if not scroll_view:
            return
        
        container = None
        for child in scroll_view.children:
            if isinstance(child, BoxLayout) and child.orientation == 'vertical':
                container = child
                break
        
        if container:
            container.clear_widgets()
            
            no_notif_label = Label(
                text="No notifications",
                color=(0.5, 0.5, 0.5, 1),
                font_size=14,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=50,
                text_size=(None, None)
            )
            container.add_widget(no_notif_label)

