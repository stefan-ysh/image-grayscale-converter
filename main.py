# -- coding: UTF-8 --
import cv2
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, Menu, Scale, Entry
from tkinter import font as tkfont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import numpy as np
from utils.launch_loading import show_loading_screen
from utils.show_progress_bar import show_progress_bar
from utils.color_handle import hex_to_bgr
from utils.excel_exporter import ExcelExporter

def get_image_processor():
    from utils.image_processor import ImageProcessor

    return ImageProcessor(img, plt, show_progress_bar)


# show loading screen when the program is launching

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
                                0 if MAX_POINTS == 0 else MAX_POINTS,
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

    # 计算实际点数
    x1, y1 = start
    x2, y2 = end
    x1, x2 = sorted(
        [max(0, min(x1, gray_img.shape[1])), max(0, min(x2, gray_img.shape[1]))]
    )
    y1, y2 = sorted(
        [max(0, min(y1, gray_img.shape[0])), max(0, min(y2, gray_img.shape[0]))]
    )
    actual_points = (x2 - x1) * (y2 - y1)

    # 创建并放置滑动条
    slider = Scale(
        top,
        from_=10,
        to=max(100000, actual_points),
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

    # 创建复选框
    use_actual_points = tk.BooleanVar()
    use_actual_points_checkbox = tk.Checkbutton(
        top, text="Use actual points", variable=use_actual_points
    )
    use_actual_points_checkbox.pack(pady=10)

    # 更新函数
    def update_value(val):
        if not use_actual_points.get():
            entry.delete(0, tk.END)
            entry.insert(0, val)

    slider.config(command=update_value)

    # 确认按钮
    def on_confirm():
        try:
            if use_actual_points.get():
                new_max_points = actual_points
            else:
                new_max_points = int(entry.get())

            if 10 <= new_max_points <= max(100000, actual_points):
                rectangles[rect_index] = (start, end, name, new_max_points)
                update_plot()
                top.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    f"Please enter a value between 10 and {max(100000, actual_points)}.",
                )
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer.")

    confirm_button = tk.Button(top, text="Confirm", command=on_confirm)
    confirm_button.pack(pady=10)

    # 更新复选框状态时的回调函数
    def update_checkbox_state():
        if use_actual_points.get():
            slider.set(actual_points)
            entry.delete(0, tk.END)
            entry.insert(0, str(actual_points))
            slider.config(state=tk.DISABLED)
            entry.config(state=tk.DISABLED)
        else:
            slider.config(state=tk.NORMAL)
            entry.config(state=tk.NORMAL)

    use_actual_points_checkbox.config(command=update_checkbox_state)


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

            if max_points == 0 or len(rect_pixels) <= max_points:
                max_points = len(rect_pixels)
            else:
                indices = np.linspace(0, len(rect_pixels) - 1, max_points, dtype=int)
                rect_pixels = rect_pixels[indices]

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
            ax.set_ylabel("Grayscale Value")

    plt.tight_layout()
    canvas.draw()

def set_line_width():
    global line_width

    def update_width(value):
        global line_width
        line_width = float(value)
        width_label.config(text=f"Line Width: {line_width:.2f}")

    top = tk.Toplevel(root)
    top.title("Line Width")
    top.geometry("300x150")

    width_label = ttk.Label(top, text=f"Line Width: {line_width:.2f}")
    width_label.pack(pady=10)

    width_scale = ttk.Scale(top, from_=0.1, to=10, orient="horizontal", length=200, command=update_width)
    width_scale.set(line_width)
    width_scale.pack(pady=10)

    ttk.Button(top, text="Apply", command=lambda: [update_plot(), top.destroy()]).pack(pady=10)


