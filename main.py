import math
import time

import pyautogui
from smooth import SmoothMouse

# PyAutoGUI waits 0.1 seconds after every call by default. Disable that global
# pause because moveTo is called for every camera frame.
pyautogui.PAUSE = 0


class MouseController:
    # Converts MediaPipe hand landmarks into operating-system mouse actions.
    def __init__(self):
        self.last_click_time = 0
        # Prevents repeated right-clicks while the same gesture is held.
        self.click_cooldown = 0.5
        # A short pinch becomes a click; holding it for this duration starts a drag.
        self.drag_delay = 0.5
        self.pinch_started_at = None
        self.is_dragging = False

        # Defines the inactive border around the camera frame for mouse mapping.
        self.frame_reduction = 100
        # Maximum fingertip distance, in camera pixels, for a pinch gesture.
        self.click_threshold = 25

        # SmoothMouse reduces sudden cursor jumps between frames.
        self.mouse_smoother = SmoothMouse(smoothening=3)
        self.screen_width, self.screen_height = pyautogui.size()
        self.navigation_active = True
        self.last_thumb_gesture_time = 0
        self.thumb_gesture_cooldown = 1.0

    def handle_hand(self, hand_landmarks, frame_width, frame_height):
        # Scene calls this whenever MediaPipe detects a hand. Landmark positions
        # are normalized, so they are converted to camera-frame pixels below.
        current_time = time.time()
        landmarks = hand_landmarks.landmark

        thumb_state = self.detect_thumb_state(landmarks)
        if (
            thumb_state is not None
            and current_time - self.last_thumb_gesture_time > self.thumb_gesture_cooldown
        ):
            self.last_thumb_gesture_time = current_time

            if thumb_state == "up":
                self.navigation_active = True
                return "Mouse navigation active"

            self.navigation_active = False
            self.release_mouse()
            return "Mouse navigation inactive"

        if not self.navigation_active:
            return None

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

        # A short thumb-index pinch is a click. The mouse button is held only
        # after the pinch lasts long enough to deliberately start a drag.
        thumb_index_distance = math.hypot(
            index_x - thumb_x,
            index_y - thumb_y,
        )

        if thumb_index_distance < self.click_threshold:
            if self.pinch_started_at is None:
                self.pinch_started_at = current_time
            elif (
                not self.is_dragging
                and current_time - self.pinch_started_at >= self.drag_delay
            ):
                pyautogui.mouseDown()
                self.is_dragging = True

        elif self.pinch_started_at is not None:
            if self.is_dragging:
                pyautogui.mouseUp()
            else:
                pyautogui.click()

            self.pinch_started_at = None
            self.is_dragging = False
            self.last_click_time = current_time

        # Pinching thumb and middle finger performs a right-click. The cooldown
        # prevents repeated clicks on every camera frame.
        thumb_middle_distance = math.hypot(
            middle_x - thumb_x,
            middle_y - thumb_y,
        )

        if (
            thumb_middle_distance < self.click_threshold
            and self.pinch_started_at is None
            and not self.is_dragging
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
        return None

    def detect_thumb_state(self, landmarks):
        # Treat a vertical thumb with folded fingers as thumbs up/down.
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]

        finger_pairs = (
            (8, 6),
            (12, 10),
            (16, 14),
            (20, 18),
        )
        folded_fingers = sum(
            1 for tip_index, pip_index in finger_pairs
            if landmarks[tip_index].y > landmarks[pip_index].y
        )

        if folded_fingers < 3:
            return None

        vertical_thumb = abs(thumb_tip.y - thumb_mcp.y) > abs(thumb_tip.x - thumb_mcp.x) # check if the thumb is vertical
        if not vertical_thumb:
            return None

        if thumb_tip.y < thumb_ip.y < thumb_mcp.y and thumb_tip.y < wrist.y:
            return "up"

        if thumb_tip.y > thumb_ip.y > thumb_mcp.y and thumb_tip.y > wrist.y:
            return "down"

        return None

    def release_mouse(self):
        # Safety method used when tracking is lost or the camera closes. It
        # cancels a pending click and ensures a drag never remains pressed.
        if self.is_dragging:
            pyautogui.mouseUp()

        self.pinch_started_at = None
        self.is_dragging = False
