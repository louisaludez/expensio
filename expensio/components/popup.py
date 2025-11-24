from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex

class MessagePopup(Popup):
    """Simple message popup for showing alerts/errors"""
    def __init__(self, title="Message", message="", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = True
        
        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        # Message label
        message_label = Label(
            text=message,
            text_size=(None, None),
            halign="center",
            valign="middle",
            size_hint_y=1
        )
        content.add_widget(message_label)
        
        # OK button
        ok_button = Button(
            text="OK",
            size_hint_y=None,
            height=40,
            background_color=get_color_from_hex("#07344E"),
            color=(1, 1, 1, 1),
            background_normal=""
        )
        ok_button.bind(on_press=self.dismiss)
        content.add_widget(ok_button)
        
        self.content = content

def show_message(title, message):
    """Helper function to show a message popup"""
    popup = MessagePopup(title=title, message=message)
    popup.open()
    return popup

def show_error(message):
    """Helper function to show an error popup"""
    return show_message("Error", message)

def show_success(message):
    """Helper function to show a success popup"""
    return show_message("Success", message)

