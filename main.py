# -- coding: UTF-8 --
import os
import sys
from tkinter import colorchooser
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, Menu, Scale, Entry, simpledialog
from tkinter import font as tkfont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk
from utils.excel_exporter import ExcelExporter
from utils.launch_loading import show_loading_screen
from utils.show_progress_bar import show_progress_bar
from utils.image_utils import ImageHandler
from utils.plot_handler import PlotHandler
from utils.rectangle_handler import RectangleHandler


class GrayScaleAnalyzer:
    def __init__(self):
        self.rect_color = (0, 255, 0)  # BGR 格式，绿色
        self.current_image = None
        self.gray_image_canvas = None
        self.plot_canvas = None
        self.gray_image_on_canvas = None
        self.rectangles = []
        self.img = None
        self.gray_img = None
        self.original_img = None  # 存储原始图像
        self.scaled_img = None    # 存储缩放后的图像
        self.line_color = "#0000ff"
        self.line_width = 0.5
        self.circle_radius = 5
        self.highlight_color = (0, 255, 0)  # 绿色
        self.rect_thickness = 2
        self.mode = "rectangle"
        self.MAX_POINTS = 3000
        self.MIN_RECT_WIDTH = 20
        self.MIN_RECT_HEIGHT = 20
        self.button_font = None
        self.image_processor = None  # Initialize to None
        self.excel_exporter = None

        # Mouse event variables
        self.rect_start = None
        self.rect_end = None
        self.dragging = False
        self.drag_start = None
        self.resizing = None

        self.scale_factor = 1.0
        self.image_start_x = 0
        self.image_start_y = 0
        
        self.last_width = 0
        self.last_height = 0
        self.chart_counter = 1
        
        # 设置matplotlib字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        self.image_handler = ImageHandler()
        self.plot_handler = PlotHandler()
        self.rectangle_handler = RectangleHandler()

    def save_chart_image(self):
        if self.image_processor:
            self.image_processor.save_plot_image()
        else:
            messagebox.showerror("Error", "Please select an image first.")

    def save_gray_image(self):
        if self.gray_img is not None and self.image_processor:
            self.image_processor.save_gray_img(cv2, self.gray_img, self.rectangles, self.rect_color, show_progress_bar)
        else:
            messagebox.showerror("Error", "Please select an image first.")

    def on_canvas_resize(self, event):
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height
            if self.original_img is not None:
                self.update_gray_image()
    def set_rect_color(self):
        color = colorchooser.askcolor(title="Choose Rectangle Color")
        if color[1]:  # color[1] 是十六进制颜色字符串
            # 将十六进制颜色转换为 RGB
            rgb_color = tuple(int(color[1][i:i+2], 16) for i in (1, 3, 5))
            # 将 RGB 转换为 BGR
            self.rect_color = rgb_color[::-1]
            self.update_display_image()
            
    def create_main_window(self):
        self.button_font = tkfont.Font(size=12)

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Create button frame at the top
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Create sub-frames for button categories
        image_frame = ttk.LabelFrame(button_frame, text="Image")
        image_frame.pack(side=tk.LEFT, padx=5, pady=5)

        chart_frame = ttk.LabelFrame(button_frame, text="Chart")
        chart_frame.pack(side=tk.LEFT, padx=5, pady=5)

        export_frame = ttk.LabelFrame(button_frame, text="Export")
        export_frame.pack(side=tk.LEFT, padx=5, pady=5)
        

        # Create buttons
        ttk.Button(image_frame, text="Select Image", command=self.select_image).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(image_frame, text="Rectangle Color", command=self.set_rect_color).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.set_max_points_num_button = ttk.Button(chart_frame, text=f"Max Points ({self.MAX_POINTS})", command=self.set_max_points)
        self.set_max_points_num_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(chart_frame, text="Line Width", command=self.set_line_width).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_chart_button = ttk.Button(export_frame, text="Save Chart Image", command=self.save_chart_image, state=tk.DISABLED)
        self.save_chart_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.export_button = ttk.Button(export_frame, text="Export Data", command=self.export_all_data_to_excel, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_gray_image_button = ttk.Button(export_frame, text="Save Gray Image", command=self.save_gray_image, state=tk.DISABLED)
        self.save_gray_image_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 创建水平分割的布局
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # 左侧：灰度图像
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)

        self.gray_image_canvas = tk.Canvas(left_frame, bg='white')
        self.gray_image_canvas.pack(fill=tk.BOTH, expand=1)

        # 右侧：图表
        plot_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(plot_frame, weight=1)

        fig, ax = plt.subplots(figsize=(8, 6))
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        # Bind mouse events to Canvas
        self.gray_image_canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.gray_image_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.gray_image_canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.gray_image_canvas.bind("<Motion>", self.on_mouse_hover)
        self.gray_image_canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.root.bind("<Configure>", self.on_window_resize)
        self.gray_image_canvas.bind("<Configure>", self.on_canvas_resize)
        # Initialize plot
        self.update_plot()

        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)

    def select_image(self):
        filename = filedialog.askopenfilename(
            title="Select image file",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")),
        )
        if not filename:
            return
        
        self.clear_all_data()
        
        img = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if img is None:
            messagebox.showerror("Error", "Could not open or find the image.")
            return
        
        self.original_img = img.copy()
        self.gray_img = img.copy()
        self.update_gray_image()
        self.save_chart_button.config(state=tk.NORMAL)
        self.export_button.config(state=tk.NORMAL)
        self.save_gray_image_button.config(state=tk.NORMAL)
        self.plot_handler.update_plot(self.plot_canvas, self.rectangles, self.original_img, self.line_width, self.line_color)

        self.excel_exporter = ExcelExporter(self.gray_img)
        
        self.image_processor = self.get_image_processor()

    def clear_all_data(self):
        self.rectangles = []
        self.original_img = None
        self.gray_img = None
        self.scaled_img = None
        self.current_image = None
        self.rect_start = None
        self.rect_end = None
        self.dragging = None
        self.resizing = None
        self.excel_exporter = None
        
        if self.gray_image_canvas:
            self.gray_image_canvas.delete("all")
        
        plt.clf()
        self.plot_canvas.draw()
        
        self.save_chart_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.DISABLED)
        self.save_gray_image_button.config(state=tk.DISABLED)
        self.chart_counter = 1

    def update_gray_image(self):
        if self.original_img is not None:
            self.scaled_img, self.scale_factor, self.image_start_x, self.image_start_y = self.image_handler.scale_image(
                self.original_img, self.gray_image_canvas.winfo_width(), self.gray_image_canvas.winfo_height()
            )
            self.display_scaled_image()
            self.plot_handler.update_plot(self.plot_canvas, self.rectangles, self.original_img, self.line_width, self.line_color)

    def display_scaled_image(self):
        if self.scaled_img is None:
            return

        image = Image.fromarray(self.scaled_img)
        self.current_image = ImageTk.PhotoImage(image=image)
        
        if self.gray_image_on_canvas:
            self.gray_image_canvas.delete(self.gray_image_on_canvas)
        
        self.gray_image_on_canvas = self.gray_image_canvas.create_image(self.image_start_x, self.image_start_y, anchor=tk.NW, image=self.current_image)
        self.update_display_image()
        
    def update_image_after_resize(self):
        # 获取新的画布尺寸
        new_width = self.gray_image_canvas.winfo_width()
        new_height = self.gray_image_canvas.winfo_height()
        
        # 只有当尺寸真的改变时才更新
        if new_width != self.last_width or new_height != self.last_height:
            self.last_width = new_width
            self.last_height = new_height
            if self.original_img is not None:
                self.update_gray_image()
    def on_window_resize(self, event):
        # 检查是否是主窗口触发的事件
        if event.widget == self.root:
            # 给一个短暂的延迟，确保新的尺寸已经被应用
            self.root.after(100, self.update_image_after_resize)

    def on_mouse_press(self, event):
        x, y = self.image_handler.canvas_to_image_coords(event.x, event.y, self.image_start_x, self.image_start_y, self.scale_factor)
        for i, (start, end, name, max_points) in enumerate(self.rectangles):
            if self.rectangle_handler.is_point_in_rect(x, y, start, end):
                self.dragging = i
                self.drag_start = (x, y)
                return
            elif self.rectangle_handler.is_point_near_corner(x, y, start, end):
                self.resizing = self.rectangle_handler.get_resize_direction(x, y, start, end)
                self.drag_start = (x, y)
                return
        self.rect_start = (x, y)
        self.rect_end = None

    def on_mouse_move(self, event):
        x, y = self.image_handler.canvas_to_image_coords(event.x, event.y, self.image_start_x, self.image_start_y, self.scale_factor)
        if self.dragging is not None:
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            start, end, name, max_points = self.rectangles[self.dragging]
            new_start = (
                max(0, min(start[0] + dx, self.gray_img.shape[1] - (end[0] - start[0]))),
                max(0, min(start[1] + dy, self.gray_img.shape[0] - (end[1] - start[1])))
            )
            new_end = (
                new_start[0] + (end[0] - start[0]),
                new_start[1] + (end[1] - start[1])
            )
            self.rectangles[self.dragging] = (new_start, new_end, name, max_points)
            self.drag_start = (x, y)
            self.update_display_image()
        elif self.resizing is not None:
            for i, (start, end, name, max_points) in enumerate(self.rectangles):
                if self.rectangle_handler.is_point_near_corner(self.drag_start[0], self.drag_start[1], start, end):
                    new_start, new_end = self.rectangle_handler.resize_rectangle(start, end, x, y, self.resizing, self.MIN_RECT_WIDTH, self.MIN_RECT_HEIGHT)
                    width = abs(new_end[0] - new_start[0])
                    height = abs(new_end[1] - new_start[1])
                    if width >= self.MIN_RECT_WIDTH and height >= self.MIN_RECT_HEIGHT:
                        self.rectangles[i] = (new_start, new_end, name, max_points)
                    break
            self.drag_start = (x, y)
            self.update_display_image()
        elif self.rect_start:
            self.rect_end = (x, y)
            self.update_display_image(drawing=True)  # 添加 drawing 参数
        else:
            for start, end, _, _ in self.rectangles:
                if self.rectangle_handler.is_point_near_corner(x, y, start, end):
                    self.update_display_image(highlight_corner=self.image_handler.image_to_canvas_coords(x, y, self.image_start_x, self.image_start_y, self.scale_factor))
                    return
            self.update_display_image()

    def on_mouse_release(self, event):
        if self.dragging is not None or self.resizing is not None:
            self.dragging = None
            self.resizing = None
            self.update_plot()
        elif self.rect_start and self.rect_end:
            if self.rect_start != self.rect_end:
                width = abs(self.rect_end[0] - self.rect_start[0])
                height = abs(self.rect_end[1] - self.rect_start[1])
                if width >= self.MIN_RECT_WIDTH and height >= self.MIN_RECT_HEIGHT:
                    rectangle_name = self.get_unique_chart_name()
                    self.rectangles.append(
                        (self.rect_start, self.rect_end, rectangle_name, 0 if self.MAX_POINTS == 0 else self.MAX_POINTS)
                    )
                    self.update_display_image()
                    self.update_plot()
                else:
                    messagebox.showwarning(
                        "Warning",
                        f"Rectangle size too small. Minimum size is {self.MIN_RECT_WIDTH}x{self.MIN_RECT_HEIGHT} pixels."
                    )
        self.rect_start = None
        self.rect_end = None

    def get_unique_chart_name(self):
            base_name = f"Chart {self.chart_counter}"
            name = base_name
            while any(rect[2] == name for rect in self.rectangles):
                self.chart_counter += 1
                name = f"Chart {self.chart_counter}"
            self.chart_counter += 1
            return name
        
    def on_mouse_hover(self, event):
        cursor = "arrow"
        for start, end, _, _ in self.rectangles:
            start_canvas = self.image_handler.image_to_canvas_coords(*start, self.image_start_x, self.image_start_y, self.scale_factor)
            end_canvas = self.image_handler.image_to_canvas_coords(*end, self.image_start_x, self.image_start_y, self.scale_factor)
            if self.rectangle_handler.is_point_near_corner(event.x, event.y, start_canvas, end_canvas):
                self.update_display_image(highlight_corner=(event.x, event.y))
                cursor = "sizing"
                break
            elif self.rectangle_handler.is_point_in_rect(event.x, event.y, start_canvas, end_canvas):
                cursor = "fleur"
                break
        self.gray_image_canvas.config(cursor=cursor)
    def export_current_rectangle_data(self, rect_index):
        if self.excel_exporter:
            start, end, name, max_points = self.rectangles[rect_index]
            self.excel_exporter.export_single_rectangle_data(start, end, name, max_points)
        else:
            messagebox.showerror("Error", "Please select an image first.")
            
    def on_right_click(self, event):
        x, y = self.image_handler.canvas_to_image_coords(event.x, event.y, self.image_start_x, self.image_start_y, self.scale_factor)
        for i, (start, end, name, max_points) in enumerate(self.rectangles):
            if self.rectangle_handler.is_point_in_rect(x, y, start, end):
                menu = Menu(self.root, tearoff=0)
                menu.add_command(label="Rename", command=lambda: self.rename_rectangle(i))
                menu.add_command(label="Delete", command=lambda: self.delete_rectangle(i))
                menu.add_command(label="Change Points", command=lambda: self.edit_rectangle_points(i))
                menu.add_command(label="Export Current Data", command=lambda: self.export_current_rectangle_data(i))
                menu.post(event.x_root, event.y_root)
                return

    def rename_rectangle(self, rect_index):
        old_name = self.rectangles[rect_index][2]
        new_name = simpledialog.askstring("Rename Rectangle", "Enter new name:", initialvalue=old_name)
        if new_name:
            self.rectangles[rect_index] = (*self.rectangles[rect_index][:2], new_name, self.rectangles[rect_index][3])
            self.update_display_image()
            self.update_plot()

    def delete_rectangle(self, rect_index):
        if messagebox.askyesno("Delete Rectangle", "Are you sure you want to delete this rectangle?"):
            del self.rectangles[rect_index]
            self.update_display_image()
            self.update_plot()

    def show_context_menu(self, x, y, rect_index):
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Delete", command=lambda: self.delete_rectangle(rect_index))
        context_menu.add_command(label="Change Points", command=lambda: self.edit_rectangle_points(rect_index))
        context_menu.post(x, y)


    def edit_rectangle_points(self, rect_index):
        start, end, name, max_points = self.rectangles[rect_index]

        top = tk.Toplevel(self.root)
        top.title(f"Edit Points for {name}")

        x1, y1 = start
        x2, y2 = end
        x1, x2 = sorted([max(0, min(x1, self.gray_img.shape[1])), max(0, min(x2, self.gray_img.shape[1]))])
        y1, y2 = sorted([max(0, min(y1, self.gray_img.shape[0])), max(0, min(y2, self.gray_img.shape[0]))])
        actual_points = (x2 - x1) * (y2 - y1)

        slider = Scale(top, from_=10, to=max(100000, actual_points), orient="horizontal", length=300, label="Number of Points")
        slider.set(max_points)
        slider.pack(pady=20)

        entry = Entry(top)
        entry.insert(0, str(max_points))
        entry.pack(pady=10)

        use_actual_points = tk.BooleanVar()
        use_actual_points_checkbox = tk.Checkbutton(top, text="Use actual points", variable=use_actual_points)
        use_actual_points_checkbox.pack(pady=10)

        def update_value(val):
            if not use_actual_points.get():
                entry.delete(0, tk.END)
                entry.insert(0, val)

        slider.config(command=update_value)

        def on_confirm():
            try:
                if use_actual_points.get():
                    new_max_points = actual_points
                else:
                    new_max_points = int(entry.get())

                if 10 <= new_max_points <= max(100000, actual_points):
                    self.rectangles[rect_index] = (start, end, name, new_max_points)
                    self.update_plot()
                    top.destroy()
                else:
                    messagebox.showerror("Error", f"Please enter a value between 10 and {max(100000, actual_points)}.")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid integer.")

        confirm_button = tk.Button(top, text="Confirm", command=on_confirm)
        confirm_button.pack(pady=10)

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

    def update_display_image(self, highlight_corner=None, drawing=False):
        if self.scaled_img is None:
            return
        display_img = self.image_handler.update_display_image(
            self.scaled_img, self.rectangles, self.image_start_x, self.image_start_y,
            self.circle_radius, self.rect_color, self.rect_start, self.rect_end,
            os.path.join(self.get_base_path(), 'assets', 'fonts', 'MicrosoftYaHei.ttf'),
            highlight_corner, drawing, self.scale_factor
        )
        image = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        self.current_image = ImageTk.PhotoImage(image=image)
        self.gray_image_canvas.delete("all")
        self.gray_image_canvas.create_image(self.image_start_x, self.image_start_y, anchor=tk.NW, image=self.current_image)


    def update_plot(self):
        self.plot_handler.update_plot(self.plot_canvas, self.rectangles, self.original_img, self.line_width, self.line_color)

    def set_line_width(self):
        def update_width(value):
            self.line_width = float(value)
            width_label.config(text=f"Line Width: {self.line_width:.2f}")

        top = tk.Toplevel(self.root)
        top.title("Line Width")
        top.geometry("300x150")

        width_label = ttk.Label(top, text=f"Line Width: {self.line_width:.2f}")
        width_label.pack(pady=10)

        width_scale = ttk.Scale(top, from_=0.1, to=10, orient="horizontal", length=200, command=update_width)
        width_scale.set(self.line_width)
        width_scale.pack(pady=10)

        ttk.Button(top, text="Apply", command=lambda: [self.update_plot(), top.destroy()]).pack(pady=10)

    def set_max_points(self):
        def update_max_points(value):
            self.MAX_POINTS = int(float(value))
            points_label.config(text=f"Max Points: {self.MAX_POINTS}")

        top = tk.Toplevel(self.root)
        top.title("Max Points")
        top.geometry("300x200")

        points_label = ttk.Label(top, text=f"Max Points: {self.MAX_POINTS}")
        points_label.pack(pady=10)

        points_scale = ttk.Scale(top, from_=10, to=100000, orient="horizontal", length=200, command=update_max_points)
        points_scale.set(self.MAX_POINTS)
        points_scale.pack(pady=10)

        use_actual_points = tk.BooleanVar()
        use_actual_points_checkbox = ttk.Checkbutton(
            top, text="Use actual points", variable=use_actual_points,
            command=lambda: [points_scale.set(0), update_max_points('0')] if use_actual_points.get() else None
        )
        use_actual_points_checkbox.pack(pady=10)

        def on_confirm():
            if use_actual_points.get():
                self.MAX_POINTS = 0
            self.set_max_points_num_button.config(
                text=f"Set Max Points ({'Actual' if self.MAX_POINTS == 0 else self.MAX_POINTS})"
            )
            top.destroy()

        button_frame = tk.Frame(top)
        button_frame.pack(pady=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=top.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        confirm_button = ttk.Button(button_frame, text="Confirm", command=on_confirm)
        confirm_button.pack(side=tk.LEFT, padx=5)

        top.bind("<Return>", lambda event: on_confirm())

        def update_checkbox_state():
            if use_actual_points.get():
                points_scale.set(0)
                points_scale.config(state=tk.DISABLED)
            else:
                points_scale.config(state=tk.NORMAL)

        use_actual_points_checkbox.config(command=update_checkbox_state)

        points_scale.focus_set()

        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = (self.root.winfo_width() - width) // 2 + self.root.winfo_x()
        y = (self.root.winfo_height() - height) // 2 + self.root.winfo_y()
        top.geometry(f"+{x}+{y}")

    def export_all_data_to_excel(self):
        if self.excel_exporter:
            self.excel_exporter.export_all_data_to_excel(self.rectangles)
        else:
            messagebox.showerror("Error", "Please select an image first.")

    def get_image_processor(self):
        from utils.image_utils import ImageProcessor
        return ImageProcessor(self.gray_img, plt, show_progress_bar)

    def on_closing_root_win(self):
        if messagebox.askokcancel("Quit", "Are you sure to quit?"):
            self.root.destroy()

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            return sys._MEIPASS
        else:
            # we are running in a normal Python environment
            return os.path.dirname(os.path.abspath(__file__))

    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 先隐藏主窗口
        
        # 显示加载屏幕
        show_loading_screen()
        
        # 配置主窗口
        self.root.title("GrayScale Analyzer")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_root_win)
        self.create_main_window()
        
        # 确保主窗口完全加载
        self.root.update_idletasks()
        
        # 隐藏加载屏幕（假设它是顶层窗口）
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        
        # 显示主窗口
        self.root.deiconify()
        
        self.root.mainloop()

def main():
    app = GrayScaleAnalyzer()
    app.run()

if __name__ == "__main__":
    main()