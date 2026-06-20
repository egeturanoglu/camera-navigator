import math
import time

import pyautogui
from smooth import SmoothMouse


class MouseController:
    # Converts MediaPipe hand landmarks into operating-system mouse actions.
    def __init__(self):
        self.last_click_time = 0
        # Prevents repeated right-clicks while the same gesture is held.
        self.click_cooldown = 0.5
        # Tracks whether the program is currently holding the left mouse button.
        self.is_left_mouse_down = False

        # Defines the inactive border around the camera frame for mouse mapping.
        self.frame_reduction = 100
        # Maximum fingertip distance, in camera pixels, for a pinch gesture.
        self.click_threshold = 25

        # SmoothMouse reduces sudden cursor jumps between frames.
        self.mouse_smoother = SmoothMouse(smoothening=3)
        self.screen_width, self.screen_height = pyautogui.size()

    def handle_hand(self, hand_landmarks, frame_width, frame_height):
        # Scene calls this whenever MediaPipe detects a hand. Landmark positions
        # are normalized, so they are converted to camera-frame pixels below.
        current_time = time.time()
        landmarks = hand_landmarks.landmark

        # Landmark indexes: 8=index tip, 4=thumb tip, 12=middle-finger tip.
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]

        index_x = int(index_tip.x * frame_width)
        index_y = int(index_tip.y * frame_height)

        thumb_x = int(thumb_tip.x * frame_width)
        thumb_y = int(thumb_tip.y * frame_height)

        middle_x = int(middle_tip.x * frame_width)
        middle_y = int(middle_tip.y * frame_height)

        # Pinching thumb and index finger holds the left mouse button down.
        # Releasing the pinch releases the left mouse button.
        thumb_index_distance = math.hypot(
            index_x - thumb_x,
            index_y - thumb_y,
        )

        if thumb_index_distance < self.click_threshold:
            if not self.is_left_mouse_down:
                pyautogui.mouseDown()
                self.is_left_mouse_down = True

        elif self.is_left_mouse_down:
            pyautogui.mouseUp()
            self.is_left_mouse_down = False
            self.last_click_time = current_time

        # Pinching thumb and middle finger performs a right-click. The cooldown
        # prevents repeated clicks on every camera frame.
        thumb_middle_distance = math.hypot(
            middle_x - thumb_x,
            middle_y - thumb_y,
        )

        if (
            thumb_middle_distance < self.click_threshold
            and not self.is_left_mouse_down
            and current_time - self.last_click_time > self.click_cooldown
        ):
            pyautogui.rightClick()
            self.last_click_time = current_time

        # Map the index fingertip from the camera safe zone to screen coordinates.
        usable_width = max(1, frame_width - 2 * self.frame_reduction)
        usable_height = max(1, frame_height - 2 * self.frame_reduction)

        mouse_x = int(
            (index_x - self.frame_reduction) * self.screen_width / usable_width
        )
        mouse_y = int(
            (index_y - self.frame_reduction) * self.screen_height / usable_height
        )

        mouse_x = max(0, min(self.screen_width, mouse_x))
        mouse_y = max(0, min(self.screen_height, mouse_y))

        current_x, current_y = self.mouse_smoother.smooth(mouse_x, mouse_y)
        pyautogui.moveTo(current_x, current_y)

    def release_mouse(self):
        # Safety method used when tracking is lost or the camera closes. It
        # ensures the operating system never keeps the left button pressed.
        if self.is_left_mouse_down:
            pyautogui.mouseUp()
            self.is_left_mouse_down = False
