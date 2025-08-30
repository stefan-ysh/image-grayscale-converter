class RectangleHandler:
    @staticmethod
    def is_point_in_rect(x, y, rect_pos, rect_size=None):
        """Check if a point is inside a rectangle
        Args:
            x, y: Point coordinates
            rect_pos: Tuple (x, y) for top-left corner
            rect_size: Optional tuple (w, h) for width and height. If None, rect_pos should be (x, y, w, h)
        """
        if rect_size is None:
            rx, ry, w, h = rect_pos
        else:
            rx, ry = rect_pos
            w, h = rect_size
        
        return rx <= x <= rx + w and ry <= y <= ry + h

    @staticmethod
    def is_point_near_corner(x, y, rect, threshold=10):
        """Check if a point is near any corner of a rectangle
        Args:
            x, y: Point coordinates
            rect: Tuple (x, y, w, h) defining the rectangle
            threshold: Distance threshold to consider "near"
        """
        rx, ry, w, h = rect
        corners = [
            (rx, ry),            # Top-left
            (rx + w, ry),        # Top-right
            (rx, ry + h),        # Bottom-left
            (rx + w, ry + h)     # Bottom-right
        ]
        return any(abs(x - cx) < threshold and abs(y - cy) < threshold for cx, cy in corners)

    @staticmethod
    def get_resize_direction(x, y, rect, threshold=10):
        """Get which corner the point is near to, if any
        Args:
            x, y: Point coordinates
            rect: Tuple (x, y, w, h) defining the rectangle
            threshold: Distance threshold to consider "near"
        """
        rx, ry, w, h = rect
        corners = {
            "top_left": (rx, ry),
            "top_right": (rx + w, ry),
            "bottom_left": (rx, ry + h),
            "bottom_right": (rx + w, ry + h)
        }
        
        for direction, (cx, cy) in corners.items():
            if abs(x - cx) < threshold and abs(y - cy) < threshold:
                return direction
        return None

    @staticmethod
    def resize_rectangle(rect, x, y, direction, min_size=(20, 20)):
        """Resize a rectangle by dragging one of its corners
        Args:
            rect: Tuple (x, y, w, h) defining the current rectangle
            x, y: New position of the dragged corner
            direction: Which corner is being dragged ("top_left", "top_right", etc.)
            min_size: Tuple (min_w, min_h) for minimum allowed size
        Returns:
            Tuple (x, y, w, h) for the resized rectangle
        """
        rx, ry, w, h = rect
        min_w, min_h = min_size
        
        if direction == "top_left":
            new_w = rx + w - x
            new_h = ry + h - y
            if new_w >= min_w and new_h >= min_h:
                return (x, y, new_w, new_h)
        
        elif direction == "top_right":
            new_w = x - rx
            new_h = ry + h - y
            if new_w >= min_w and new_h >= min_h:
                return (rx, y, new_w, new_h)
        
        elif direction == "bottom_left":
            new_w = rx + w - x
            new_h = y - ry
            if new_w >= min_w and new_h >= min_h:
                return (x, ry, new_w, new_h)
        
        elif direction == "bottom_right":
            new_w = x - rx
            new_h = y - ry
            if new_w >= min_w and new_h >= min_h:
                return (rx, ry, new_w, new_h)
        
        # If we get here, either the direction was invalid or the new size would be too small
        return rect

    @staticmethod
    def normalize_rectangle(rect):
        """Ensure rectangle has positive width and height
        Args:
            rect: Tuple (x, y, w, h) defining the rectangle
        Returns:
            Normalized rectangle tuple (x, y, w, h) with positive width and height
        """
        x, y, w, h = rect
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h
        return (x, y, w, h)
