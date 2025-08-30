# -- coding: UTF-8 --
import wx
import cv2
import numpy as np
from PIL import Image
from utils.excel_exporter import ExcelExporter

class ImagePanel(wx.Panel):
    def __init__(self, parent, main_frame):
        super().__init__(parent)
        
        self.main_frame = main_frame
        
        # Initialize variables
        self.rect_color = (0, 255, 0)  # BGR format, green
        self.current_image = None
        self.rectangles = []  # Store in display coordinates
        self.original_rectangles = []  # Store in original image coordinates
        self.rectangle_names = []  # Store rectangle names
        self.rectangle_max_points = []  # Store individual rectangle point settings
        self.original_img = None
        self.gray_img = None
        self.scaled_img = None
        self.current_scale = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.resize_direction = None
        self.resize_start = None
        self.MIN_RECT_WIDTH = 20
        self.MIN_RECT_HEIGHT = 20
        self.dragging = False
        self.selected_rect_index = -1
        self.drag_start = None
        self.start_pos = None
        self.current_rect = None
        self.resize_handles_size = 8
        
        # Set background color
        self.SetBackgroundColour(wx.Colour(200, 200, 200))
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
        # Make panel focusable for keyboard events
        self.SetCanFocus(True)

    def get_image_bounds(self):
        """Get the bounds of the scaled image on the panel"""
        if self.scaled_img is not None:
            height, width = self.scaled_img.shape[:2]
            panel_size = self.GetSize()
            x_offset = (panel_size.width - width) // 2
            y_offset = (panel_size.height - height) // 2
            return x_offset, y_offset, width, height
        return 0, 0, 0, 0

    def point_in_image(self, point):
        """Check if a point is within the image bounds"""
        x_offset, y_offset, width, height = self.get_image_bounds()
        return (x_offset <= point.x <= x_offset + width and 
                y_offset <= point.y <= y_offset + height)

    def on_paint(self, event):
        """Handle paint events"""
        dc = wx.PaintDC(self)
        dc.Clear()
        
        if self.current_image:
            x_offset, y_offset = self.get_image_bounds()[:2]
            dc.DrawBitmap(self.current_image, x_offset, y_offset)
            
            # Draw existing rectangles
            for i, rect in enumerate(self.rectangles):
                if i == self.selected_rect_index:
                    # Red for selected
                    dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 2))
                    dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0, 80)))
                    dc.DrawRectangle(*rect)
                    
                    # Draw resize handles
                    self.draw_resize_handles(dc, rect)
                else:
                    # Use current rect_color for others
                    color = wx.Colour(*self.rect_color[::-1])  # Convert BGR to RGB
                    dc.SetPen(wx.Pen(color, 2))
                    dc.SetBrush(wx.TRANSPARENT_BRUSH)
                    dc.DrawRectangle(*rect)
                
                # Draw rectangle name
                if i < len(self.rectangle_names):
                    dc.SetTextForeground(wx.Colour(255, 255, 255))
                    dc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                    
                    # Draw text with background
                    text = self.rectangle_names[i]
                    text_size = dc.GetTextExtent(text)
                    text_x = rect[0] + 2
                    text_y = rect[1] + 2
                    
                    # Draw black background for text
                    dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 150)))
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
                    dc.DrawRectangle(text_x - 1, text_y - 1, text_size.width + 2, text_size.height + 2)
                    
                    # Draw text
                    dc.DrawText(text, text_x, text_y)
            
            # Draw rectangle being created
            if hasattr(self, 'current_rect') and self.current_rect is not None:
                dc.SetPen(wx.Pen(wx.Colour(*self.rect_color[::-1]), 2))
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.DrawRectangle(*self.current_rect)

    def draw_resize_handles(self, dc, rect):
        """Draw resize handles for the selected rectangle"""
        x, y, w, h = rect
        handle_size = self.resize_handles_size
        
        # Set brush and pen for handles
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
        
        # Draw corner handles
        handles = [
            (x - handle_size//2, y - handle_size//2),  # top-left
            (x + w - handle_size//2, y - handle_size//2),  # top-right
            (x - handle_size//2, y + h - handle_size//2),  # bottom-left
            (x + w - handle_size//2, y + h - handle_size//2),  # bottom-right
        ]
        
        for hx, hy in handles:
            dc.DrawRectangle(hx, hy, handle_size, handle_size)

    def get_resize_direction(self, pos, rect):
        """Determine resize direction based on mouse position"""
        x, y, w, h = rect
        handle_size = self.resize_handles_size
        
        # Check corners
        if (x - handle_size <= pos.x <= x + handle_size and 
            y - handle_size <= pos.y <= y + handle_size):
            return "top_left"
        elif (x + w - handle_size <= pos.x <= x + w + handle_size and 
              y - handle_size <= pos.y <= y + handle_size):
            return "top_right"
        elif (x - handle_size <= pos.x <= x + handle_size and 
              y + h - handle_size <= pos.y <= y + h + handle_size):
            return "bottom_left"
        elif (x + w - handle_size <= pos.x <= x + w + handle_size and 
              y + h - handle_size <= pos.y <= y + h + handle_size):
            return "bottom_right"
        
        return None

    def is_point_in_rect(self, pos, rect):
        """Check if point is inside rectangle"""
        x, y, w, h = rect
        return x <= pos.x <= x + w and y <= pos.y <= y + h

    def on_left_down(self, event):
        """Handle left mouse button down events"""
        pos = event.GetPosition()
        if not self.point_in_image(pos):
            return
        
        # Check if clicked on resize handle of selected rectangle
        if self.selected_rect_index >= 0:
            resize_direction = self.get_resize_direction(pos, self.rectangles[self.selected_rect_index])
            if resize_direction:
                self.resize_direction = resize_direction
                self.resize_start = pos
                return
        
        # Check if clicked on a rectangle
        for i, rect in enumerate(self.rectangles):
            if self.is_point_in_rect(pos, rect):
                self.selected_rect_index = i
                self.dragging = True
                self.drag_start = pos
                self.Refresh()
                
                # Select the corresponding plot tab
                self.main_frame.select_plot_tab(i)
                
                # Analyze the region but don't create new plot if already exists
                if not self.main_frame.plot_panel.has_plot(i):
                    self.analyze_rectangle(i)
                return
        
        # If not clicking on a rectangle, start drawing a new one
        self.selected_rect_index = -1
        self.start_pos = pos
        self.dragging = False
        self.resize_direction = None
        self.current_rect = None
        self.resize_start = None
        self.Refresh()

    def on_motion(self, event):
        """Handle mouse motion events"""
        pos = event.GetPosition()
        
        # Update cursor based on position
        if self.selected_rect_index >= 0:
            resize_direction = self.get_resize_direction(pos, self.rectangles[self.selected_rect_index])
            if resize_direction in ["top_left", "bottom_right"]:
                self.SetCursor(wx.Cursor(wx.CURSOR_SIZENWSE))
            elif resize_direction in ["top_right", "bottom_left"]:
                self.SetCursor(wx.Cursor(wx.CURSOR_SIZENESW))
            elif self.is_point_in_rect(pos, self.rectangles[self.selected_rect_index]):
                self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            else:
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        
        if not event.Dragging():
            return
            
        current_pos = self.constrain_point_to_image(pos)
            
        if self.resize_direction and self.selected_rect_index >= 0:
            # Resize the selected rectangle
            self.resize_rectangle(current_pos)
            
        elif self.dragging and self.selected_rect_index >= 0:
            # Move the selected rectangle
            self.move_rectangle(current_pos)
            
        elif hasattr(self, 'start_pos') and self.start_pos:
            # Drawing a new rectangle
            width = current_pos.x - self.start_pos.x
            height = current_pos.y - self.start_pos.y
            
            self.current_rect = (
                min(self.start_pos.x, current_pos.x),
                min(self.start_pos.y, current_pos.y),
                abs(width),
                abs(height)
            )
            self.Refresh()

    def resize_rectangle(self, current_pos):
        """Resize the selected rectangle"""
        rect = list(self.rectangles[self.selected_rect_index])
        
        if self.resize_direction == "bottom_right":
            rect[2] = current_pos.x - rect[0]
            rect[3] = current_pos.y - rect[1]
        elif self.resize_direction == "top_left":
            old_right = rect[0] + rect[2]
            old_bottom = rect[1] + rect[3]
            rect[0] = current_pos.x
            rect[1] = current_pos.y
            rect[2] = old_right - rect[0]
            rect[3] = old_bottom - rect[1]
        elif self.resize_direction == "top_right":
            old_bottom = rect[1] + rect[3]
            rect[1] = current_pos.y
            rect[2] = current_pos.x - rect[0]
            rect[3] = old_bottom - rect[1]
        elif self.resize_direction == "bottom_left":
            old_right = rect[0] + rect[2]
            rect[0] = current_pos.x
            rect[2] = old_right - rect[0]
            rect[3] = current_pos.y - rect[1]
        
        # Ensure minimum size
        if rect[2] >= self.MIN_RECT_WIDTH and rect[3] >= self.MIN_RECT_HEIGHT:
            self.rectangles[self.selected_rect_index] = tuple(rect)
            self.original_rectangles[self.selected_rect_index] = self.scale_rect_to_original(rect)
            
            # Don't update plot during resize for performance - will update on mouse up
        
        self.Refresh()

    def move_rectangle(self, current_pos):
        """Move the selected rectangle"""
        dx = current_pos.x - self.drag_start.x
        dy = current_pos.y - self.drag_start.y
        
        rect = list(self.rectangles[self.selected_rect_index])
        new_x = rect[0] + dx
        new_y = rect[1] + dy
        
        # Constrain rectangle to image bounds
        x_offset, y_offset, width, height = self.get_image_bounds()
        new_x = max(x_offset, min(new_x, x_offset + width - rect[2]))
        new_y = max(y_offset, min(new_y, y_offset + height - rect[3]))
        
        rect[0] = new_x
        rect[1] = new_y
        self.rectangles[self.selected_rect_index] = tuple(rect)
        self.original_rectangles[self.selected_rect_index] = self.scale_rect_to_original(rect)
        
        # Don't update plot during move for performance - will update on mouse up
        
        self.drag_start = current_pos
        self.Refresh()

    def on_left_up(self, event):
        """Handle left mouse button up events"""
        if self.resize_direction:
            self.resize_direction = None
            self.resize_start = None
            # Always update plot after resize
            if self.selected_rect_index >= 0:
                self.analyze_rectangle(self.selected_rect_index)
        elif self.dragging:
            self.dragging = False
            # Always update plot after move
            if self.selected_rect_index >= 0:
                self.analyze_rectangle(self.selected_rect_index)
        elif hasattr(self, 'start_pos') and self.start_pos and hasattr(self, 'current_rect') and self.current_rect:
            # Finish creating new rectangle
            if self.current_rect[2] >= self.MIN_RECT_WIDTH and self.current_rect[3] >= self.MIN_RECT_HEIGHT:
                self.rectangles.append(self.current_rect)
                self.original_rectangles.append(self.scale_rect_to_original(self.current_rect))
                
                # Generate default rectangle name
                rect_index = len(self.rectangles) - 1
                default_name = f"region_{rect_index + 1}"
                self.rectangle_names.append(default_name)
                
                # Add default max points setting (use global)
                self.rectangle_max_points.append(-1)  # -1 means use global setting
                
                # Select and analyze
                self.selected_rect_index = rect_index
                self.analyze_rectangle(self.selected_rect_index)
        
        # Cleanup
        self.Refresh()
        if hasattr(self, 'current_rect'): 
            self.current_rect = None
        if hasattr(self, 'start_pos'): 
            self.start_pos = None

    def on_right_down(self, event):
        """Handle right mouse button down events"""
        pos = event.GetPosition()
        for i, rect in enumerate(self.rectangles):
            if self.is_point_in_rect(pos, rect):
                self.selected_rect_index = i
                self.show_context_menu(event.GetPosition())
                return
        self.selected_rect_index = -1
        self.Refresh()

    def show_context_menu(self, pos):
        """Show context menu for the selected rectangle"""
        menu = wx.Menu()
        
        rename_item = menu.Append(wx.ID_ANY, "Rename Rectangle")
        points_item = menu.Append(wx.ID_ANY, "Set Max Points")
        menu.AppendSeparator()
        delete_item = menu.Append(wx.ID_ANY, "Delete Rectangle")
        
        self.Bind(wx.EVT_MENU, self.on_rename_rectangle, rename_item)
        self.Bind(wx.EVT_MENU, self.on_set_max_points, points_item)
        self.Bind(wx.EVT_MENU, self.on_delete_rectangle, delete_item)
        
        self.PopupMenu(menu, pos)
        menu.Destroy()

    def on_rename_rectangle(self, event):
        """Rename the selected rectangle"""
        if self.selected_rect_index >= 0:
            current_name = self.rectangle_names[self.selected_rect_index]
            dlg = wx.TextEntryDialog(self, 'Enter new name for this region:', 'Rename Region', current_name)
            if dlg.ShowModal() == wx.ID_OK:
                new_name = dlg.GetValue().strip()
                if new_name:
                    self.rectangle_names[self.selected_rect_index] = new_name
                    # Update the plot tab title
                    self.main_frame.plot_panel.update_tab_title(self.selected_rect_index, new_name)
            dlg.Destroy()

    def on_set_max_points(self, event):
        """Set max points for the selected rectangle"""
        if self.selected_rect_index >= 0:
            # Get current setting for this rectangle or global default
            current_points = (self.rectangle_max_points[self.selected_rect_index] 
                            if self.selected_rect_index < len(self.rectangle_max_points) 
                            else self.main_frame.MAX_POINTS)
            
            # Create dialog
            dlg = wx.Dialog(self, title="Set Max Points", size=(350, 200))
            panel = wx.Panel(dlg)
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Add explanation
            text = wx.StaticText(panel, label="Set maximum points for this rectangle:")
            sizer.Add(text, 0, wx.ALL, 10)
            
            # Points setting
            h_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(panel, label="Max Points:")
            spin_ctrl = wx.SpinCtrl(panel, value=str(current_points if current_points > 0 else 3000), 
                                   min=0, max=100000)
            h_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            h_sizer.Add(spin_ctrl, 1, wx.ALL, 5)
            sizer.Add(h_sizer, 0, wx.EXPAND | wx.ALL, 5)
            
            # Use actual points checkbox
            use_actual_cb = wx.CheckBox(panel, label="Use actual points (0 = all pixels)")
            use_actual_cb.SetValue(current_points == 0)
            if current_points == 0:
                spin_ctrl.Enable(False)
            sizer.Add(use_actual_cb, 0, wx.ALL, 10)
            
            # Buttons
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            use_global_btn = wx.Button(panel, wx.ID_ANY, "Use Global Setting")
            ok_btn = wx.Button(panel, wx.ID_OK, "OK")
            cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
            btn_sizer.Add(use_global_btn, 0, wx.ALL, 5)
            btn_sizer.AddStretchSpacer()
            btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
            btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
            sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
            
            panel.SetSizer(sizer)
            
            # Event handlers
            def on_use_actual(event):
                enabled = not use_actual_cb.GetValue()
                spin_ctrl.Enable(enabled)
                if not enabled:
                    spin_ctrl.SetValue(0)
            
            def on_use_global(event):
                dlg.EndModal(wx.ID_APPLY)
            
            use_actual_cb.Bind(wx.EVT_CHECKBOX, on_use_actual)
            use_global_btn.Bind(wx.EVT_BUTTON, on_use_global)
            
            # Show dialog
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                new_points = spin_ctrl.GetValue() if not use_actual_cb.GetValue() else 0
                # Ensure the list is long enough
                while len(self.rectangle_max_points) <= self.selected_rect_index:
                    self.rectangle_max_points.append(self.main_frame.MAX_POINTS)
                self.rectangle_max_points[self.selected_rect_index] = new_points
                # Refresh the plot with new settings
                self.analyze_rectangle(self.selected_rect_index)
            elif result == wx.ID_APPLY:  # Use global setting
                # Remove individual setting (use global)
                if self.selected_rect_index < len(self.rectangle_max_points):
                    self.rectangle_max_points[self.selected_rect_index] = -1  # -1 means use global
                # Refresh the plot with global settings
                self.analyze_rectangle(self.selected_rect_index)
            
            dlg.Destroy()

    def on_delete_rectangle(self, event):
        """Delete the selected rectangle"""
        if self.selected_rect_index >= 0:
            # Remove from plot panel first
            self.main_frame.remove_plot(self.selected_rect_index)
            
            # Remove the rectangle from all lists
            self.rectangles.pop(self.selected_rect_index)
            self.original_rectangles.pop(self.selected_rect_index)
            self.rectangle_names.pop(self.selected_rect_index)
            
            # Remove max points setting if exists
            if self.selected_rect_index < len(self.rectangle_max_points):
                self.rectangle_max_points.pop(self.selected_rect_index)
            
            # Update plot indices for remaining rectangles
            self.main_frame.plot_panel.reindex_plots(self.selected_rect_index)
            
            # Reset selection
            self.selected_rect_index = -1
            
            # Update display
            self.Refresh()

    def analyze_rectangle(self, rect_index):
        """Analyze the gray scale distribution in the selected rectangle"""
        if self.gray_img is None or rect_index >= len(self.original_rectangles):
            return

        # Convert display coordinates to original image coordinates
        original_rect = self.original_rectangles[rect_index]
        x, y, w, h = [int(v) for v in original_rect]

        # Get max points setting for this rectangle
        max_points = self.main_frame.MAX_POINTS  # Default to global setting
        if rect_index < len(self.rectangle_max_points):
            individual_setting = self.rectangle_max_points[rect_index]
            if individual_setting >= 0:  # -1 means use global
                max_points = individual_setting

        # Extract the region
        region = self.gray_img[y:y+h, x:x+w]
        if region.size > 0:
            # Calculate statistics
            data = region.ravel()
            rect_name = self.rectangle_names[rect_index] if rect_index < len(self.rectangle_names) else f"region_{rect_index + 1}"
            region_data = {
                'region': region,
                'data': data,
                'mean': np.mean(data),
                'std_dev': np.std(data),
                'median': np.median(data),
                'min': np.min(data),
                'max': np.max(data),
                'coordinates': (x, y, w, h),
                'area': w * h,
                'name': rect_name,
                'max_points': max_points  # Pass the max points setting
            }
            
            # Update plot
            self.main_frame.update_plot(region_data, rect_index)

    def scale_rect_to_original(self, display_rect):
        """Convert rectangle coordinates from display scale to original image scale"""
        if self.original_img is None:
            return display_rect
            
        x_offset, y_offset, display_width, display_height = self.get_image_bounds()
        orig_height, orig_width = self.original_img.shape[:2]
        
        # Calculate scaling factors
        scale_x = orig_width / display_width
        scale_y = orig_height / display_height
        
        # Convert coordinates relative to image
        x = (display_rect[0] - x_offset) * scale_x
        y = (display_rect[1] - y_offset) * scale_y
        w = display_rect[2] * scale_x
        h = display_rect[3] * scale_y
        
        # Ensure coordinates are within image bounds
        x = max(0, min(x, orig_width - w))
        y = max(0, min(y, orig_height - h))
        
        return (int(x), int(y), int(w), int(h))

    def scale_rect_to_display(self, original_rect):
        """Convert original image coordinates to display scale"""
        if self.original_img is None:
            return original_rect
            
        x_offset, y_offset, display_width, display_height = self.get_image_bounds()
        orig_height, orig_width = self.original_img.shape[:2]
        
        # Calculate scaling factors
        scale_x = display_width / orig_width
        scale_y = display_height / orig_height
        
        # Convert from image coordinates to display coordinates
        x = original_rect[0] * scale_x + x_offset
        y = original_rect[1] * scale_y + y_offset
        w = original_rect[2] * scale_x
        h = original_rect[3] * scale_y
        
        return (int(x), int(y), int(w), int(h))

    def on_size(self, event=None):
        """Handle size events"""
        if event:
            event.Skip()
        self.update_display()

    def load_image(self, path):
        """Load and process an image"""
        self.original_img = cv2.imread(path)
        if self.original_img is None:
            raise Exception("Failed to load image")
        
        self.gray_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2GRAY)
        self.rectangles = []
        self.original_rectangles = []
        self.rectangle_names = []
        self.rectangle_max_points = []
        self.selected_rect_index = -1
        
        self.update_display()

    def update_display(self):
        """Update the display with the current image"""
        if self.original_img is not None:
            try:
                panel_size = self.GetSize()
                if panel_size.width <= 0 or panel_size.height <= 0:
                    return
                    
                self.scaled_img, scale_factor, x_offset, y_offset = self.main_frame.image_handler.scale_image(
                    self.original_img, panel_size.width, panel_size.height)
                
                if self.scaled_img is not None:
                    height, width = self.scaled_img.shape[:2]
                    rgb_img = cv2.cvtColor(self.scaled_img, cv2.COLOR_BGR2RGB)
                    self.current_image = wx.Bitmap.FromBuffer(width, height, rgb_img)
                    self.current_scale = scale_factor
                    self.x_offset = x_offset
                    self.y_offset = y_offset
                    
                    # Update rectangle display positions
                    new_rectangles = []
                    for rect in self.original_rectangles:
                        new_rectangles.append(self.scale_rect_to_display(rect))
                    self.rectangles = new_rectangles
                    
                    self.Refresh()
            except Exception as e:
                wx.MessageBox(f'Error updating display: {str(e)}', 'Error',
                            wx.OK | wx.ICON_ERROR)

    def save_results(self, pathname):
        """Save analysis results"""
        if self.original_img is None:
            raise Exception("No image loaded")
            
        # Create a copy of the original image
        result_img = self.original_img.copy()
        
        # Draw rectangles and names on the image
        for i, rect in enumerate(self.original_rectangles):
            x, y, w, h = [int(v) for v in rect]
            
            # Draw rectangle
            cv2.rectangle(result_img, (x, y), (x + w, y + h), self.rect_color, 2)
            
            # Draw rectangle name if available
            if i < len(self.rectangle_names):
                rect_name = self.rectangle_names[i]
                
                # Set font parameters
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                font_thickness = 2
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(rect_name, font, font_scale, font_thickness)
                
                # Calculate text position (top-left corner of rectangle with some padding)
                text_x = x + 5
                text_y = y + text_height + 5
                
                # Make sure text doesn't go outside image bounds
                if text_y > result_img.shape[0]:
                    text_y = y - 5
                if text_x + text_width > result_img.shape[1]:
                    text_x = result_img.shape[1] - text_width - 5
                
                # Draw text background rectangle for better visibility
                bg_x1 = text_x - 3
                bg_y1 = text_y - text_height - 3
                bg_x2 = text_x + text_width + 3
                bg_y2 = text_y + baseline + 3
                
                # Ensure background rectangle is within image bounds
                bg_x1 = max(0, bg_x1)
                bg_y1 = max(0, bg_y1)
                bg_x2 = min(result_img.shape[1], bg_x2)
                bg_y2 = min(result_img.shape[0], bg_y2)
                
                # Draw semi-transparent background
                overlay = result_img.copy()
                cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, result_img, 0.3, 0, result_img)
                
                # Draw the text in white
                cv2.putText(result_img, rect_name, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)
        
        # Save the image with rectangles and names
        cv2.imwrite(pathname, result_img)
        
        # Save the grayscale version
        gray_pathname = pathname.rsplit('.', 1)[0] + '_gray.png'
        cv2.imwrite(gray_pathname, self.gray_img)

    def export_to_excel(self, pathname):
        """Export analysis results to Excel"""
        if not self.rectangles or self.gray_img is None:
            raise Exception("No regions selected")
        
        # Show progress for large datasets
        total_pixels = sum(rect[2] * rect[3] for rect in self.original_rectangles)
        show_progress = total_pixels > 100000 or len(self.rectangles) > 5
        
        progress_dialog = None
        if show_progress:
            progress_dialog = wx.ProgressDialog(
                "Preparing Export",
                "Collecting region data...",
                maximum=100,
                parent=self.GetTopLevelParent(),
                style=wx.PD_AUTO_HIDE | wx.PD_APP_MODAL
            )
            progress_dialog.Update(10, "Processing regions...")
            wx.GetApp().Yield()
            
        # Collect data from all regions
        regions_data = []
        for i, rect in enumerate(self.original_rectangles):
            if progress_dialog:
                progress = 10 + int((i / len(self.original_rectangles)) * 70)
                progress_dialog.Update(progress, f"Processing region {i+1} of {len(self.original_rectangles)}...")
                wx.GetApp().Yield()
                
            x, y, w, h = [int(v) for v in rect]
            
            # Ensure coordinates are within bounds
            x = max(0, min(x, self.gray_img.shape[1] - 1))
            y = max(0, min(y, self.gray_img.shape[0] - 1))
            w = min(w, self.gray_img.shape[1] - x)
            h = min(h, self.gray_img.shape[0] - y)
            
            region = self.gray_img[y:y+h, x:x+w]
            
            rect_name = self.rectangle_names[i] if i < len(self.rectangle_names) else f"region_{i + 1}"
            
            # Get max points setting for this rectangle
            max_points = self.main_frame.MAX_POINTS  # Default to global setting
            if i < len(self.rectangle_max_points):
                individual_setting = self.rectangle_max_points[i]
                if individual_setting >= 0:  # -1 means use global
                    max_points = individual_setting
            
            region_data = {
                'region_id': i + 1,
                'name': rect_name,
                'region': region,
                'coordinates': (x, y, w, h),
                'max_points': max_points
            }
            regions_data.append(region_data)
        
        if progress_dialog:
            progress_dialog.Update(80, "Starting Excel export...")
            wx.GetApp().Yield()
        
        # Export to Excel
        try:
            exporter = ExcelExporter(self.gray_img)
            exporter.export_to_excel(regions_data, pathname)
        finally:
            if progress_dialog:
                progress_dialog.Destroy()

    def constrain_point_to_image(self, point):
        """Constrain a point to be within the image bounds"""
        x_offset, y_offset, width, height = self.get_image_bounds()
        x = max(x_offset, min(point.x, x_offset + width))
        y = max(y_offset, min(point.y, y_offset + height))
        return wx.Point(x, y)

    def highlight_rectangle(self, rect_index):
        """Highlight a specific rectangle"""
        if 0 <= rect_index < len(self.rectangles):
            self.selected_rect_index = rect_index
            self.Refresh()

    def on_key_down(self, event):
        """Handle key down events"""
        key_code = event.GetKeyCode()
        
        if key_code == wx.WXK_DELETE and self.selected_rect_index >= 0:
            # Delete selected rectangle
            self.on_delete_rectangle(None)
        elif key_code == wx.WXK_ESCAPE:
            # Deselect rectangle
            self.selected_rect_index = -1
            self.Refresh()
        else:
            event.Skip()
