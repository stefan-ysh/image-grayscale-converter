# -- coding: UTF-8 --
import threading
import cv2
import tkinter as tk
from tkinter import filedialog, Menu, Scale, Entry, ttk
from tkinter import font as tkfont
import matplotlib.pyplot as plt
from openpyxl.chart import LineChart, Reference
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import numpy as np
import time

# show progress bar
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

def get_image_processor():
    from image_processor import ImageProcessor
    return ImageProcessor(img, plt, show_progress_bar)

# show loading screen when the program is launching
def show_loading_screen():
    loading_window = tk.Toplevel()
    loading_window.title("")
    loading_window.geometry("300x100")
    loading_window.resizable(False, False)
    # Disable window minimization
    loading_window.attributes("-toolwindow", 1)

    # Disable window closing
    loading_window.protocol("WM_DELETE_WINDOW", lambda: None)

    # Remove the close button
    loading_window.overrideredirect(True)

    # Center the loading window on the screen
    screen_width = loading_window.winfo_screenwidth()
    screen_height = loading_window.winfo_screenheight()
    x = (screen_width - 300) // 2
    y = (screen_height - 100) // 2
    loading_window.geometry(f"300x100+{x}+{y}")
    loading_label = tk.Label(loading_window, text="launching...", font=("Arial", 16))
    loading_label.pack(pady=20)

    progress_bar = tk.Canvas(loading_window, width=200, height=20)
    progress_bar.pack()

    # 使用更多的步骤来实现更平滑的动画
    steps = 200
    for i in range(steps):
        progress_bar.delete("all")  # 清除之前的进度
        width = (i + 1) * 200 / steps
        progress_bar.create_rectangle(0, 0, width, 20, fill="blue", outline="")
        loading_window.update()
        time.sleep(0.01)  # 减少每步的延迟，使动画更流畅

    loading_window.destroy()


root = tk.Tk()
root.withdraw()  # Hide the main window initially

show_loading_screen()  # Show loading screen

root.deiconify()  # Show the main window after loading
root.title("GrayScale Analyzer")
# todo set the window icon
# root.iconbitmap("logo.ico")
pixel_data_with_coordinates = []
rectangles = []
lines = []

mouse_coordinates = []
img = None
gray_img = None

line_color = "#0000ff"  # 蓝色
line_width = 1
mouse_pressed = False

rect_start = None
rect_end = None
rect_thickness = 2

line_start = None

# set the initial mode
mode = "rectangle"

# set the initial max points
MAX_POINTS = 1000

dragging = False
drag_start = None
resizing = None
min_rect_size = 20
circle_radius = 5
highlight_color = (0, 255, 0)
MIN_RECT_WIDTH = 20
MIN_RECT_HEIGHT = 20
# Define a standard button font
button_font = tkfont.Font(size=15)

# convert hex color to bgr
def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (4, 2, 0))  # BGR 顺序

