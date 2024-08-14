import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import colorchooser
from tkinter import messagebox
from image_processor import ImageProcessor
import numpy as np

root = tk.Tk()
root.title("Image Uploader")

pixel_data_with_coordinates = []
rectangles = []
lines = []

mouse_coordinates = []
img = None
gray_img = None

line_colors = ["#FF0000", "#FFFF00"]  # 红色和黄色
line_width = 1
mouse_pressed = False

rect_start = None
rect_end = None
rect_thickness = 2

line_start = None
line_thickness = 1
current_color_index = 0

mode = "rectangle"

MAX_POINTS = 1000  # 设置初始最大点数

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (4, 2, 0))  # BGR 顺序


def mouse_callback(event, x, y, flags, param):
    global rect_start, rect_end, mouse_pressed, mouse_coordinates, rectangles, line_start, lines, current_color_index

    if mode == "mouse_hover":
        print("do nothing")
    elif mode == "rectangle":
        if event == cv2.EVENT_LBUTTONDOWN:
            rect_start = (x, y)
            rect_end = None
        elif event == cv2.EVENT_MOUSEMOVE:
            if rect_start:
                rect_end = (x, y)
                update_display_image()
        elif event == cv2.EVENT_LBUTTONUP:
            rect_end = (x, y)
            if rect_start != rect_end:
                rectangle_name = f"Rectangle {len(rectangles) + 1}"
                rectangles.append(
                    (
                        rect_start,
                        rect_end,
                        line_colors[current_color_index],
                        rectangle_name,
                        MAX_POINTS,  # 添加当前的MAX_POINTS值
                    )
                )
                current_color_index = (current_color_index + 1) % len(line_colors)
                update_display_image()
                update_plot_from_rectangle()
            rect_start = None
            rect_end = None


def update_display_image():
    if img is None or gray_img is None:
        return

    display_img = gray_img.copy()

    if mode == "rectangle":
        for start, end, color, name, _ in rectangles:
            bgr_color = hex_to_bgr(color)
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

    cv2.imshow("Gray Image", display_img)


def update_plot_from_rectangle():
    global pixel_data_with_coordinates

    if not rectangles:
        return

    plt.clf()
    num_plots = len(rectangles)
    cols = 2
    rows = (num_plots + 1) // cols

    for idx, (start, end, color, name, max_points) in enumerate(rectangles):
        x1, y1 = start
        x2, y2 = end
        x1, x2 = sorted(
            [max(0, min(x1, gray_img.shape[1])), max(0, min(x2, gray_img.shape[1]))]
        )
        y1, y2 = sorted(
            [max(0, min(y1, gray_img.shape[0])), max(0, min(y2, gray_img.shape[0]))]
        )

        rect_pixels = gray_img[y1:y2, x1:x2].flatten()

        # 如果像素点数量超过max_points，进行降采样
        if len(rect_pixels) > max_points:
            indices = np.linspace(0, len(rect_pixels) - 1, max_points, dtype=int)
            rect_pixels = rect_pixels[indices]

        rect_data = [(i + 1, gray_value) for i, gray_value in enumerate(rect_pixels)]

        ax = plt.subplot(rows, cols, idx + 1)
        x_data = [i for i, _ in rect_data]
        y_data = [gray_value for _, gray_value in rect_data]
        ax.plot(x_data, y_data, marker="", linewidth=line_width, color=color)
        ax.set_title(f"{name} (Points: {max_points})")
        ax.set_xlabel("Pixel Index")
        ax.set_ylabel("Gray Value")

    plt.tight_layout()
    canvas.draw()


