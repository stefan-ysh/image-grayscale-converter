import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, Menu
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from image_processor import ImageProcessor
import numpy as np

root = tk.Tk()
root.title("Image Grayscale Chart Generator")
# 设置窗口图标
root.iconbitmap("logo.ico")
pixel_data_with_coordinates = []
rectangles = []
lines = []

mouse_coordinates = []
img = None
gray_img = None

line_color = "#0000FF"  # 蓝色
line_width = 1
mouse_pressed = False

rect_start = None
rect_end = None
rect_thickness = 1

line_start = None

mode = "rectangle"

MAX_POINTS = 1000  # 设置初始最大点数

# 新增变量
dragging = False
drag_start = None
resizing = None
min_rect_size = 20
circle_radius = 5  # 圆圈半径
highlight_color = (0, 255, 0)  # 高亮颜色（绿色）
MIN_RECT_WIDTH = 20  # 最小矩形宽度
MIN_RECT_HEIGHT = 20  # 最小矩形高度


def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (4, 2, 0))  # BGR 顺序


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
                        new_start = (start[0] + dx, start[1] + dy)
                        new_end = (end[0] + dx, end[1] + dy)
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
                        messagebox.showwarning("Warning", f"Rectangle size too small. Minimum size is {MIN_RECT_WIDTH}x{MIN_RECT_HEIGHT} pixels.")
                rect_start = None
                rect_end = None
        elif event == cv2.EVENT_RBUTTONDOWN:
            for i, (start, end, name, max_points) in enumerate(rectangles):
                if is_point_in_rect(x, y, start, end):
                    show_context_menu(x, y, i)
                    return


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
    new_max_points = simpledialog.askinteger(
        "Edit Points",
        f"Enter new number of points for {name} (current: {max_points}):",
        initialvalue=max_points,
        minvalue=10,
        maxvalue=100000
    )
    if new_max_points:
        rectangles[rect_index] = (start, end, name, new_max_points)
        update_plot()


def is_point_in_rect(x, y, start, end):
    return start[0] <= x <= end[0] and start[1] <= y <= end[1]


def is_point_near_corner(x, y, start, end, threshold=10):
    corners = [start, (start[0], end[1]), end, (end[0], start[1])]
    return any(
        abs(x - cx) < threshold and abs(y - cy) < threshold for cx, cy in corners
    )


def get_resize_direction(x, y, start, end, threshold=10):
    top_left = abs(x - start[0]) < threshold and abs(y - start[1]) < threshold
    top_right = abs(x - end[0]) < threshold and abs(y - start[1]) < threshold
    bottom_left = abs(x - start[0]) < threshold and abs(y - end[1]) < threshold
    bottom_right = abs(x - end[0]) < threshold and abs(y - end[1]) < threshold

    if top_left:
        return "top_left"
    elif top_right:
        return "top_right"
    elif bottom_left:
        return "bottom_left"
    elif bottom_right:
        return "bottom_right"
    else:
        return None


def resize_rectangle(start, end, x, y, direction):
    new_start, new_end = start, end
    if direction == "top_left":
        new_start = (x, y)
    elif direction == "top_right":
        new_start = (start[0], y)
        new_end = (x, end[1])
    elif direction == "bottom_left":
        new_start = (x, start[1])
        new_end = (end[0], y)
    elif direction == "bottom_right":
        new_end = (x, y)
    
    # 确保新的矩形宽高不小于最小值
    width = abs(new_end[0] - new_start[0])
    height = abs(new_end[1] - new_start[1])
    
    if width < MIN_RECT_WIDTH:
        if direction in ["top_left", "bottom_left"]:
            new_start = (new_end[0] - MIN_RECT_WIDTH, new_start[1])
        else:
            new_end = (new_start[0] + MIN_RECT_WIDTH, new_end[1])
    
    if height < MIN_RECT_HEIGHT:
        if direction in ["top_left", "top_right"]:
            new_start = (new_start[0], new_end[1] - MIN_RECT_HEIGHT)
        else:
            new_end = (new_end[0], new_start[1] + MIN_RECT_HEIGHT)
    
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
            "Please select the image and draw a rectangular area \n to generate a grayscale chart.",
            ha="center",
            va="center",
            fontsize=14,
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
    new_max_points = simpledialog.askinteger(
        "设置最大点数",
        "请输入新的最大点数（建议范围：100-10000）：\n\n"
        "说明：\n"
        "1. 较小的值会减少数据量，加快处理速度，但可能丢失细节。\n"
        "2. 较大的值会保留更多细节，但可能会降低性能。\n"
        "3. 对于高分辨率图像或大区域，可能需要更大的值。\n"
        "4. 更改后将应用于新生成的图表。",
        initialvalue=MAX_POINTS,
        minvalue=10,
        maxvalue=100000,
    )
    if new_max_points:
        MAX_POINTS = new_max_points
        set_max_points_num_button.config(text=f"Set Max Points ({MAX_POINTS})")


