from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button

# Initialize controllers
keyboard = KeyboardController()
mouse = MouseController()

def get_key(key_name):
    """Convert key name to actual key command"""
    special_keys = {
        "left": Key.left,
        "right": Key.right,
        "down": Key.down,
        "space": Key.space,
        "shift": Key.shift,
        "up": Key.up
    }

    mouse_buttons = {
        "left_click": Button.left,
        "right_click": Button.right,
        "middle_click": Button.middle
    }

    if key_name in mouse_buttons:
        return mouse_buttons[key_name]
    return special_keys.get(key_name.lower(), key_name)

def move_mouse(direction, amount=10):
    """Move the mouse cursor in the specified direction"""
    current_pos = mouse.position
    x, y = current_pos

    if direction == "left":
        mouse.position = (x - amount, y)
    elif direction == "right":
        mouse.position = (x + amount, y)
    elif direction == "up":
        mouse.position = (x, y - amount)
    elif direction == "down":
        mouse.position = (x, y + amount)

def handle_input_action(action_key, action_type):
    """Handle keyboard and mouse input actions"""
    if action_key.endswith("_click"):
        if action_type == "press":
            mouse.press(get_key(action_key))
        else:
            mouse.release(get_key(action_key))
    elif action_key.startswith("mouse_"):
        direction = action_key.split("_")[1]
        move_mouse(direction)
    else:
        key = get_key(action_key)
        if action_type == "press":
            keyboard.press(key)
            if action_type != "hold":  # For non-hold actions, release immediately
                keyboard.release(key)