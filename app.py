import tkinter as tk

from components.scene import Scene
from main import MouseController

# Create the main Tkinter window.
root = tk.Tk()

# This class contains all hand-gesture-to-mouse behavior.
mouse_controller = MouseController()

# Scene owns the GUI and camera. MouseController methods are passed as
# callbacks so Scene does not need to know anything about mouse behavior.
scene = Scene(
    root=root,
    on_hand_detected=mouse_controller.handle_hand,
    on_tracking_lost=mouse_controller.release_mouse,
)

# Start Tkinter's event loop and keep the window responsive.
root.mainloop()