# mouse event
def mouse_callback(event, x, y, flags, param):
    global rect_start, rect_end, mouse_pressed, mouse_coordinates, rectangles, line_start, lines
    global dragging, drag_start, resizing

    if mode == "mouse_hover":
        print("do nothing")
    elif mode == "rectangle":
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, (start, end, name, max_points) in enumerate(rectangles):
                if is_point_in_rect(x, y, start, end):
                    dragging = True
                    drag_start = (x, y)
                    return
                elif is_point_near_corner(x, y, start, end):
                    resizing = get_resize_direction(x, y, start, end)
                    drag_start = (x, y)
                    return
            rect_start = (x, y)
            rect_end = None
        elif event == cv2.EVENT_MOUSEMOVE:
            if dragging:
                dx = x - drag_start[0]
                dy = y - drag_start[1]
                for i, (start, end, name, max_points) in enumerate(rectangles):
                    if is_point_in_rect(drag_start[0], drag_start[1], start, end):
                        new_start = (
                            max(
                                0,
                                min(
                                    start[0] + dx,
                                    gray_img.shape[1] - (end[0] - start[0]),
                                ),
                            ),
                            max(
                                0,
                                min(
                                    start[1] + dy,
                                    gray_img.shape[0] - (end[1] - start[1]),
                                ),
                            ),
                        )
                        new_end = (
                            new_start[0] + (end[0] - start[0]),
                            new_start[1] + (end[1] - start[1]),
                        )
                        rectangles[i] = (new_start, new_end, name, max_points)
                        break
                drag_start = (x, y)
                update_display_image()
            elif resizing is not None:
                for i, (start, end, name, max_points) in enumerate(rectangles):
                    if is_point_near_corner(drag_start[0], drag_start[1], start, end):
                        new_start, new_end = resize_rectangle(
                            start, end, x, y, resizing
                        )
                        # 确保新的矩形尺寸不小于最小值
                        width = abs(new_end[0] - new_start[0])
                        height = abs(new_end[1] - new_start[1])
                        if width >= MIN_RECT_WIDTH and height >= MIN_RECT_HEIGHT:
                            rectangles[i] = (new_start, new_end, name, max_points)
                        break
                drag_start = (x, y)
                update_display_image()
            elif rect_start:
                rect_end = (x, y)
                update_display_image()
            else:
                # 检查鼠标是否悬停在任何矩形的角上
                for start, end, _, _ in rectangles:
                    if is_point_near_corner(x, y, start, end):
                        update_display_image(highlight_corner=(x, y))
                        return
                update_display_image()
        elif event == cv2.EVENT_LBUTTONUP:
            if dragging or resizing:
                dragging = False
                resizing = None
                update_plot()  # 在鼠标抬起时更新plot
            elif rect_start and rect_end:
                if rect_start != rect_end:
                    # 确保矩形宽高不小于最小值
                    width = abs(rect_end[0] - rect_start[0])
                    height = abs(rect_end[1] - rect_start[1])
                    if width >= MIN_RECT_WIDTH and height >= MIN_RECT_HEIGHT:
                        rectangle_name = f"Chart {len(rectangles) + 1}"
                        rectangles.append(
                            (
                                rect_start,
                                rect_end,
                                rectangle_name,
                                MAX_POINTS,
                            )
                        )
                        update_display_image()
                        update_plot()
                    else:
                        messagebox.showwarning(
                            "Warning",
                            f"Rectangle size too small. Minimum size is {MIN_RECT_WIDTH}x{MIN_RECT_HEIGHT} pixels.",
                        )
                rect_start = None
                rect_end = None
        elif event == cv2.EVENT_RBUTTONDOWN:
            for i, (start, end, name, max_points) in enumerate(rectangles):
                if is_point_in_rect(x, y, start, end):
                    show_context_menu(x, y, i)
                    return


# show the context menu of the rectangle
def show_context_menu(x, y, rect_index):
    context_menu = Menu(root, tearoff=0)
    context_menu.add_command(
        label="Delete", command=lambda: delete_rectangle(rect_index)
    )
    context_menu.add_command(
        label="Change Points", command=lambda: edit_rectangle_points(rect_index)
    )
    context_menu.post(root.winfo_pointerx(), root.winfo_pointery())


def delete_rectangle(rect_index):
    rectangles.pop(rect_index)
    update_display_image()
    update_plot()


def edit_rectangle_points(rect_index):
    start, end, name, max_points = rectangles[rect_index]

    # 创建一个新的顶层窗口
    top = tk.Toplevel(root)
    top.title(f"Edit Points for {name}")

    # 创建并放置滑动条
    slider = Scale(
        top,
        from_=10,
        to=100000,
        orient="horizontal",
        length=300,
        label="Number of Points",
    )
    slider.set(max_points)
    slider.pack(pady=20)

    # 创建输入框
    entry = Entry(top)
    entry.insert(0, str(max_points))
    entry.pack(pady=10)

    # 更新函数
    def update_value(val):
        entry.delete(0, tk.END)
        entry.insert(0, val)

    slider.config(command=update_value)

    # 确认按钮
    def on_confirm():
        try:
            new_max_points = int(entry.get())
            if 10 <= new_max_points <= 100000:
                rectangles[rect_index] = (start, end, name, new_max_points)
                update_plot()
                top.destroy()
            else:
                messagebox.showerror(
                    "Error", "Please enter a value between 10 and 100000."
                )
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer.")

    confirm_button = tk.Button(top, text="Confirm", command=on_confirm)
    confirm_button.pack(pady=10)


def is_point_in_rect(x, y, start, end):
    return start[0] <= x <= end[0] and start[1] <= y <= end[1]


def is_point_near_corner(x, y, start, end, threshold=10):
    corners = [start, (start[0], end[1]), end, (end[0], start[1])]
    return any(
        abs(x - cx) < threshold and abs(y - cy) < threshold for cx, cy in corners
    )


