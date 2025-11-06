import kivy as kk
from kivy.app import App
from kivy.uix.label import Label

class ExpensioApp(App):
    def build(self):
        return Label(text="Welcome to Expensio!")

if __name__ == "__main__":
    ExpensioApp().run()