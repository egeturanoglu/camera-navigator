class SmoothMouse:
    def __init__(self, smoothening=7):
        self.smoothening = smoothening
        # store previous coordinates
        self.prev_x = 0
        self.prev_y = 0

    def smooth(self, target_x, target_y):
        current_x = self.prev_x + (target_x - self.prev_x) / self.smoothening
        current_y = self.prev_y + (target_y - self.prev_y) / self.smoothening

        self.prev_x = current_x
        self.prev_y = current_y

        return current_x, current_y
