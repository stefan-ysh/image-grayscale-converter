# -- coding: UTF-8 --
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tkinter import messagebox, filedialog
from datetime import datetime


class ImageHandler:
    @staticmethod
    def scale_image(original_img, canvas_width, canvas_height):
        img_height, img_width = original_img.shape[:2]

        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        scale_factor = min(width_ratio, height_ratio)

        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        scaled_img = cv2.resize(
            original_img, (new_width, new_height), interpolation=cv2.INTER_AREA
        )

        image_start_x = (canvas_width - new_width) // 2
        image_start_y = (canvas_height - new_height) // 2

        return scaled_img, scale_factor, image_start_x, image_start_y

    @staticmethod
    def canvas_to_image_coords(x, y, image_start_x, image_start_y, scale_factor):
        image_x = int((x - image_start_x) / scale_factor)
        image_y = int((y - image_start_y) / scale_factor)
        return (image_x, image_y)

    @staticmethod
    def image_to_canvas_coords(x, y, image_start_x, image_start_y, scale_factor):
        canvas_x = int(x * scale_factor + image_start_x)
        canvas_y = int(y * scale_factor + image_start_y)
        return (canvas_x, canvas_y)

    @staticmethod
    def update_display_image(
        scaled_img,
        rectangles,
        image_start_x,
        image_start_y,
        circle_radius,
        rect_color,
        rect_start,
        rect_end,
        font_path,
        highlight_corner=None,
        drawing=False,
        scale_factor=1.0,
    ):
        display_img = scaled_img.copy()
        pil_img = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        try:
            font = ImageFont.truetype(font_path, 15)
        except IOError:
            print(f"Error: Font file not found at {font_path}")
            font = ImageFont.load_default()

        for start, end, name, _ in rectangles:
            start_canvas = ImageHandler.image_to_canvas_coords(
                start[0], start[1], image_start_x, image_start_y, scale_factor
            )
            end_canvas = ImageHandler.image_to_canvas_coords(
                end[0], end[1], image_start_x, image_start_y, scale_factor
            )

            draw.rectangle(
                [
                    (start_canvas[0] - image_start_x, start_canvas[1] - image_start_y),
                    (end_canvas[0] - image_start_x, end_canvas[1] - image_start_y),
                ],
                outline=(0, 0, 255),
                width=2,
            )

            left, top, right, bottom = draw.textbbox((0, 0), name, font=font)
            text_width = right - left
            text_height = bottom - top
            rect_width = end_canvas[0] - start_canvas[0]

            if text_width + 10 > rect_width:
                text_position = (
                    start_canvas[0] - image_start_x,
                    start_canvas[1] - image_start_y - text_height - 5,
                )
            else:
                text_position = (
                    start_canvas[0] - image_start_x + 5,
                    start_canvas[1] - image_start_y + 5,
                )

            text_bg = [
                text_position[0] - 2,
                text_position[1] - 2,
                text_position[0] + text_width + 2,
                text_position[1] + text_height + 2,
            ]
            draw.rectangle(text_bg, fill=(255, 255, 255))

            draw.text(text_position, name, font=font, fill=(0, 0, 255))

            corners = [
                start_canvas,
                (start_canvas[0], end_canvas[1]),
                end_canvas,
                (end_canvas[0], start_canvas[1]),
            ]
            for corner in corners:
                corner_img = (corner[0] - image_start_x, corner[1] - image_start_y)
                if (
                    highlight_corner
                    and abs(highlight_corner[0] - corner[0]) < 10
                    and abs(highlight_corner[1] - corner[1]) < 10
                ):
                    draw.ellipse(
                        [
                            (
                                corner_img[0] - circle_radius,
                                corner_img[1] - circle_radius,
                            ),
                            (
                                corner_img[0] + circle_radius,
                                corner_img[1] + circle_radius,
                            ),
                        ],
                        fill=(0, 255, 0),
                    )
                else:
                    draw.ellipse(
                        [
                            (
                                corner_img[0] - circle_radius,
                                corner_img[1] - circle_radius,
                            ),
                            (
                                corner_img[0] + circle_radius,
                                corner_img[1] + circle_radius,
                            ),
                        ],
                        outline=(255, 0, 0),
                    )

        display_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if drawing and rect_start and rect_end:
            start_canvas = ImageHandler.image_to_canvas_coords(
                rect_start[0], rect_start[1], image_start_x, image_start_y, scale_factor
            )
            end_canvas = ImageHandler.image_to_canvas_coords(
                rect_end[0], rect_end[1], image_start_x, image_start_y, scale_factor
            )
            cv2.rectangle(
                display_img,
                (start_canvas[0] - image_start_x, start_canvas[1] - image_start_y),
                (end_canvas[0] - image_start_x, end_canvas[1] - image_start_y),
                rect_color,
                2,
            )

        return display_img


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
            font_path = os.path.join(
                ImageProcessor.get_base_path(), "assets", "fonts", "MicrosoftYaHei.ttf"
            )
            font = ImageFont.truetype(font_path, 20)
        except IOError:
            font = ImageFont.load_default()

        for rect in rectangles:
            start, end, name, _ = rect
            # 在图像上绘制矩形框，使用蓝色（RGB格式），线宽为1
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

    @staticmethod
    def get_base_path():
        # Add this method to get the base path of your project
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
