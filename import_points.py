# -- coding: UTF-8 --
import threading
import cv2
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import numpy as np
import time

def show_progress_bar(title, task_function, *args):
    progress_window = tk.Toplevel()
    progress_window.title(title)
    progress_window.geometry("300x100")
    progress_window.resizable(False, False)
    progress_window.attributes("-toolwindow", 1)
    progress_window.overrideredirect(True)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

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

def show_loading_screen():
    loading_window = tk.Toplevel()
    loading_window.title("")
    loading_window.geometry("300x100")
    loading_window.resizable(False, False)
    loading_window.attributes("-toolwindow", 1)
    loading_window.protocol("WM_DELETE_WINDOW", lambda: None)
    loading_window.overrideredirect(True)

    screen_width = loading_window.winfo_screenwidth()
    screen_height = loading_window.winfo_screenheight()
    x = (screen_width - 300) // 2
    y = (screen_height - 100) // 2
    loading_window.geometry(f"300x100+{x}+{y}")
    
    tk.Label(loading_window, text="launching...", font=("Arial", 16)).pack(pady=20)

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

def import_task(filename):
    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(filename)
    else:
        raise ValueError("Unsupported file format")

    required_columns = ['X', 'Y', 'Grayscale']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("The file must contain 'X', 'Y', and 'Grayscale' columns")

    min_x, max_x = df['X'].min().astype(int), df['X'].max().astype(int)
    min_y, max_y = df['Y'].min().astype(int), df['Y'].max().astype(int)
    
    img = np.zeros((max_y - min_y + 1, max_x - min_x + 1), dtype=np.uint8)

    for _, row in df.iterrows():
        x, y, gray = row['X'].astype(int), row['Y'].astype(int), row['Grayscale'].astype(int)
        img[max_y - y, x - min_x] = gray

    return img

def import_and_draw_image():
    filename = filedialog.askopenfilename(
        title="Select data file",
        filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")),
    )
    if not filename:
        return

    try:
        imported_img = show_progress_bar("Importing Data", import_task, filename)
        show_scaled_image(imported_img)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import data: {str(e)}")


def show_scaled_image(img):
    cv2.namedWindow("Imported Image", cv2.WINDOW_NORMAL)
    cv2.imshow("Imported Image", img)
    
    def close_window():
        cv2.destroyAllWindows()
        root.quit()
    
    root.after(100, lambda: root.bind('<Key>', lambda e: close_window()))
    root.mainloop()

root = tk.Tk()
root.withdraw()

show_loading_screen()
root.title("Import and Draw Image")

root.deiconify()
tk.Button(root, text="Import Data", command=import_and_draw_image).pack(pady=20)

root.mainloop()