import tkinter as tk
import threading
from tkinter import ttk


def show_progress_bar(title, task_function, *args):
    progress_window = tk.Toplevel()
    progress_window.title(title)
    progress_window.geometry("300x100")
    progress_window.resizable(False, False)
    progress_window.attributes("-toolwindow", 1)
    progress_window.overrideredirect(True)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

    # Center the window
    x = (progress_window.winfo_screenwidth() - 300) // 2
    y = (progress_window.winfo_screenheight() - 100) // 2
    progress_window.geometry(f"300x100+{x}+{y}")

    tk.Label(progress_window, text="Processing...", font=("Arial", 16)).pack(pady=10)
    progress_window.grab_set()

    progress_bar = ttk.Progressbar(progress_window, length=200, mode="indeterminate")
    progress_bar.pack(pady=10)
    progress_bar.start()

    result = None

    def run_task():
        nonlocal result
        result = task_function(*args)
        progress_window.quit()

    threading.Thread(target=run_task, daemon=True).start()

    progress_window.mainloop()
    progress_window.destroy()
    return result
