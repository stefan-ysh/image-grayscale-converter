from tkinter import messagebox, filedialog
from datetime import datetime


class ImageProcessor:
    def __init__(self, img, plt):
        self.img = img
        self.plt = plt

    @staticmethod
    def save_plot_image(img, plt):
        # 如果没有选择图片，则不允许保存
        if img is None:
            messagebox.showerror("Error", "Please select an image first.")
            return
        # 获取当前时间并格式化为字符串
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # 弹出保存文件对话框，并使用当前时间作为默认文件名
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            title="select path to save image",
            initialfile=f"gray_values_plot_{current_time}.png",
            filetypes=[("PNG files", "*.png"),
                       ("All files", "*.*")]
        )
        if filename:
            # 保存折线图到指定路径
            plt.savefig(filename)
            # print(f"Plot saved as {filename}")
            messagebox.showinfo("Success", "Plot saved successfully!")
