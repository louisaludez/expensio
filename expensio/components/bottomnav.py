from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.app import App

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

