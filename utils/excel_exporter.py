import pandas as pd
import numpy as np
from datetime import datetime
from tkinter import filedialog, messagebox
from openpyxl.chart import LineChart, Reference
from utils.show_progress_bar import show_progress_bar


class ExcelExporter:
    def __init__(self, gray_img):
        self.gray_img = gray_img

    def export_data_to_excel(self, rectangles):
        if self.gray_img is None:
            messagebox.showerror("Error", "Please select an image first.")
            return

        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            title="Save Data as Excel File",
            initialfile=f"pixel_data_{current_time}.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )

        if not filename:
            return

        def export_task():
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                for idx, (start, end, name, max_points) in enumerate(rectangles):
                    x1, y1 = start
                    x2, y2 = end
                    x1, x2 = sorted(
                        [
                            max(0, min(x1, self.gray_img.shape[1])),
                            max(0, min(x2, self.gray_img.shape[1])),
                        ]
                    )
                    y1, y2 = sorted(
                        [
                            max(0, min(y1, self.gray_img.shape[0])),
                            max(0, min(y2, self.gray_img.shape[0])),
                        ]
                    )
                    rect_pixels = self.gray_img[y1:y2, x1:x2].flatten()

                    total_points = len(rect_pixels)
                    if total_points > max_points:
                        indices = np.linspace(
                            0, total_points - 1, max_points, dtype=int
                        )
                        rect_pixels = rect_pixels[indices]
                    else:
                        indices = np.arange(total_points)
                        max_points = total_points  # 更新max_points为实际点数

                    data = []
                    for i, (index, gray_value) in enumerate(zip(indices, rect_pixels)):
                        x_coord = x1 + (index % (x2 - x1))
                        y_coord = (
                            self.gray_img.shape[0] - (y1 + (index // (x2 - x1))) - 1
                        )
                        data.append([i + 1, gray_value, x_coord, y_coord])

                    df = pd.DataFrame(data, columns=["Index", "Grayscale", "X", "Y"])
                    sheet_name = f"Chart_{idx + 1}"

                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # 在这里创建和添加图表
                    worksheet = writer.sheets[sheet_name]

                    chart = LineChart()
                    chart.title = f"Grayscale Value vs Index - {name}"
                    chart.style = 13
                    chart.x_axis.title = "Index"
                    chart.y_axis.title = "Grayscale Value"

                    data = Reference(
                        worksheet, min_col=2, min_row=1, max_col=2, max_row=len(df) + 1
                    )
                    categories = Reference(
                        worksheet, min_col=1, min_row=2, max_row=len(df) + 1
                    )

                    chart.add_data(data, titles_from_data=True)
                    chart.set_categories(categories)

                    # 设置x轴的最大值为实际的点数
                    chart.x_axis.scaling.max = max_points

                    # 设置线条
                    s = chart.series[0]
                    s.graphicalProperties.line.solidFill = "0000FF"
                    s.graphicalProperties.line.width = 4800

                    worksheet.add_chart(chart, "F2")

            return True

        result = show_progress_bar("Exporting Data", export_task)

        if result:
            messagebox.showinfo(
                "Success", "Data exported and charts added successfully!"
            )
        else:
            messagebox.showerror("Error", "Failed to export data.")
