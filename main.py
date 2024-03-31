import cv2
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import colorchooser
from tkinter import messagebox
from image_processor import ImageProcessor

# 创建一个简单的GUI窗口
root = tk.Tk()
root.title("Image Uploader")

# 初始化记录鼠标滑过的像素点坐标和灰度值的列表
pixel_data_with_coordinates = []

# 初始化图像
img = None

# 初始化灰度图像
gray_img = {}

# 设置折线图的颜色和宽度
line_color = 'lightblue'
line_width = 2


# 鼠标回调函数
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # 获取当前鼠标位置的灰度值
        gray_value = gray_img[y, x]
        print(f"Gray value at position ({x}, {y}): {gray_value}")

        # 记录像素点的坐标和灰度值
        pixel_data_with_coordinates.append((x, y, gray_value))
        # 更新折线图
        update_plot()


# 选择图片文件
def select_image():
    global img, gray_img, pixel_data_with_coordinates
    filename = filedialog.askopenfilename(
        title="Select image file",
        filetypes=(("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*"))
    )
    if not filename:
        return
    img = cv2.imread(filename)
    if img is None:
        messagebox.showerror("Error", "Could not open or find the image.")
        return
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Gray Image", gray_img)
    # 清空数据
    pixel_data_with_coordinates = []

    # 上传图片之后，保存图片、导出数据按钮启用
    save_button.config(state=tk.NORMAL)
    export_button.config(state=tk.NORMAL)

    update_plot()
    # 创建一个用于显示图像的窗口
    cv2.namedWindow("Gray Image", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Gray Image", mouse_callback)


# 更新折线图
def update_plot():
    # 清除之前的图形
    plt.clf()
    # 绘制折线图
    plt.plot(
        [i + 1 for i, d in enumerate(pixel_data_with_coordinates)],
        [d[2] for d in pixel_data_with_coordinates],
        marker='',
        color=line_color,
        linewidth=line_width
    )
    plt.title("Pixel Gray Values Over Time")
    plt.xlabel("Pixel Index")
    plt.ylabel("Gray Value")
    # 刷新图形
    canvas.draw()


# 创建选择图片的按钮和折线图canvas
select_button = tk.Button(root, text="Select Image", command=select_image)
select_button.grid(row=0, column=0, sticky="ew")


def show_color_chooser():
    color = colorchooser.askcolor(title="Select a color")
    # print(f"Selected color: {color}")

    global line_color
    line_color = color[1]
    # 按钮文字更新
    choose_color_button.config(text=f"{line_color}")

    update_plot()


# 创建一个按钮，点击后会打开颜色选择器
choose_color_button = tk.Button(root, text=f"{line_color}", command=show_color_chooser)
# 位置在select_button的右侧
choose_color_button.grid(row=0, column=1, sticky="ew")

# 保存折线图的函数
image_processor = ImageProcessor(img, plt)

# 创建保存图片的按钮，并放置到GUI窗口中
save_button = tk.Button(root, text="Save Plot Image", command=lambda: image_processor.save_plot_image(img, plt))

save_button.grid(row=0, column=2, sticky="ew")


# 导出数据到Excel的函数
def export_data_to_excel():
    # 如果没有选择图片，则不允许导出
    if img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return
    # 将记录的像素数据转换为DataFrame
    df = pd.DataFrame(pixel_data_with_coordinates, columns=['X', 'Y', 'Gray'])
    # 获取当前时间并格式化为字符串
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # 弹出保存文件对话框，并使用当前时间作为默认文件名
    filename = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        title="Save Data as Excel File",
        initialfile=f"pixel_data_{current_time}.xlsx",
        filetypes=[("Excel files", "*.xlsx"),
                   ("All files", "*.*")]
    )
    if filename:
        # 保存数据到指定路径的Excel文件
        df.to_excel(filename, index=False)
        # print(f"Data exported to {filename}")
        messagebox.showinfo("Success", "Data exported successfully!")


# 创建导出数据的按钮，并放置到GUI窗口中
export_button = tk.Button(root, text="Export Data to Excel", command=export_data_to_excel)
export_button.grid(row=0, column=3, sticky="ew")


# 创建用于显示折线图的Tkinter canvas
def create_plot_canvas():
    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=root)
    # 设置列跨越所有4列，并设置sticky为"nsew"以便在所有方向上扩展
    canvas.get_tk_widget().grid(row=1, column=0, columnspan=4, sticky="nsew")
    return canvas


# 初始化时保存按钮和导出按钮禁用
save_button.config(state="disabled")
export_button.config(state="disabled")

# 创建用于显示折线图的Tkinter canvas
canvas = create_plot_canvas()
update_plot()
# 设置行和列的权重，使按钮随着窗口大小的改变而改变
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
# 运行GUI事件循环
root.mainloop()

# 销毁所有窗口
cv2.destroyAllWindows()