def get_resize_direction(x, y, start, end, threshold=10):
    corners = {
        "top_left": (start[0], start[1]),
        "top_right": (end[0], start[1]),
        "bottom_left": (start[0], end[1]),
        "bottom_right": (end[0], end[1]),
    }

    for direction, (cx, cy) in corners.items():
        if abs(x - cx) < threshold and abs(y - cy) < threshold:
            return direction

    return None


def resize_rectangle(start, end, x, y, direction):
    new_start, new_end = start, end
    if direction == "top_left":
        new_start = (
            max(0, min(x, end[0] - MIN_RECT_WIDTH)),
            max(0, min(y, end[1] - MIN_RECT_HEIGHT)),
        )
    elif direction == "top_right":
        new_start = (start[0], max(0, min(y, end[1] - MIN_RECT_HEIGHT)))
        new_end = (
            max(start[0] + MIN_RECT_WIDTH, min(x, gray_img.shape[1] - 1)),
            end[1],
        )
    elif direction == "bottom_left":
        new_start = (max(0, min(x, end[0] - MIN_RECT_WIDTH)), start[1])
        new_end = (
            end[0],
            max(start[1] + MIN_RECT_HEIGHT, min(y, gray_img.shape[0] - 1)),
        )
    elif direction == "bottom_right":
        new_end = (
            max(start[0] + MIN_RECT_WIDTH, min(x, gray_img.shape[1] - 1)),
            max(start[1] + MIN_RECT_HEIGHT, min(y, gray_img.shape[0] - 1)),
        )

    return new_start, new_end


def update_display_image(highlight_corner=None):
    if img is None or gray_img is None:
        return

    display_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

    if mode == "rectangle":
        for start, end, name, _ in rectangles:
            bgr_color = hex_to_bgr(line_color)
            cv2.rectangle(display_img, start, end, bgr_color, rect_thickness)
            text_position = (start[0], start[1] - 10)
            cv2.putText(
                display_img,
                name,
                text_position,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                bgr_color,
                1,
                cv2.LINE_AA,
            )

            # 在四个角上绘制小圆圈
            corners = [start, (start[0], end[1]), end, (end[0], start[1])]
            for corner in corners:
                if highlight_corner and is_point_near_corner(
                    highlight_corner[0], highlight_corner[1], corner, corner
                ):
                    cv2.circle(display_img, corner, circle_radius, highlight_color, -1)
                else:
                    cv2.circle(display_img, corner, circle_radius, bgr_color, -1)

        if rect_start and rect_end:
            cv2.rectangle(
                display_img,
                rect_start,
                rect_end,
                hex_to_bgr(line_color),
                rect_thickness,
            )

    cv2.imshow("Gray Image", display_img)


def update_plot():
    plt.clf()
    if not rectangles:
        # 当没有图表时，显示提示信息
        plt.text(
            0.5,
            0.5,
            "Please select an image \n to generate a grayscale chart",
            ha="center",
            va="center",
            fontsize=20,
        )
        plt.axis("off")
    else:
        num_plots = len(rectangles)
        cols = 2
        rows = (num_plots + 1) // cols

        for idx, (start, end, name, max_points) in enumerate(rectangles):
            x1, y1 = start
            x2, y2 = end
            x1, x2 = sorted(
                [max(0, min(x1, gray_img.shape[1])), max(0, min(x2, gray_img.shape[1]))]
            )
            y1, y2 = sorted(
                [max(0, min(y1, gray_img.shape[0])), max(0, min(y2, gray_img.shape[0]))]
            )

            rect_pixels = gray_img[y1:y2, x1:x2].flatten()

            if len(rect_pixels) > max_points:
                indices = np.linspace(0, len(rect_pixels) - 1, max_points, dtype=int)
                rect_pixels = rect_pixels[indices]
            elif len(rect_pixels) < max_points:
                # 如果像素数量不足，使用真是像素数量
                max_points = len(rect_pixels)
                # 同步更新 rectangles 中的 max_points
                rectangles[idx] = (start, end, name, max_points)

            rect_data = [
                (i + 1, gray_value) for i, gray_value in enumerate(rect_pixels)
            ]

            row = idx // cols
            col = idx % cols

            if row == rows - 1 and num_plots % 2 != 0:
                ax = plt.subplot(rows, 1, row + 1)
            else:
                ax = plt.subplot(rows, cols, idx + 1)

            x_data = [i for i, _ in rect_data]
            y_data = [gray_value for _, gray_value in rect_data]
            ax.plot(x_data, y_data, marker="", linewidth=line_width, color=line_color)
            ax.set_title(f"{name} (Points: {max_points})")
            ax.set_xlabel("Pixel Index")
            ax.set_ylabel("Gray Value")

    plt.tight_layout()
    canvas.draw()


