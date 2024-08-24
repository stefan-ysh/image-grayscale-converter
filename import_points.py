# -- coding: UTF-8 --
import threading
import cv2
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import numpy as np
import time
from PIL import Image, ImageTk

def show_progress_bar(title, task_function, *args):
    progress_window = tk.Toplevel()
    progress_window.title(title)
    progress_window.geometry("400x100")
    progress_window.resizable(False, False)
    progress_window.attributes("-toolwindow", 1)
    progress_window.overrideredirect(True)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

    x = (progress_window.winfo_screenwidth() - 400) // 2
    y = (progress_window.winfo_screenheight() - 100) // 2
    progress_window.geometry(f"400x100+{x}+{y}")

    progress_label = tk.Label(progress_window, text="Processing...", font=("Arial", 12))
    progress_label.pack(pady=5)
    progress_window.grab_set()

    progress_bar = ttk.Progressbar(progress_window, length=300, mode="determinate")
    progress_bar.pack(pady=5)

    result = None

    def run_task():
        nonlocal result
        result = task_function(progress_label, progress_bar, *args)
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
    
    tk.Label(loading_window, text="Launching...", font=("Arial", 16)).pack(pady=20)

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

def import_task(progress_label, progress_bar, filename, file_index, total_files):
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

    total_rows = len(df)
    for index, row in df.iterrows():
        x, y, gray = row['X'].astype(int), row['Y'].astype(int), row['Grayscale'].astype(int)
        img[max_y - y, x - min_x] = gray
        
        # Update progress
        progress = (index + 1) / total_rows
        progress_bar['value'] = progress * 100
        progress_label.config(text=f"Processing file {file_index}/{total_files}, row {index + 1}/{total_rows}")
        progress_label.update()

    return img

def import_and_draw_images():
    filenames = filedialog.askopenfilenames(
        title="Select data files",
        filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")),
    )
    if not filenames:
        return

    try:
        images = []
        total_files = len(filenames)
        for i, filename in enumerate(filenames, 1):
            imported_img = show_progress_bar(f"Importing Data", import_task, filename, i, total_files)
            images.append(imported_img)
        show_images(images)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import data: {str(e)}")

def show_images(images):
    for widget in image_frame.winfo_children():
        widget.destroy()

    frame_width = image_frame.winfo_width()
    img_width = frame_width // 2 - 10  # 10 pixels for padding

    for i, img in enumerate(images):
        pil_img = Image.fromarray(img)
        pil_img.thumbnail((img_width, img_width))  # Resize image to fit half the frame width
        tk_img = ImageTk.PhotoImage(pil_img)
        
        label = tk.Label(image_frame, image=tk_img)
        label.image = tk_img  # Keep a reference
        label.grid(row=i//2, column=i%2, padx=5, pady=5)

root = tk.Tk()
root.title("Import and Draw Images")

import_button = tk.Button(root, text="Import Data", command=import_and_draw_images)
import_button.pack(pady=20)

image_frame = tk.Frame(root)
image_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

root.mainloop()