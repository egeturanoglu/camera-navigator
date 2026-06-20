import tkinter as tk
import threading

import cv2
import mediapipe as mp
from PIL import Image, ImageOps, ImageTk

from components.button import Button


class Scene:
    # Owns the Tkinter interface, camera lifecycle, and MediaPipe detection.
    # Mouse behavior is delegated to callbacks supplied by app.py.
    def __init__(self, root, on_hand_detected, on_tracking_lost):
        self.root = root
        # These callbacks keep GUI/camera responsibilities separate from mouse control.
        self.on_hand_detected = on_hand_detected
        self.on_tracking_lost = on_tracking_lost

        self.cap = None
        self.camera_active = False
        self.camera_starting = False
        self.is_closing = False
        self.preview_size = (800, 520)

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        self.root.title("Camera Navigator")
        self.root.geometry("900x700")
        self.root.configure(bg="#111827")
        # Run our cleanup method when the user closes the window.
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.title_label = tk.Label(
            root,
            text="Camera Navigator",
            bg="#111827",
            fg="white",
            font=("Arial", 20, "bold"),
        )
        self.title_label.pack(pady=(20, 10))

        # Keep a fixed-size preview area. Label width/height values become pixels
        # when an image is assigned, which previously shrank the camera to 80x28.
        self.preview_frame = tk.Frame(
            root,
            width=self.preview_size[0],
            height=self.preview_size[1],
            bg="#1f2937",
        )
        self.preview_frame.pack(padx=30, pady=10)
        self.preview_frame.pack_propagate(False)

        self.camera_label = tk.Label(
            self.preview_frame,
            text="Starting Camera...",
            bg="#1f2937",
            fg="#d1d5db",
            font=("Arial", 14),
        )
        self.camera_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.camera_button = Button(
            root,
            text="Close Camera",
            command=self.toggle_camera,
            variant="danger",
        )
        self.camera_button.pack(pady=(10, 20))

        self.start_camera()
        self.update_camera()

    def start_camera(self):
        # Opening a camera can take time, so do it on a background thread.
        if self.camera_active or self.camera_starting:
            return

        self.camera_starting = True
        self.camera_label.configure(image="", text="Loading camera...")
        self.camera_label.image = None
        self.camera_button.configure(state="disabled", text="Loading...")

        threading.Thread(target=self.open_camera_in_background, daemon=True).start()

    def open_camera_in_background(self):
        # DirectShow generally opens Windows cameras faster than the default backend.
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Fall back to OpenCV's default backend if DirectShow is unavailable.
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(0)

        try:
            self.root.after(0, self.finish_start_camera, cap)
        except tk.TclError:
            # The window was closed before the camera finished opening.
            cap.release()

    def finish_start_camera(self, cap):
        if self.is_closing:
            cap.release()
            return

        self.camera_starting = False

        # Check if the camera is opened successfully
        if not cap.isOpened():
            cap.release()  # Release the camera if it is not opened

            self.camera_label.configure(
                image="",
                text="Could not open camera.",
            )
            self.camera_button.configure(state="normal", text="Open Camera")
            self.camera_button.set_variant("success")
            return

        self.cap = cap
        self.camera_active = True
        self.camera_button.configure(state="normal", text="Close Camera")
        self.camera_button.set_variant("danger")

    def stop_camera(self, message="Camera Closed"):
        # Stop mouse interaction first, then release the camera resource safely.
        self.on_tracking_lost()

        # Release the camera if it is not None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.camera_active = False

        self.camera_label.configure(image="", text=message)
        self.camera_label.image = None

        self.camera_button.configure(state="normal", text="Open Camera")
        self.camera_button.set_variant("success")

    def toggle_camera(self):
        # Switch between the open and closed camera states.
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def update_camera(self):
        if self.is_closing:
            return

        # Read the frame if the camera is active and the cap is not None
        if self.camera_active and self.cap is not None:
            success, frame = self.cap.read()  # read the frame

            if not success:
                self.stop_camera("Something went wrong.")
            else:
                self.show_frame(frame)

        # Schedule the next frame without blocking Tkinter's GUI event loop.
        # This replaces a traditional while True camera loop.
        self.root.after(15, self.update_camera)

    def show_frame(self, frame):
        # Process one frame, notify MouseController, then render it in Tkinter.
        frame = cv2.flip(frame, 1)  # flip the frame horizontally

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to RGB
        result = self.hands.process(rgb_frame)  # process the frame

        height, width, _ = frame.shape  # get the frame dimensions

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

                # Send landmarks to MouseController through the callback.
                self.on_hand_detected(hand_landmarks, width, height)
        else:
            self.on_tracking_lost()

        # Convert OpenCV's BGR image to RGB because Pillow/Tkinter expects RGB.
        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to RGB
        image = Image.fromarray(display_frame)
        # Create a consistently large preview without stretching the camera image.
        # Empty areas are filled with the same dark color as the preview background.
        image = ImageOps.pad(
            image,
            self.preview_size,
            method=Image.Resampling.LANCZOS,
            color="#1f2937",
        )

        image_tk = ImageTk.PhotoImage(image=image)

        self.camera_label.configure(image=image_tk, text="")
        # Keep a reference or Python may garbage-collect the preview image.
        self.camera_label.image = image_tk

    def close_app(self):
        # Release mouse, camera, and MediaPipe resources before closing.
        self.is_closing = True
        self.stop_camera()
        self.hands.close()
        self.root.destroy()
