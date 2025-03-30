from collections import defaultdict
import json

# Global configuration
CAMERA_INDEX = 1  # Mac's built-in webcam
COOLDOWN = 0.3  # 0.3 seconds cooldown
HEAD_TILT_THRESHOLD = 30

# Initialize timing and state tracking
last_action_time = defaultdict(float)  # Store last action time for each movement
previous_states = defaultdict(bool)  # Store previous states of movements

def load_keybindings():
    """Load keybindings from file, uses the same format as config_gui.py"""
    try:
        with open('keybindings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Using the same defaults as config_gui.py
        return {
            "left_arm_bend": "left",
            "right_arm_bend": "right",
            "tilt_left": "z",
            "tilt_right": "x",
            "jump": "space",
            "squat": "down",
            "knee_clap": "shift",
            "arm_raised": "mouse_up",
            "arm_lowered": "mouse_down"
        }

def load_toggles():
    """Load movement toggles from file, uses the same format as config_gui.py"""
    try:
        with open('toggles.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default to all movements enabled, matching config_gui.py
        default_bindings = load_keybindings()
        return {key: True for key in default_bindings.keys()}