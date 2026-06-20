import tkinter as tk

# define global colors (per button)
COLORS = {
    "danger": {
        "bg": "#dc2626",
        "activebackground": "#b91c1c",
    },
    "success": {
        "bg": "#16a34a",
        "activebackground": "#15803d",
    },
}


class Button(tk.Button):  # inherits from tk.Button
    def __init__(self, master, text, command, variant="danger"):

        style = COLORS[variant]

        super().__init__(  # call tk.button constructor
            master,
            text=text,
            command=command,
            bg=style["bg"],
            fg="white",
            activebackground=style["activebackground"],
            activeforeground="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            borderwidth=0,
        )

    def set_variant(self, variant):

        style = COLORS[variant]
        self.config(bg=style["bg"], activebackground=style["activebackground"])
