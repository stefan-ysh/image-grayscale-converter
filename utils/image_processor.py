# -- coding: UTF-8 --
from tkinter import messagebox, filedialog
from datetime import datetime


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
        img_with_rectangles = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
        for idx, rect in enumerate(rectangles):
            start, end, _, _ = rect
            # 在图像上绘制矩形框，使用蓝色（BGR格式），线宽为2
            cv2.rectangle(img_with_rectangles, start, end, (255, 0, 0), 2)
            # 设置文本位置，略微在矩形框上方
            text_x, text_y = start[0], start[1] - 10
            # 在图像上绘制文本，使用简单的字体，文本内容为"Chart {idx+1}"
            cv2.putText(
                # 指定图像
                img_with_rectangles,
                # 指定文本内容
                f"Chart {idx+1}",
                # 指定文本位置
                (text_x, text_y),
                # 指定字体
                cv2.FONT_HERSHEY_SIMPLEX,
                # 指定字体大小
                0.5,
                # 指定颜色
                (255, 0, 0),
                # 指定线宽
                1,
            )
        return img_with_rectangles

    @staticmethod
    def _handle_save_result(result, image_type):
        if result:
            messagebox.showinfo("Success", f"{image_type} saved successfully!")
        else:
            messagebox.showerror("Error", f"Failed to save {image_type.lower()}.")
