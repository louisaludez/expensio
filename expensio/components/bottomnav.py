from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

class ImageButton(ButtonBehavior, Image):
    """Clickable image button"""
    pass

class BottomNavBar(BoxLayout):
    """Reusable bottom navigation bar component"""
    
    def navigate_to_screen(self, screen_name):
        """Navigate to a screen"""
        try:
            app = App.get_running_app()
            if app and app.root:
                print(f"Navigating to: {screen_name}")
                app.root.current = screen_name
            else:
                print("App or root not found")
        except Exception as e:
            print(f"Navigation error: {e}")
            import traceback
            traceback.print_exc()
    
    def show_logout_confirmation(self):
        """Show confirmation popup before logging out"""
        app = App.get_running_app()
        
        # Create popup content
        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        # Message label
        message_label = Label(
            text="Are you sure you want to logout?",
            text_size=(None, None),
            halign="center",
            valign="middle",
            size_hint_y=1,
            color=(1, 1, 1, 1)  
        )
        content.add_widget(message_label)
        
        # Button layout
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        
        # Cancel button 
        cancel_btn = Button(
            text="Cancel",
            background_color=(0, 0, 0, 0),  
            color=(0, 0, 0, 1),  
            background_normal="",
            size_hint_x=0.5
        )
        
        # Draw rounded background for cancel button
        def draw_cancel_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)  
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        cancel_btn.bind(pos=draw_cancel_bg, size=draw_cancel_bg)
        Clock.schedule_once(lambda dt: draw_cancel_bg(cancel_btn), 0.1)
        
        # Logout button 
        logout_btn = Button(
            text="Logout",
            background_color=(0, 0, 0, 0),  
            color=(1, 1, 1, 1), 
            background_normal="",
            size_hint_x=0.5
        )
        
        # Draw rounded background for logout button
        def draw_logout_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*get_color_from_hex("#AD590C"))  
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        logout_btn.bind(pos=draw_logout_bg, size=draw_logout_bg)
        Clock.schedule_once(lambda dt: draw_logout_bg(logout_btn), 0.1)
        
        def confirm_logout(instance):
            popup.dismiss()
            # Clear current user
            if app:
                app.current_user = None
                app.root.current = 'welcome'
        
        logout_btn.bind(on_press=confirm_logout)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(logout_btn)
        content.add_widget(button_layout)
        
        # Create and show popup
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.8, 0.3),
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

