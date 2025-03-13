# PPDWindow.py, Charlie Jordan, 3/13/2025

import tkinter as tk
from tkinter import ttk

class PPDWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        # self.withdraw()

        print(self.bind("<Key>", self.key_bind))
        # self.destroy()
        self.after_code = self.after(1000, self.destroy)
    
    def key_bind(self, e: tk.Event):
        print(e)
        if e.keysym.lower().startswith("control"):

        # self.unbind()
        pass