def select_image():
    global img, gray_img, pixel_data_with_coordinates, mouse_coordinates, rectangles, lines, rect_start, rect_end, line_start
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

    save_button.config(state=tk.NORMAL)
    export_button.config(state=tk.NORMAL)
    save_gray_image_button.config(state=tk.NORMAL)
    update_plot()

    cv2.namedWindow("Gray Image", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Gray Image", mouse_callback)


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

            if len(rect_pixels) > max_points:
                indices = np.linspace(0, len(rect_pixels) - 1, max_points, dtype=int)
                rect_pixels = rect_pixels[indices]

            data = []
            for i, gray_value in enumerate(rect_pixels):
                x_coord = x1 + (i % (x2 - x1))
                y_coord = y1 + (i // (x2 - x1))
                data.append([i + 1, gray_value, x_coord, y_coord])

            df = pd.DataFrame(data, columns=["Index", "Gray", "X", "Y"])
            sheet_name = f"Chart_{idx + 1}"

            df.to_excel(writer, sheet_name=sheet_name, index=False)

    workbook = load_workbook(filename)
    for idx, sheet_name in enumerate(workbook.sheetnames):
        worksheet = workbook[sheet_name]

        chart = LineChart()
        chart.title = f"Gray Value vs Index - {sheet_name}"
        chart.style = 13
        chart.x_axis.title = "Index"
        chart.y_axis.title = "Gray Value"

        data = Reference(
            worksheet, min_col=2, min_row=1, max_col=2, max_row=len(df) + 1
        )
        categories = Reference(worksheet, min_col=1, min_row=2, max_row=len(df) + 1)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)

        worksheet.add_chart(chart, "F2")

    workbook.save(filename)
    messagebox.showinfo("Success", "Data exported and chart added successfully!")


select_button = tk.Button(root, text="Select Image", command=select_image)
select_button.grid(row=0, column=0, sticky="ew")

set_max_points_num_button = tk.Button(
    root, text=f"Set Max Points ({MAX_POINTS})", command=set_max_points
)
set_max_points_num_button.grid(row=0, column=1, sticky="ew")

image_processor = ImageProcessor(img, plt)

save_button = tk.Button(
    root,
    text="Save Plot Image",
    command=lambda: image_processor.save_plot_image(img, plt),
)
save_button.grid(row=0, column=2, sticky="ew")

export_button = tk.Button(
    root, text="Export Data to Excel", command=export_data_to_excel
)


def save_gray_img():
    global gray_img, rectangles
    if gray_img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return

    # Get current time for filename
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Open save file dialog
    filename = filedialog.asksaveasfilename(
        defaultextension=".png",
        title="Save Gray Image",
        initialfile=f"gray_image_{current_time}.png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
    )

    if filename:
        # Create a copy of the gray image to draw on
        img_with_rectangles = gray_img.copy()

        # Draw rectangles and their names on the image
        for idx, rect in enumerate(rectangles):
            cv2.rectangle(img_with_rectangles, rect[0], rect[1], (0, 255, 0), 2)
            # Calculate position for text (above the rectangle)
            text_x = rect[0][0]
            text_y = rect[0][1] - 10  # 10 pixels above the rectangle
            cv2.putText(
                img_with_rectangles,
                f"Chart {idx+1}",
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )

        # Save the image with rectangles and names
        cv2.imwrite(filename, img_with_rectangles)
        messagebox.showinfo(
            "Success", "Gray image with rectangles and names saved successfully!"
        )


save_gray_image_button = tk.Button(root, text="Save Gray Image", command=save_gray_img)


save_gray_image_button.grid(row=0, column=4, sticky="ew")
export_button.grid(row=0, column=3, sticky="ew")


def create_plot_canvas():
    fig, ax = plt.subplots(figsize=(8, 6))  # Set initial size of figure
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=1, column=0, columnspan=5, sticky="nsew")
    return canvas


save_button.config(state="disabled")
export_button.config(state="disabled")

canvas = create_plot_canvas()
update_plot()
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
root.grid_columnconfigure(4, weight=1)

root.mainloop()
cv2.destroyAllWindows()
