# -- coding: UTF-8 --
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt
from utils.launch_loading import show_loading_screen

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
    
    img = np.zeros((max(max_y - min_y + 1, 1), max(max_x - min_x + 1, 1)), dtype=np.uint8)

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
        # messagebox.showinfo("No Files Selected", "Please select at least one file to import.")
        return

    try:
        images = []
        total_files = len(filenames)
        for i, filename in enumerate(filenames, 1):
            if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
                messagebox.showerror("Invalid File Format", f"The file '{os.path.basename(filename)}' is not a supported format. Please select CSV or Excel files only.")
                return
            imported_img = show_progress_bar(f"Importing Data", import_task, filename, i, total_files)
            images.append((imported_img, os.path.basename(filename)))
        show_images(images)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import data: {str(e)}")

def show_images(images):
    for widget in image_frame.winfo_children():
        widget.destroy()

    if not images:
        # Display a message when no data is uploaded
        message_label = tk.Label(image_frame, text="Please upload data to display images", font=("Arial", 16))
        message_label.pack(expand=True)
        return

    frame_width = max(image_frame.winfo_width(), 1)
    frame_height = max(image_frame.winfo_height(), 1)
    
    num_images = len(images)
    num_cols = min(3, num_images)  # Maximum 3 columns
    num_rows = (num_images + num_cols - 1) // num_cols

    max_img_width = max(frame_width // num_cols - 20, 1)  # 20 pixels for padding
    max_img_height = max(frame_height // num_rows - 40, 1)  # 40 pixels for padding and filename

    for i, (img, filename) in enumerate(images):
        pil_img = Image.fromarray(img)
        original_pil_img = pil_img.copy()  # Store the original image
        
        # Calculate the scaling factor to fit within the available space while maintaining aspect ratio
        width_ratio = max_img_width / pil_img.width
        height_ratio = max_img_height / pil_img.height
        scale_factor = min(width_ratio, height_ratio)
        
        new_size = (int(pil_img.width * scale_factor), int(pil_img.height * scale_factor))
        pil_img = pil_img.resize(new_size, Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        frame = tk.Frame(image_frame, borderwidth=1, relief="solid")
        frame.grid(row=i//num_cols, column=i%num_cols, padx=10, pady=10, sticky="nsew")
        
        # Create a container for the image and overlay elements
        container = tk.Frame(frame)
        container.pack(expand=True, fill=tk.BOTH)
        
        # Add the image
        image_label = tk.Label(container, image=tk_img)
        image_label.image = tk_img  # Keep a reference
        image_label.original_image = original_pil_img  # Store the original image
        image_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Add filename at the top center
        filename_label = tk.Label(container, text=filename, bg='white', fg='black')
        filename_label.place(relx=0.5, y=0, anchor='n')
        
        # Add "Show 3D Plot" button to the top right corner
        show_3d_button = tk.Button(container, text="3D", command=lambda img=img: show_3d_plot(img))
        show_3d_button.place(relx=1, y=0, anchor='ne')

    # Configure grid to center the images
    for i in range(num_cols):
        image_frame.grid_columnconfigure(i, weight=1)
    for i in range(num_rows):
        image_frame.grid_rowconfigure(i, weight=1)

def show_3d_plot(img):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    y, x = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    Z = img
    
    surf = ax.plot_surface(x, y, Z, cmap='gray')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Intensity')
    ax.set_title('3D Surface Plot of Fingerprint')
    
    # Set the origin to bottom-left
    ax.set_xlim(0, img.shape[1])
    ax.set_ylim(0, img.shape[0])
    
    # Invert y-axis to match image coordinates
    ax.invert_yaxis()
    
    fig.colorbar(surf, shrink=0.5, aspect=5)
    
    plt.show()

root = tk.Tk()
root.withdraw()  # Hide the main window initially

show_loading_screen()  # Show loading screen

root.deiconify()  # Show the main window after loading screen

root.title("Images")

import_button = tk.Button(root, text="Import Data", command=import_and_draw_images)
import_button.pack(pady=20)

image_frame = tk.Frame(root)
image_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Display initial message
initial_message = tk.Label(image_frame, text="Please upload data to display images", font=("Arial", 16))
initial_message.pack(expand=True)

# Bind the root window's <Configure> event to update images
def update_root_images(event=None):
    # Only update if the image_frame has been created and has children
    if 'image_frame' in globals() and image_frame.winfo_children():
        frame_width = max(image_frame.winfo_width(), 1)
        frame_height = max(image_frame.winfo_height(), 1)
        
        num_images = len([child for child in image_frame.winfo_children() if isinstance(child, tk.Frame)])
        if num_images == 0:
            return  # No images to update

        num_cols = min(3, num_images)  # Maximum 3 columns
        num_rows = (num_images + num_cols - 1) // num_cols

        max_img_width = max(frame_width // num_cols - 20, 1)  # 20 pixels for padding
        max_img_height = max(frame_height // num_rows - 20, 1)  # 20 pixels for padding

        for frame in image_frame.winfo_children():
            if isinstance(frame, tk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Label) and hasattr(child, 'original_image'):
                                pil_img = child.original_image.copy()
                                # Calculate the scaling factor to fit within the available space while maintaining aspect ratio
                                width_ratio = max_img_width / pil_img.width
                                height_ratio = max_img_height / pil_img.height
                                scale_factor = min(width_ratio, height_ratio)
                                
                                new_size = (int(pil_img.width * scale_factor), int(pil_img.height * scale_factor))
                                pil_img = pil_img.resize(new_size, Image.LANCZOS)
                                tk_img = ImageTk.PhotoImage(pil_img)
                                child.configure(image=tk_img)
                                child.image = tk_img  # Keep a reference

root.bind("<Configure>", update_root_images)

# root 宽高设置
root.minsize(600, 400)  # 设置最小宽度为600像素，最小高度为400像素
# 居中
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 800
window_height = 600
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.mainloop()