from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.app import App

class ImageButton(ButtonBehavior, Image):
    """Clickable image button"""
    pass

class TopBar(BoxLayout):
  
    
    def navigate_back(self):
       
        try:
            app = App.get_running_app()
            if app and app.root:
                print(f"Navigating back to home from {app.root.current}")
                app.root.current = 'home'
            else:
                print("App or root not found")
        except Exception as e:
            print(f"Navigation error: {e}")
            import traceback
            traceback.print_exc()

