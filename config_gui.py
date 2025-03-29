import tkinter as tk
from tkinter import ttk
import json
import os


class KeyBindingGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Movement Controls Configuration")

        # Default keybindings
        self.default_bindings = {
            "left_arm_bend": "left",
            "right_arm_bend": "right",
            "tilt_left": "z",
            "tilt_right": "x",
            "jump": "space",
            "squat": "down",
            "knee_clap": "shift"
        }

        # Default toggle states (all enabled by default)
        self.default_toggles = {key: True for key in self.default_bindings.keys()}

        # Load existing config or use defaults
        self.current_bindings = self.load_config() or self.default_bindings.copy()
        self.current_toggles = self.load_toggles() or self.default_toggles.copy()

        self.create_widgets()

    def create_widgets(self):
        # Create and pack widgets for each movement
        movements = {
            "left_arm_bend": "Left Arm Bend",
            "right_arm_bend": "Right Arm Bend",
            "tilt_left": "Tilt Head Left",
            "tilt_right": "Tilt Head Right",
            "jump": "Jump (Right Knee Raise)",
            "squat": "Squat",
            "knee_clap": "Knee Clap"
        }

        for key, description in movements.items():
            frame = ttk.Frame(self.root, padding="5")
            frame.pack(fill=tk.X, padx=5, pady=2)

            # Label for the movement
            ttk.Label(frame, text=description).pack(side=tk.LEFT)

            # Entry for the keybinding
            entry = ttk.Entry(frame, width=10)
            entry.insert(0, self.current_bindings[key])
            entry.pack(side=tk.LEFT, padx=5)
            setattr(self, f"entry_{key}", entry)

            # Toggle button (Checkbutton) for enabling/disabling the action
            toggle_var = tk.BooleanVar(value=self.current_toggles[key])
            toggle_button = ttk.Checkbutton(
                frame,
                text="Enable",
                variable=toggle_var,
                onvalue=True,
                offvalue=False
            )
            toggle_button.pack(side=tk.RIGHT)
            setattr(self, f"toggle_{key}", toggle_var)

        # Save and Reset buttons
        button_frame = ttk.Frame(self.root, padding="5")
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side=tk.RIGHT, padx=5)

    def save_config(self):
        # Update current bindings and toggles from entries
        for key in self.default_bindings.keys():
            entry = getattr(self, f"entry_{key}")
            self.current_bindings[key] = entry.get()

            toggle_var = getattr(self, f"toggle_{key}")
            self.current_toggles[key] = toggle_var.get()

        # Save to file
        with open('keybindings.json', 'w') as f:
            json.dump(self.current_bindings, f, indent=4)

        with open('toggles.json', 'w') as f:
            json.dump(self.current_toggles, f, indent=4)

    def load_config(self):
        try:
            with open('keybindings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def load_toggles(self):
        try:
            with open('toggles.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def reset_to_defaults(self):
        # Reset all entries and toggles to default values
        for key, value in self.default_bindings.items():
            entry = getattr(self, f"entry_{key}")
            entry.delete(0, tk.END)
            entry.insert(0, value)

            toggle_var = getattr(self, f"toggle_{key}")
            toggle_var.set(self.default_toggles[key])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = KeyBindingGUI()
    app.run()