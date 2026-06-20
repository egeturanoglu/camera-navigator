import math
import time

import cv2
import mediapipe as mp
import pyautogui
from smooth import SmoothMouse

# click cooldown config
last_click_time = 0
click_cooldown = 0.5
is_left_mouse_down = False

cap = cv2.VideoCapture(0)
frame_reduction = 100  # safe zone

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7
)

mouse_smoother = SmoothMouse(
    smoothening=3
)  # create a SmoothMouse object with 7 degree.

while True:
    current_time = time.time()
    success, frame = (
        cap.read()
    )  # cap returns 2 values: 1 bool (success) and 1 numpy array (frame - actual video)

    if not success:
        print("Could not connect to camera")
        break

    frame = cv2.flip(frame, 1)  # flip the video on y-axis (noted with "1")

    rgb_frame = cv2.cvtColor(
        frame, cv2.COLOR_BGR2RGB
    )  # change BGR to RGB (OpenCV returns BGR, MediaPipe expects RGB)

    result = hands.process(rgb_frame)  # run detect hands

    h, w, c = frame.shape  # fetch dimensions of the video

    if result.multi_hand_landmarks:  # if there is a hand in the video
        for (
            hand_landmarks
        ) in result.multi_hand_landmarks:  # for every hand in the video
            mp_draw.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )  # draw landmarks on hand (skeleton)

            # assign fingers
            index_finger_tip = hand_landmarks.landmark[8]  # assign index finger
            thumb_tip = hand_landmarks.landmark[4]
            middle_finger_tip = hand_landmarks.landmark[12]
            ring_finger_tip = hand_landmarks.landmark[16]
            pinky_tip = hand_landmarks.landmark[20]

            # find the real pixel values by summing
            # index finger
            xi = int(index_finger_tip.x * w)
            yi = int(index_finger_tip.y * h)

            # thumb
            xt = int(thumb_tip.x * w)
            yt = int(thumb_tip.y * h)

            # middle finger
            xm = int(middle_finger_tip.x * w)
            ym = int(middle_finger_tip.y * h)

            # ring finger
            xr = int(ring_finger_tip.x * w)
            yr = int(ring_finger_tip.y * h)

            # pinky
            xp = int(pinky_tip.x * w)
            yp = int(pinky_tip.y * h)

            # for left-click logic
            thumb_index_distance = math.hypot(
                xi - xt, yi - yt
            )  # distance betweem index finger and the thumb
            click_threshold = 25

            if thumb_index_distance < click_threshold:
                if not is_left_mouse_down:
                    pyautogui.mouseDown()  # mouse down -> click left-button button don't let go.
                    is_left_mouse_down = True
            elif (
                is_left_mouse_down
            ):  # only applied when index finger and thumb isnt close to each others
                pyautogui.mouseUp()
                is_left_mouse_down = False
                last_click_time = current_time

            # for right-click logic
            thumb_middle_distance = math.hypot(
                xm - xt, ym - yt
            )  # distance betweem middle finger and the thumb

            if (
                thumb_middle_distance < click_threshold
                and not is_left_mouse_down
                and current_time - last_click_time > click_cooldown
            ):
                pyautogui.rightClick()
                last_click_time = current_time

            # for mouse control (index) smoothening:
            screen_w, screen_h = pyautogui.size()  # take actual pc screen size

            mouse_x = int((xi - frame_reduction) * screen_w / (w - 2 * frame_reduction))
            mouse_y = int((yi - frame_reduction) * screen_h / (h - 2 * frame_reduction))

            mouse_x = max(0, min(screen_w, mouse_x))
            mouse_y = max(0, min(screen_h, mouse_y))

            curr_x, curr_y = mouse_smoother.smooth(mouse_x, mouse_y)
            pyautogui.moveTo(curr_x, curr_y)  # actual mouse operation

            # draw circles at the finger tips
            # index
            cv2.circle(
                frame, (xi, yi), 12, (0, 255, 0), cv2.FILLED
            )  # draw a green circle at index finger tip

            # thumb
            cv2.circle(frame, (xt, yt), 12, (0, 255, 0), cv2.FILLED)

            # middle finger
            cv2.circle(frame, (xm, ym), 12, (0, 255, 0), cv2.FILLED)

            # ring finger
            cv2.circle(frame, (xr, yr), 12, (0, 255, 0), cv2.FILLED)

            # pinky
            cv2.circle(frame, (xp, yp), 12, (0, 255, 0), cv2.FILLED)

            cv2.putText(
                frame,
                f"Index Finger: {xi}, {yi}",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )  # put a text at the screen

    elif is_left_mouse_down:
        # Do not leave the OS mouse button pressed if hand tracking is lost.
        pyautogui.mouseUp()
        is_left_mouse_down = False

    cv2.imshow(
        "Hand Tracking", frame
    )  # imshow = imageshow, show the image on the computer screen.

    if cv2.waitKey(1) & 0xFF == ord("q"):  # press "q" to exit
        break

# cleanup
cap.release()
cv2.destroyAllWindows()