def set_max_points():
    global MAX_POINTS

    # 创建一个新的顶层窗口
    top = tk.Toplevel(root, padx=100)
    top.title("")

    # 不显示最小化和最大化按钮
    top.attributes("-toolwindow", 1)
    top.resizable(False, False)

    # 最上层且禁止与其他窗口交互
    top.attributes("-topmost", True)
    top.grab_set()

    top.overrideredirect(True)

    # 创建并放置滑动条
    slider = Scale(
        top, from_=10, to=100000, orient="horizontal", length=400, label="Max Points", font=200
    )
    slider.set(MAX_POINTS)
    slider.pack(pady=20)

    # 创建输入框
    entry = Entry(top, font=300)
    entry.insert(0, str(MAX_POINTS))
    entry.pack(pady=10)

    # 更新函数
    def update_value(val):
        entry.delete(0, tk.END)
        entry.insert(0, val)

    def update_slider(event):
        try:
            value = int(entry.get())
            if 10 <= value <= 100000:
                slider.set(value)
        except ValueError:
            pass

    slider.config(command=update_value)
    entry.bind('<KeyRelease>', update_slider)

    # 说明文本
    explanation = tk.Label(
        top,
        text="1. 较小的值会减少数据量，加快处理速度，但可能丢失细节。\n"
        "2. 较大的值会保留更多细节，但可能会降低性能，处理时间较慢。\n"
        "3. 对于高分辨率图像或大区域，可能需要更大的值。\n"
        "4. 更改后将应用于新生成的图表，不会影响已生成的图表。",
        justify=tk.LEFT,
        font=300,
    )
    explanation.pack(pady=10)

    # 确认函数
    def on_confirm():
        global MAX_POINTS
        try:
            value = int(entry.get())
            if 10 <= value <= 100000:
                MAX_POINTS = value
                set_max_points_num_button.config(text=f"Set Max Points ({MAX_POINTS})")
                top.destroy()
            else:
                messagebox.showerror("Error", "Please enter a value between 10 and 100000.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer.")

    # Create a frame to hold the buttons
    button_frame = tk.Frame(top)
    button_frame.pack(pady=10)
    # Cancel button
    cancel_button = tk.Button(button_frame, text="Cancel", command=top.destroy, font=300)
    cancel_button.pack(side=tk.LEFT, padx=5)
    # Confirm button
    confirm_button = tk.Button(button_frame, text="Confirm", command=on_confirm, font=300)
    confirm_button.pack(side=tk.LEFT, padx=5)

    # 绑定回车键到确认函数
    entry.bind('<Return>', lambda event: on_confirm())

    # 设置焦点到输入框
    entry.focus_set()
    # 更新窗口大小并居中显示
    top.update_idletasks()
    width = top.winfo_width()
    height = top.winfo_height()
    x = (root.winfo_width() - width) // 2 + root.winfo_x()
    y = (root.winfo_height() - height) // 2 + root.winfo_y()
    top.geometry(f'+{x}+{y}')

