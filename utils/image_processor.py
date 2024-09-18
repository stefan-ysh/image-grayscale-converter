# -- coding: UTF-8 --
from tkinter import messagebox, filedialog
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class ImageProcessor:
    def __init__(self, img, plt, show_progress_bar):
        self.img = img
        self.plt = plt
        self.show_progress_bar = show_progress_bar

    def save_plot_image(self):
        if self.img is None:
            messagebox.showerror("Error", "Please select an image first.")
            return

        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            title="Save Chart Image",
            initialfile=f"chart_{current_time}.png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if filename:

            def save_task():
                self.plt.savefig(filename, dpi=300, bbox_inches="tight")
                return True

            self._handle_save_result(
                self.show_progress_bar("Saving Chart Image", save_task), "Chart image"
            )

    @staticmethod
    def save_gray_img(cv2, gray_img, rectangles, show_progress_bar):
        if gray_img is None:
            messagebox.showerror("Error", "Please select an image first.")
            return

        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            title="Save Gray Image",
            initialfile=f"gray_image_{current_time}.png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )

        if filename:

            def save_task():
                img_with_rectangles = ImageProcessor._draw_rectangles(
                    cv2, gray_img, rectangles
                )
                cv2.imwrite(filename, img_with_rectangles)
                return True

            ImageProcessor._handle_save_result(
                show_progress_bar("Saving Gray Image", save_task),
                "Gray image with rectangles and names",
            )

    @staticmethod
    def _draw_rectangles(cv2, gray_img, rectangles):
        img_with_rectangles = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2RGB)
        
        # 创建一个PIL Image对象
        pil_img = Image.fromarray(cv2.cvtColor(img_with_rectangles, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        # 加载字体
        try:
            font = ImageFont.truetype("assets/fonts/MicrosoftYaHei.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        for rect in rectangles:
            start, end, name, _ = rect
            # 在图像上绘制矩形框，使用蓝色（RGB格式），线宽为2
            draw.rectangle([start, end], outline=(0, 0, 255), width=1)
            
            # 设置文本位置，略微在矩形框上方
            text_x, text_y = start[0], start[1] - 25
            
            # 在图像上绘制文本，使用实际的名称
            draw.text((text_x, text_y), name, font=font, fill=(0, 0, 255))

        # 将PIL Image转换回OpenCV格式
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


    @staticmethod
    def _handle_save_result(result, image_type):
        if result:
            messagebox.showinfo("Success", f"{image_type} saved successfully!")
        else:
            messagebox.showerror("Error", f"Failed to save {image_type.lower()}.")