def update_plot():
    plt.clf()
    num_plots = len(lines) + len(rectangles) + (1 if mouse_coordinates else 0)
    cols = 1 if num_plots == 1 else 2  # 如果只有一个折线图，使用单列布局
    rows = num_plots if num_plots > 1 else 1  # 如果只有一个折线图，行数等于1

    if mouse_coordinates:
        x_data = []
        y_data = []
        for i, (x, y) in enumerate(mouse_coordinates):
            if 0 <= x < gray_img.shape[1] and 0 <= y < gray_img.shape[0]:
                gray_value = gray_img[y, x]
                x_data.append(i + 1)
                y_data.append(gray_value)

        # 如果点数超过MAX_POINTS，进行降采样
        if len(x_data) > MAX_POINTS:
            indices = np.linspace(0, len(x_data) - 1, MAX_POINTS, dtype=int)
            x_data = [x_data[i] for i in indices]
            y_data = [y_data[i] for i in indices]

        ax = plt.subplot(rows, cols, 1)
        ax.plot(
            x_data,
            y_data,
            marker="",
            linewidth=line_width,
            label="Mouse Path",
            color="blue",
        )
        ax.set_title(f"Mouse Path (Points: {MAX_POINTS})")
        ax.set_xlabel("Pixel Index")
        ax.set_ylabel("Gray Value")

    for idx, (start, end, color, name) in enumerate(lines):
        x_data = []
        y_data = []
        if start and end:
            x1, y1 = start
            x2, y2 = end
            num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1
            for i in range(num_points):
                x = int(x1 + (x2 - x1) * i / (num_points - 1))
                y = int(y1 + (y2 - y1) * i / (num_points - 1))
                if 0 <= x < gray_img.shape[1] and 0 <= y < gray_img.shape[0]:
                    gray_value = gray_img[y, x]
                    x_data.append(i + 1)
                    y_data.append(gray_value)

            # 如果点数超过MAX_POINTS，进行降采样
            if len(x_data) > MAX_POINTS:
                indices = np.linspace(0, len(x_data) - 1, MAX_POINTS, dtype=int)
                x_data = [x_data[i] for i in indices]
                y_data = [y_data[i] for i in indices]

            ax = plt.subplot(rows, cols, idx + 2 if mouse_coordinates else idx + 1)
            ax.plot(
                x_data, y_data, marker="", linewidth=line_width, label=name, color=color
            )
            ax.set_title(f"{name} (Points: {MAX_POINTS})")
            ax.set_xlabel("Pixel Index")
            ax.set_ylabel("Gray Value")

    for idx, (start, end, color, name, max_points) in enumerate(rectangles):
        x_data = []
        y_data = []
        if start and end:
            x1, y1 = start
            x2, y2 = end
            x_coords = [x1, x2, x2, x1, x1]
            y_coords = [y1, y1, y2, y2, y1]
            for i in range(len(x_coords) - 1):
                x1, y1 = x_coords[i], y_coords[i]
                x2, y2 = x_coords[i + 1], y_coords[i + 1]
                num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1
                for j in range(num_points):
                    x = int(x1 + (x2 - x1) * j / (num_points - 1))
                    y = int(y1 + (y2 - y1) * j / (num_points - 1))
                    if 0 <= x < gray_img.shape[1] and 0 <= y < gray_img.shape[0]:
                        gray_value = gray_img[y, x]
                        x_data.append(j + 1)
                        y_data.append(gray_value)

            # 如果点数超过max_points，进行降采样
            if len(x_data) > max_points:
                indices = np.linspace(0, len(x_data) - 1, max_points, dtype=int)
                x_data = [x_data[i] for i in indices]
                y_data = [y_data[i] for i in indices]

            ax = plt.subplot(
                rows,
                cols,
                len(lines) + idx + 2 if mouse_coordinates else len(lines) + idx + 1,
            )
            ax.plot(
                x_data, y_data, marker="", linewidth=line_width, label=name, color=color
            )
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
        messagebox.showinfo("设置成功", f"最大点数已设置为 {MAX_POINTS}")
        set_max_points_num_button.config(text=f"Set Max Points ({MAX_POINTS})")


def select_image():
    global img, gray_img, pixel_data_with_coordinates, mouse_coordinates, rectangles, lines, rect_start, rect_end, line_start, current_color_index
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
    current_color_index = 0

    save_button.config(state=tk.NORMAL)
    export_button.config(state=tk.NORMAL)
    update_plot()

    cv2.namedWindow("Gray Image", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Gray Image", mouse_callback)


def export_data_to_excel():
    if img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Ask user to select the location and file name to save the Excel file
    filename = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        title="Save Data as Excel File",
        initialfile=f"pixel_data_{current_time}.xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
    )

    if not filename:
        return  # User canceled the save dialog

    # Create an Excel file with pandas and openpyxl
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Access the XlsxWriter workbook and worksheet objects
        for idx, (start, end, color, name, max_points) in enumerate(rectangles):
            x1, y1 = start
            x2, y2 = end
            x1, x2 = sorted(
                [max(0, min(x1, gray_img.shape[1])), max(0, min(x2, gray_img.shape[1]))]
            )
            y1, y2 = sorted(
                [max(0, min(y1, gray_img.shape[0])), max(0, min(y2, gray_img.shape[0]))]
            )
            rect_pixels = gray_img[y1:y2, x1:x2].flatten()

            # 如果像素点数量超过max_points，进行降采样
            if len(rect_pixels) > max_points:
                indices = np.linspace(0, len(rect_pixels) - 1, max_points, dtype=int)
                rect_pixels = rect_pixels[indices]

            data = []
            for i, gray_value in enumerate(rect_pixels):
                x_coord = x1 + (
                    i % (x2 - x1)
                )  # Calculate x coordinate within the rectangle
                y_coord = y1 + (
                    i // (x2 - x1)
                )  # Calculate y coordinate within the rectangle
                data.append([i + 1, gray_value, x_coord, y_coord])

            df = pd.DataFrame(data, columns=["Index", "Gray", "X", "Y"])
            sheet_name = f"Chart_{idx + 1}"

            # Write the DataFrame to a new sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Load the workbook and add charts
    workbook = load_workbook(filename)
    for idx, sheet_name in enumerate(workbook.sheetnames):
        worksheet = workbook[sheet_name]

        # Create a LineChart object
        chart = LineChart()
        chart.title = f"Gray Value vs Index - {sheet_name}"
        chart.style = 13
        chart.x_axis.title = "Index"
        chart.y_axis.title = "Gray Value"

        # Select the data range
        data = Reference(
            worksheet, min_col=2, min_row=1, max_col=2, max_row=len(df) + 1
        )
        categories = Reference(worksheet, min_col=1, min_row=2, max_row=len(df) + 1)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)

        # Add the chart to the worksheet
        worksheet.add_chart(chart, "F2")

    # Save the workbook
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
