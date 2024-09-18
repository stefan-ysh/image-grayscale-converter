class RectangleHandler:
    @staticmethod
    def is_point_in_rect(x, y, start, end):
        return min(start[0], end[0]) <= x <= max(start[0], end[0]) and min(
            start[1], end[1]
        ) <= y <= max(start[1], end[1])

    @staticmethod
    def is_point_near_corner(x, y, start, end, threshold=10):
        corners = [start, (start[0], end[1]), end, (end[0], start[1])]
        return any(
            abs(x - cx) < threshold and abs(y - cy) < threshold for cx, cy in corners
        )

    @staticmethod
    def get_resize_direction(x, y, start, end, threshold=10):
        corners = {
            "top_left": start,
            "top_right": (end[0], start[1]),
            "bottom_left": (start[0], end[1]),
            "bottom_right": end,
        }
        for direction, (cx, cy) in corners.items():
            if abs(x - cx) < threshold and abs(y - cy) < threshold:
                return direction
        return None

    @staticmethod
    def resize_rectangle(start, end, x, y, direction, MIN_RECT_WIDTH, MIN_RECT_HEIGHT):
        new_start, new_end = list(start), list(end)
        if direction == "top_left":
            new_start = [x, y]
        elif direction == "top_right":
            new_start[1] = y
            new_end[0] = x
        elif direction == "bottom_left":
            new_start[0] = x
            new_end[1] = y
        elif direction == "bottom_right":
            new_end = [x, y]

        if (
            abs(new_end[0] - new_start[0]) < MIN_RECT_WIDTH
            or abs(new_end[1] - new_start[1]) < MIN_RECT_HEIGHT
        ):
            return start, end

        return tuple(new_start), tuple(new_end)
