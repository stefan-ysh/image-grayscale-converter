# -- coding: UTF-8 --
import cv2
import wx
import numpy as np


class ImageHandler:
    @staticmethod
    def scale_image(original_img, canvas_width, canvas_height):
        """Scale an image to fit within the canvas while maintaining aspect ratio"""
        img_height, img_width = original_img.shape[:2]

        # Calculate scale factors
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        scale_factor = min(width_ratio, height_ratio)

        # Calculate new dimensions
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        # Resize image
        scaled_img = cv2.resize(original_img, (new_width, new_height), 
                              interpolation=cv2.INTER_AREA)

        # Calculate centering offsets
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2

        return scaled_img, scale_factor, x_offset, y_offset

    @staticmethod
    def canvas_to_image_coords(x, y, x_offset, y_offset, scale_factor):
        """Convert canvas coordinates to original image coordinates"""
        image_x = int((x - x_offset) / scale_factor)
        image_y = int((y - y_offset) / scale_factor)
        return (image_x, image_y)

    @staticmethod
    def image_to_canvas_coords(x, y, x_offset, y_offset, scale_factor):
        """Convert original image coordinates to canvas coordinates"""
        canvas_x = int(x * scale_factor + x_offset)
        canvas_y = int(y * scale_factor + y_offset)
        return (canvas_x, canvas_y)

    @staticmethod
    def draw_rectangles_on_dc(dc, rectangles, selected_rect_index=-1):
        """Draw rectangles and resize handles on a wxPython DC"""
        normal_pen = wx.Pen(wx.Colour(0, 255, 0), 2)  # Green
        selected_pen = wx.Pen(wx.Colour(255, 0, 0), 2)  # Red
        selected_brush = wx.Brush(wx.Colour(255, 0, 0, 80))  # Semi-transparent red
        
        for i, rect in enumerate(rectangles):
            if i == selected_rect_index:
                dc.SetPen(selected_pen)
                dc.SetBrush(selected_brush)
            else:
                dc.SetPen(normal_pen)
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
            
            dc.DrawRectangle(*rect)
            
            if i == selected_rect_index:
                ImageHandler.draw_resize_handles(dc, rect)

    @staticmethod
    def draw_resize_handles(dc, rect):
        """Draw resize handles at the corners of the rectangle"""
        x, y, w, h = rect
        handle_size = 6
        corners = [
            (x, y),           # Top-left
            (x + w, y),       # Top-right
            (x, y + h),       # Bottom-left
            (x + w, y + h)    # Bottom-right
        ]
        
        dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
        
        for cx, cy in corners:
            dc.DrawRectangle(
                cx - handle_size//2,
                cy - handle_size//2,
                handle_size,
                handle_size
            )
