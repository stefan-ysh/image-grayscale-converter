#-- coding: UTF-8 --
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
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if filename:
            # 保存折线图到指定路径
            plt.savefig(filename)
            # print(f"Plot saved as {filename}")
            messagebox.showinfo("Success", "Plot saved successfully!")

    @staticmethod
    def save_gray_img(cv2, gray_img, rectangles):
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
            # Convert grayscale image to BGR for colored rectangles
            img_with_rectangles = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

            print(f"Number of rectangles: {len(rectangles)}")
            for idx, rect in enumerate(rectangles):
                start, end, _, _ = rect
                print(f"Drawing rectangle {idx+1}: {start} to {end}")
                cv2.rectangle(img_with_rectangles, start, end, (0, 255, 0), 2)
                text_x, text_y = start[0], start[1] - 10
                cv2.putText(
                    img_with_rectangles,
                    f"Chart {idx+1}",
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )

            cv2.imwrite(filename, img_with_rectangles)
            print(f"Image saved to: {filename}")
            messagebox.showinfo(
                "Success", "Gray image with rectangles and names saved successfully!"
            )



# def save_gray_img():
#     global gray_img, rectangles
#     if gray_img is None:
#         messagebox.showerror("Error", "Please select an image first.")
#         return

#     # Get current time for filename
#     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#     # Open save file dialog
#     filename = filedialog.asksaveasfilename(
#         defaultextension=".png",
#         title="Save Gray Image",
#         initialfile=f"gray_image_{current_time}.png",
#         filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
#     )

#     if filename:
#         # Create a copy of the gray image to draw on
#         img_with_rectangles = gray_img.copy()

#         # Draw rectangles and their names on the image
#         for idx, rect in enumerate(rectangles):
#             cv2.rectangle(img_with_rectangles, rect[0], rect[1], (0, 255, 0), 2)
#             # Calculate position for text (above the rectangle)
#             text_x = rect[0][0]
#             text_y = rect[0][1] - 10  # 10 pixels above the rectangle
#             cv2.putText(
#                 img_with_rectangles,
#                 f"Chart {idx+1}",
#                 (text_x, text_y),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.5,
#                 (0, 255, 0),
#                 1,
#             )

#         # Save the image with rectangles and names
#         cv2.imwrite(filename, img_with_rectangles)
#         messagebox.showinfo(
#             "Success", "Gray image with rectangles and names saved successfully!"
#         )
