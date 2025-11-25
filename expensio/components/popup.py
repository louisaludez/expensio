from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle

class MessagePopup(Popup):
    """Message"""
    def __init__(self, title="Message", message="", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = True
        self.background = ""
        self.background_color = (1, 1, 1, 0)
        self.separator_color = (0, 0, 0, 0)
        
        
        with self.canvas.before:
            Color(*get_color_from_hex("#26536d"))
            self._rounded_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        self.bind(pos=self._update_background, size=self._update_background)
        
        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        # Message label
        message_label = Label(
            text=message,
            text_size=(None, None),
            halign="center",
            valign="middle",
            size_hint_y=1,
            color=(1, 1, 1, 1)  
        )
        content.add_widget(message_label)
        
        
        ok_button = Button(
            text="OK",
            size_hint_y=None,
            height=40,
            background_color=(0, 0, 0, 0), 
            color=(0, 0, 0, 1),  
            background_normal=""
        )
        
        # Draw rounded background for button
        def draw_button_bg(instance, value=None):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)  
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
        
        ok_button.bind(pos=draw_button_bg, size=draw_button_bg)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: draw_button_bg(ok_button), 0.1)
        
        ok_button.bind(on_press=self.dismiss)
        content.add_widget(ok_button)
        
        self.content = content
    
    def _update_background(self, *args):
       
        if hasattr(self, "_rounded_bg"):
            self._rounded_bg.pos = self.pos
            self._rounded_bg.size = self.size

def show_message(title, message):
 
    popup = MessagePopup(title=title, message=message)
    popup.open()
    return popup

def show_error(message):
  
    return show_message("Error", message)

def show_success(message):
   
    return show_message("Success", message)