def select_image():
    global img, gray_img, pixel_data_with_coordinates, mouse_coordinates, rectangles, lines, rect_start, rect_end, line_start, image_processor
    filename = filedialog.askopenfilename(
        title="Select image file",
        filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")),
    )
    if not filename:
        return
    img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    if img is None:
        messagebox.showerror("Error", "Could not open or find the image.")
        return
    gray_img = img.copy()
    cv2.imshow("Gray Image", gray_img)
    pixel_data_with_coordinates = []
    mouse_coordinates = []
    rectangles = []
    lines = []
    rect_start = None
    rect_end = None
    line_start = None

    save_chart_button.config(state=tk.NORMAL)
    export_button.config(state=tk.NORMAL)
    save_gray_image_button.config(state=tk.NORMAL)
    update_plot()

    cv2.namedWindow("Gray Image", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Gray Image", mouse_callback)

    # 在这里初始化 ImageProcessor
    image_processor = get_image_processor()

def export_data_to_excel():
    if img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        title="Save Data as Excel File",
        initialfile=f"pixel_data_{current_time}.xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
    )

    if not filename:
        return

    def export_task():
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            for idx, (start, end, name, max_points) in enumerate(rectangles):
                x1, y1 = start
                x2, y2 = end
                x1, x2 = sorted(
                    [max(0, min(x1, gray_img.shape[1])), max(0, min(x2, gray_img.shape[1]))]
                )
                y1, y2 = sorted(
                    [max(0, min(y1, gray_img.shape[0])), max(0, min(y2, gray_img.shape[0]))]
                )
                rect_pixels = gray_img[y1:y2, x1:x2].flatten()

                total_points = len(rect_pixels)
                if total_points > max_points:
                    indices = np.linspace(0, total_points - 1, max_points, dtype=int)
                    rect_pixels = rect_pixels[indices]
                else:
                    indices = np.arange(total_points)
                    max_points = total_points  # 更新max_points为实际点数

                data = []
                for i, (index, gray_value) in enumerate(zip(indices, rect_pixels)):
                    x_coord = x1 + (index % (x2 - x1))
                    y_coord = gray_img.shape[0] - (y1 + (index // (x2 - x1))) - 1
                    data.append([i + 1, gray_value, x_coord, y_coord])

                df = pd.DataFrame(data, columns=["Index", "Gray", "X", "Y"])
                sheet_name = f"Chart_{idx + 1}"

                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # 在这里创建和添加图表
                worksheet = writer.sheets[sheet_name]

                chart = LineChart()
                chart.title = f"Gray Value vs Index - {name}"
                chart.style = 13
                chart.x_axis.title = "Index"
                chart.y_axis.title = "Gray Value"

                data = Reference(worksheet, min_col=2, min_row=1, max_col=2, max_row=len(df) + 1)
                categories = Reference(worksheet, min_col=1, min_row=2, max_row=len(df) + 1)

                chart.add_data(data, titles_from_data=True)
                chart.set_categories(categories)

                # 设置x轴的最大值为实际的点数
                chart.x_axis.scaling.max = max_points

                worksheet.add_chart(chart, "F2")

        return True

    result = show_progress_bar("Exporting Data", export_task)
    
    if result:
        messagebox.showinfo("Success", "Data exported and charts added successfully!")
    else:
        messagebox.showerror("Error", "Failed to export data.")

# 主窗口按钮设置
select_button = tk.Button(root, padx=10, text="Select Image", command=select_image, font=button_font)
set_max_points_num_button = tk.Button(root, padx=10, text=f"Set Max Points ({MAX_POINTS})", command=set_max_points, font=button_font)
save_chart_button = tk.Button(root, padx=10, text="Save Chart Image", command=lambda: image_processor.save_plot_image() if image_processor else None, font=button_font)
export_button = tk.Button(root, padx=10, text="Export Data to Excel", command=export_data_to_excel, font=button_font)
save_gray_image_button = tk.Button(root, padx=10, text="Save Gray Image", command=lambda: image_processor.save_gray_img(cv2, gray_img, rectangles, show_progress_bar), font=button_font)

select_button.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
set_max_points_num_button.grid(row=0, column=1, sticky="ew", padx=20, pady=20)
save_chart_button.grid(row=0, column=2, sticky="ew", padx=20, pady=20)
save_gray_image_button.grid(row=0, column=4, sticky="ew", padx=20, pady=20)
export_button.grid(row=0, column=3, sticky="ew", padx=20, pady=20)


def create_plot_canvas():
    fig, ax = plt.subplots(figsize=(8, 6))  # Set initial size of figure
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=1, column=0, columnspan=5, sticky="nsew")
    return canvas


save_chart_button.config(state="disabled")
export_button.config(state="disabled")
save_gray_image_button.config(state="disabled")

# 关闭窗口
def on_closing_root_win():
    if messagebox.askokcancel("Quit", "Are you sure to quit?"):
        # 关闭gray_img窗口
        cv2.destroyAllWindows()
        # 关闭root窗口
        root.destroy()
        
canvas = create_plot_canvas()
update_plot()
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
root.grid_columnconfigure(4, weight=1)

# 监听关闭主窗口的事件
root.protocol("WM_DELETE_WINDOW", on_closing_root_win)
root.mainloop()
cv2.destroyAllWindows()