def set_max_points():
    global MAX_POINTS

    def update_max_points(value):
        global MAX_POINTS
        MAX_POINTS = int(float(value))
        points_label.config(text=f"Max Points: {MAX_POINTS}")

    top = tk.Toplevel(root)
    top.title("Max Points")
    top.geometry("300x200")

    points_label = ttk.Label(top, text=f"Max Points: {MAX_POINTS}")
    points_label.pack(pady=10)

    points_scale = ttk.Scale(top, from_=10, to=100000, orient="horizontal", length=200, command=update_max_points)
    points_scale.set(MAX_POINTS)
    points_scale.pack(pady=10)

    use_actual_points = tk.BooleanVar()
    use_actual_points_checkbox = ttk.Checkbutton(
        top, text="Use actual points", variable=use_actual_points,
        command=lambda: [points_scale.set(0), update_max_points('0')] if use_actual_points.get() else None
    )
    use_actual_points_checkbox.pack(pady=10)

    def on_confirm():
        global MAX_POINTS
        if use_actual_points.get():
            MAX_POINTS = 0
        set_max_points_num_button.config(
            text=f"Set Max Points ({'Actual' if MAX_POINTS == 0 else MAX_POINTS})"
        )
        top.destroy()

    # Create a frame to hold the buttons
    button_frame = tk.Frame(top)
    button_frame.pack(pady=10)

    # Cancel button
    cancel_button = ttk.Button(button_frame, text="Cancel", command=top.destroy)
    cancel_button.pack(side=tk.LEFT, padx=5)

    # Confirm button
    confirm_button = ttk.Button(button_frame, text="Confirm", command=on_confirm)
    confirm_button.pack(side=tk.LEFT, padx=5)

    # Bind the Enter key to the confirm function
    top.bind("<Return>", lambda event: on_confirm())

    # Update checkbox state
    def update_checkbox_state():
        if use_actual_points.get():
            points_scale.set(0)
            points_scale.config(state=tk.DISABLED)
        else:
            points_scale.config(state=tk.NORMAL)

    use_actual_points_checkbox.config(command=update_checkbox_state)

    # Set focus to the scale
    points_scale.focus_set()

    # Update window size and center it
    top.update_idletasks()
    width = top.winfo_width()
    height = top.winfo_height()
    x = (root.winfo_width() - width) // 2 + root.winfo_x()
    y = (root.winfo_height() - height) // 2 + root.winfo_y()
    top.geometry(f"+{x}+{y}")


def select_image():
    global img, gray_img, pixel_data_with_coordinates, mouse_coordinates, rectangles, lines, rect_start, rect_end, line_start, image_processor, excel_exporter
    filename = filedialog.askopenfilename(
        title="Select image file",
        filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")),
    )
    if not filename:
        return
    img = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
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
    excel_exporter = ExcelExporter(gray_img)


# 替换原来的 export_data_to_excel 函数
def export_data_to_excel():
    if excel_exporter:
        excel_exporter.export_data_to_excel(rectangles)
    else:
        messagebox.showerror("Error", "Please select an image first.")

def create_button(root, text, command, state=tk.NORMAL):
    return ttk.Button(root, text=text, command=command, style='TButton', state=state)

def create_and_grid_button(root, text, command, state=tk.NORMAL):
    button = create_button(root, text, command, state)
    button.grid(row=0, column=i, sticky="ew", padx=20, pady=20)
    return button

# 创建ttk样式
style = ttk.Style()
style.configure('TButton', font=button_font, padding=10)

# 主窗口按钮设置
buttons = [
    ("Select Image", select_image, tk.NORMAL),
    (f" Max Points ({MAX_POINTS})", set_max_points, tk.NORMAL),
    ("Line Width", set_line_width, tk.NORMAL),
    ("Save Chart Image", lambda: image_processor.save_plot_image() if image_processor else None, tk.DISABLED),
    ("Export Data", export_data_to_excel, tk.DISABLED),
    ("Save Gray Image", lambda: image_processor.save_gray_img(cv2, gray_img, rectangles, show_progress_bar), tk.DISABLED)
]

for i, (text, command, state) in enumerate(buttons):
    button = create_and_grid_button(root, text, command, state)
    if "Chart" in text:
        save_chart_button = button
    elif "Export" in text:
        export_button = button
    elif "Gray Image" in text:
        save_gray_image_button = button
    elif "Max Points" in text:
        set_max_points_num_button = button


def create_plot_canvas():
    fig, ax = plt.subplots(figsize=(8, 6))  # Set initial size of figure
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=1, column=0, columnspan=6, sticky="nsew")
    return canvas


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
root.grid_columnconfigure(5, weight=1) 

# 监听关闭主窗口的事件
root.protocol("WM_DELETE_WINDOW", on_closing_root_win)
root.mainloop()
cv2.destroyAllWindows()
