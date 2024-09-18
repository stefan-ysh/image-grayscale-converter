import matplotlib.pyplot as plt
import numpy as np


class PlotHandler:
    @staticmethod
    def update_plot(plot_canvas, rectangles, original_img, line_width, line_color):
        plt.clf()
        if not rectangles:
            plt.text(
                0.5,
                0.5,
                "Please select an image \n to generate a grayscale chart",
                ha="center",
                va="center",
                fontsize=20,
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
                    [
                        max(0, min(x1, original_img.shape[1])),
                        max(0, min(x2, original_img.shape[1])),
                    ]
                )
                y1, y2 = sorted(
                    [
                        max(0, min(y1, original_img.shape[0])),
                        max(0, min(y2, original_img.shape[0])),
                    ]
                )

                rect_pixels = original_img[y1:y2, x1:x2].flatten()

                if len(rect_pixels) == 0:
                    continue

                if max_points == 0 or len(rect_pixels) <= max_points:
                    max_points = len(rect_pixels)
                else:
                    indices = np.linspace(
                        0, len(rect_pixels) - 1, max_points, dtype=int
                    )
                    rect_pixels = rect_pixels[indices]

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
                ax.plot(
                    x_data, y_data, marker="", linewidth=line_width, color=line_color
                )
                ax.set_title(f"{name} (Points: {max_points})")
                ax.set_xlabel("Pixel Index")
                ax.set_ylabel("Grayscale Value")

        plt.tight_layout()
        plot_canvas.draw()
