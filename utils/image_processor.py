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
        for rect in rectangles:
            start, end, name, _ = rect  # 解包时包括名称
            # 在图像上绘制矩形框，使用蓝色（BGR格式），线宽为2
            cv2.rectangle(img_with_rectangles, start, end, (255, 0, 0), 2)
            # 设置文本位置，略微在矩形框上方
            text_x, text_y = start[0], start[1] - 10
            # 在图像上绘制文本，使用实际的名称
            cv2.putText(
                img_with_rectangles,
                name,  # 使用传入的实际名称
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                1,
            )
        return img_with_rectangles

    @staticmethod
    def _handle_save_result(result, image_type):
        if result:
            messagebox.showinfo("Success", f"{image_type} saved successfully!")
        else:
            messagebox.showerror("Error", f"Failed to save {image_type.lower()}.")
