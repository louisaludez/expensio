from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Line
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

def save_users(users):
    """Persist users back to the JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

class NotificationCard(BoxLayout):
    """Widget for displaying a notification"""
    def __init__(self, message, time_ago, icon, color, notification_type=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [10, 10, 10, 10]
        self.spacing = 4
        
        # Normalize color (fallback to muted teal)
        if not color:
            color = get_color_from_hex("#4A7DA5")
        self.card_color = color
        
        # Rounded background with subtle border + shadow
        border_color = (*self.card_color[:3], 0.55)
        
        def update_background(instance, *_):
            if instance.width <= 0 or instance.height <= 0:
                return
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0, 0, 0, 0.05)
                RoundedRectangle(
                    pos=(instance.x, instance.y - 1),
                    size=(instance.width, instance.height + 1),
                    radius=[14]
                )
                Color(1, 1, 1, 1)
                RoundedRectangle(
                    pos=instance.pos,
                    size=instance.size,
                    radius=[14]
                )
                Color(*border_color)
                Line(
                    rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, 14),
                    width=0.9
                )
        
        self.bind(pos=update_background, size=update_background)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: update_background(self), 0.05)
        
        # Icon + message row
        icon_row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=12)
        
        icon_wrapper = AnchorLayout(size_hint=(None, None), size=(30, 30), padding=0)
        
        def update_icon_bg(wrapper, *_):
            wrapper.canvas.before.clear()
            with wrapper.canvas.before:
                Color(self.card_color[0], self.card_color[1], self.card_color[2], 0.15)
                RoundedRectangle(pos=wrapper.pos, size=wrapper.size, radius=[10])
        
        icon_wrapper.bind(pos=update_icon_bg, size=update_icon_bg)
        Clock.schedule_once(lambda dt: update_icon_bg(icon_wrapper), 0)
        
        icon_img = Image(
            source=icon,
            size_hint=(None, None),
            size=(16, 16),
            allow_stretch=True
        )
        icon_wrapper.add_widget(icon_img)
        icon_row.add_widget(icon_wrapper)
        
        text_container = BoxLayout(orientation="vertical", size_hint_x=1, size_hint_y=None, spacing=4)
        text_container.bind(minimum_height=text_container.setter('height'))
        
        message_label = Label(
            text=message,
            markup=True,
            color=(0.07, 0.2, 0.31, 1),
            font_size=13,
            halign="left",
            valign="top",
            size_hint_y=None,
            size_hint_x=1,
            text_size=(0, None)
        )
        message_label.height = 20
        text_container.add_widget(message_label)
        icon_row.add_widget(text_container)
        self.add_widget(icon_row)
        
        time_container = BoxLayout(orientation="vertical", size_hint_y=None, padding=[icon_wrapper.size[0] + icon_row.spacing, 0, 0, 0])
        time_label = Label(
            text=time_ago,
            color=(0.45, 0.48, 0.52, 1),
            font_size=11,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=16,
            text_size=(0, None)
        )
        time_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        time_container.add_widget(time_label)
        self.add_widget(time_container)
        
        def refresh_layout(*_):
            available_width = self.width - (self.padding[0] + self.padding[2] + icon_wrapper.width + icon_row.spacing)
            if available_width > 0:
                message_label.text_size = (available_width, None)
            text_height = message_label.texture_size[1] if message_label.texture_size else 20
            message_label.height = text_height
            text_container.height = text_height
            icon_row.height = max(icon_wrapper.height, text_height)
            time_container.padding = [icon_wrapper.width + icon_row.spacing, 0, 0, 0]
            time_container.height = time_label.height
            self.height = icon_row.height + time_container.height + self.padding[1] + self.padding[3] + self.spacing
        
        message_label.bind(texture_size=lambda inst, size: refresh_layout())
        self.bind(size=lambda *args: refresh_layout())
        Clock.schedule_once(lambda dt: refresh_layout(), 0.1)

class NotifScreen(Screen):
    def _ensure_notifications_store(self, user_data):
        """Ensure notifications are stored as {id: {cleared: bool}}"""
        needs_save = False
        notifications_state = user_data.get('notifications')
        if notifications_state is None:
            notifications_state = {}
            user_data['notifications'] = notifications_state
            needs_save = True
        
        legacy = user_data.pop('cleared_notifications', None)
        if legacy is not None:
            needs_save = True
            for notif_id in legacy:
                entry = notifications_state.setdefault(notif_id, {})
                if not entry.get('cleared', False):
                    entry['cleared'] = True
        
        return notifications_state, needs_save
    
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
        monthly_budget = user_data.get('monthly_budget', 0)
        
        # Generate notifications
        notifications = []
        
        # Calculate current month expenses
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        # Show transactions from last 7 days
        recent_date_threshold = now - timedelta(days=7)
        current_expenses = 0
        recent_transactions = []
        
        for trans in transactions:
            try:
                trans_date = None
                if 'timestamp' in trans:
                    try:
                        trans_date = datetime.fromisoformat(trans['timestamp'])
                    except:
                        pass
                
                if trans_date is None:
                    date_str = trans.get('date', '')
                    if date_str:
                        try:
                            trans_date = datetime.strptime(date_str, "%m/%d/%Y")
                        except:
                            continue
                    else:
                        continue
                
                if trans_date >= current_month_start and trans.get('type') == 'expense':
                    current_expenses += trans.get('amount', 0)
                    # Show transactions from last 7 days
                    if trans_date >= recent_date_threshold:
                        recent_transactions.append((trans, trans_date))
            except Exception as e:
                # Debug: print error to see what's happening
                import traceback
                print(f"Error processing transaction: {e}")
                print(traceback.format_exc())
                continue
        
        # Track notification states (cleared or not) per user in JSON
        notifications_state, needs_save = self._ensure_notifications_store(user_data)
        
        def should_display(notif_id):
            nonlocal needs_save
            entry = notifications_state.get(notif_id)
            if entry is None:
                notifications_state[notif_id] = {'cleared': False}
                needs_save = True
                return True
            return not entry.get('cleared', False)
        
        # Budget warning notifications
        budget_percentage = (current_expenses / monthly_budget * 100) if monthly_budget > 0 else 0
        
        if budget_percentage >= 100:
            notif_id = 'budget_exceeded'
            if should_display(notif_id):
                notifications.append({
                    'id': notif_id,
                    'type': 'warning',
                    'message': '[b][color=#FF4444]Budget Exceeded![/color][/b] You\'ve exceeded your monthly budget.',
                    'time_ago': 'Just now',
                    'icon': 'assets/increase.png',
                    'color': get_color_from_hex("#FF8C00")
                })
        elif budget_percentage >= 80:
            notif_id = 'budget_warning_80'
            if should_display(notif_id):
                notifications.append({
                    'id': notif_id,
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
                notif_id = 'savings_achievement'
                if should_display(notif_id):
                    notifications.append({
                        'id': notif_id,
                        'type': 'success',
                        'message': f'[b][color=#32CD32]Great job![/color][/b] You saved [b][color=#32CD32]₱{last_week_savings:,.0f}[/color][/b] more this week than last.',
                        'time_ago': '2 hours ago',
                        'icon': 'assets/like.png',
                        'color': get_color_from_hex("#32CD32")
                    })
        
        # Daily tip notification
        notif_id = 'daily_tip'
        if should_display(notif_id):
            notifications.append({
                'id': notif_id,
                'type': 'tip',
                'message': '[b][color=#FF8C00]Tip:[/color][/b] Try logging your expenses daily to stay on track.',
                'time_ago': '1 hour ago',
                'icon': 'assets/lightbulb.png',
                'color': get_color_from_hex("#FFA500")
            })
        
        # Sort recent transactions by date (most recent first)
        recent_transactions.sort(key=lambda x: x[1], reverse=True)
        
        # Debug: Print how many recent transactions were found
        print(f"Found {len(recent_transactions)} recent transactions")
        for trans, trans_date in recent_transactions[:5]:
            print(f"  - {trans.get('category', 'Unknown')}: ₱{trans.get('amount', 0):,.2f} on {trans_date}")
        
        # Recent transaction notifications
        for idx, (trans, trans_date) in enumerate(recent_transactions[:3]):  # Limit to 3 most recent
            notif_id = f'transaction_{trans.get("id", idx)}'
            if should_display(notif_id):
                time_ago = self.get_time_ago(trans_date.isoformat() if isinstance(trans_date, datetime) else str(trans_date))
                category = trans.get("category", "Unknown")
                # Capitalize category name for display
                category_display = category.capitalize() if category else "Unknown"
                notifications.append({
                    'id': notif_id,
                    'type': 'transaction',
                    'message': f'Expense added: {category_display} - ₱{trans.get("amount", 0):,.2f}',
                    'time_ago': time_ago,
                    'icon': 'assets/smartphone.png',
                    'color': get_color_from_hex("#4169E1")
                })
            else:
                print(f"Transaction {notif_id} was already cleared")
        
        if needs_save:
            users[app.current_user] = user_data
            save_users(users)
        
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
                size_hint_x=1,
                height=25,
                text_size=(0, None),
                padding=[0, 0, 0, 8]
            )
            today_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
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
                size_hint_x=1,
                height=25,
                text_size=(0, None),
                padding=[0, 8, 0, 8]
            )
            yesterday_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
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
        """Clear all notifications and save to user data"""
        app = App.get_running_app()
        if not app or not app.current_user:
            return
        
        users = load_users()
        if app.current_user not in users:
            return
        
        user_data = users[app.current_user]
        
        # Get all current notification IDs before clearing
        # We need to mark all current notifications as cleared
        # Generate notifications to get their IDs
        transactions = user_data.get('transactions', [])
        monthly_budget = user_data.get('monthly_budget', 0)
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        # Show transactions from last 7 days
        recent_date_threshold = now - timedelta(days=7)
        current_expenses = 0
        recent_transactions = []
        
        for trans in transactions:
            try:
                trans_date = None
                if 'timestamp' in trans:
                    try:
                        trans_date = datetime.fromisoformat(trans['timestamp'])
                    except:
                        pass
                
                if trans_date is None:
                    date_str = trans.get('date', '')
                    if date_str:
                        try:
                            trans_date = datetime.strptime(date_str, "%m/%d/%Y")
                        except:
                            continue
                    else:
                        continue
                
                if trans_date >= current_month_start and trans.get('type') == 'expense':
                    current_expenses += trans.get('amount', 0)
                    # Show transactions from last 7 days
                    if trans_date >= recent_date_threshold:
                        recent_transactions.append((trans, trans_date))
            except:
                continue
        
        # Collect all notification IDs that would be shown
        notifications_state, needs_save = self._ensure_notifications_store(user_data)
        
        def mark_cleared(notif_id):
            nonlocal needs_save
            entry = notifications_state.get(notif_id)
            if entry is None:
                notifications_state[notif_id] = {'cleared': True}
                needs_save = True
                return
            if not entry.get('cleared', False):
                entry['cleared'] = True
                needs_save = True
        
        # Budget warnings
        budget_percentage = (current_expenses / monthly_budget * 100) if monthly_budget > 0 else 0
        if budget_percentage >= 100:
            mark_cleared('budget_exceeded')
        elif budget_percentage >= 80:
            mark_cleared('budget_warning_80')
        
        # Savings achievement
        total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        total_expenses_all = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        savings = total_income - total_expenses_all
        
        if savings > 0:
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
                mark_cleared('savings_achievement')
        
        # Daily tip
        mark_cleared('daily_tip')
        
        # Recent transactions
        for idx, (trans, trans_date) in enumerate(recent_transactions[:3]):
            notif_id = f'transaction_{trans.get("id", idx)}'
            mark_cleared(notif_id)
        
        # Save cleared notifications
        if needs_save:
            user_data['notifications'] = notifications_state
            users[app.current_user] = user_data
            save_users(users)
        
        # Clear UI
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

