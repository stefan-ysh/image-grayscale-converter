import tkinter as tk
import time

class LoadingScreen:
    def __init__(self, width=300, height=100, title="", text="launching...", font=("Arial", 16)):
        self.width = width
        self.height = height
        self.title = title
        self.text = text
        self.font = font

    def show(self):
        loading_window = tk.Toplevel()
        loading_window.title(self.title)
        loading_window.geometry(f"{self.width}x{self.height}")
        loading_window.resizable(False, False)
        loading_window.attributes("-toolwindow", 1)
        loading_window.protocol("WM_DELETE_WINDOW", lambda: None)
        loading_window.overrideredirect(True)

        screen_width = loading_window.winfo_screenwidth()
        screen_height = loading_window.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        loading_window.geometry(f"{self.width}x{self.height}+{x}+{y}")

        loading_label = tk.Label(loading_window, text=self.text, font=self.font)
        loading_label.pack(pady=20)

        progress_bar = tk.Canvas(loading_window, width=200, height=20)
        progress_bar.pack()

        steps = 200
        for i in range(steps):
            progress_bar.delete("all")
            width = (i + 1) * 200 / steps
            progress_bar.create_rectangle(0, 0, width, 20, fill="blue", outline="")
            loading_window.update()
            time.sleep(0.01)

        loading_window.destroy()

def show_loading_screen():
    loading_screen = LoadingScreen()
    loading_screen.show()
