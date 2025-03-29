import cv2
import mediapipe as mp
from pynput.keyboard import Controller, Key
from pynput.mouse import Controller as MouseController
import math
import json

# Initialize MediaPipe Pose and controllers
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils
keyboard = Controller()
mouse = MouseController()

def load_keybindings():
    try:
        with open('keybindings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
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
    try:
        with open('toggles.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {key: True for key in load_keybindings().keys()}

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

def get_arm_vertical_position(shoulder, wrist):
    """
    Returns True if arm is raised (wrist above shoulder),
    False if arm is lowered (wrist below shoulder)
    """
    return wrist.y < shoulder.y

def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    return angle if angle <= 180 else 360 - angle

# Load keybindings and toggles
keybindings = load_keybindings()
toggles = load_toggles()

cap = cv2.VideoCapture(1)  # Use camera index 1 (Mac's built-in webcam)
neutral_angle = 0
threshold = 30
tiltLock = False
spaceLock = False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = results.pose_landmarks.landmark

                # Left arm bend detection
        if toggles.get("left_arm_bend", False):
            try:
                left_shoulder = [landmarks[11].x, landmarks[11].y]
                left_elbow = [landmarks[13].x, landmarks[13].y]
                left_wrist = [landmarks[15].x, landmarks[15].y]
                left_arm_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

                if left_arm_angle < 60:
                    if keybindings["left_arm_bend"].startswith("mouse_"):
                        # Extract direction from the keybinding (e.g., "mouse_left" -> "left")
                        direction = keybindings["left_arm_bend"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        left_key = get_key(keybindings["left_arm_bend"])
                        keyboard.press(left_key)
                        print(f"Left arm: {keybindings['left_arm_bend']}")
                else:
                    if not keybindings["left_arm_bend"].startswith("mouse_"):
                        left_key = get_key(keybindings["left_arm_bend"])
                        keyboard.release(left_key)
            except (AttributeError, IndexError):
                pass

        # Right arm bend detection
        if toggles.get("right_arm_bend", False):
            try:
                right_shoulder = [landmarks[12].x, landmarks[12].y]
                right_elbow = [landmarks[14].x, landmarks[14].y]
                right_wrist = [landmarks[16].x, landmarks[16].y]
                right_arm_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

                if right_arm_angle < 60:
                    if keybindings["right_arm_bend"].startswith("mouse_"):
                        direction = keybindings["right_arm_bend"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        right_key = get_key(keybindings["right_arm_bend"])
                        keyboard.press(right_key)
                        print(f"Right arm: {keybindings['right_arm_bend']}")
                else:
                    if not keybindings["right_arm_bend"].startswith("mouse_"):
                        right_key = get_key(keybindings["right_arm_bend"])
                        keyboard.release(right_key)
            except (AttributeError, IndexError):
                pass

        # Arm raised detection
        if toggles.get("arm_raised", False):
            try:
                left_shoulder = landmarks[11]
                left_wrist = landmarks[15]
                right_shoulder = landmarks[12]
                right_wrist = landmarks[16]
                
                if get_arm_vertical_position(left_shoulder, left_wrist) or get_arm_vertical_position(right_shoulder, right_wrist):
                    if keybindings["arm_raised"].startswith("mouse_"):
                        direction = keybindings["arm_raised"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
            except (AttributeError, IndexError):
                pass

        # Arm lowered detection
        if toggles.get("arm_lowered", False):
            try:
                left_shoulder = landmarks[11]
                left_wrist = landmarks[15]
                right_shoulder = landmarks[12]
                right_wrist = landmarks[16]
                
                if not get_arm_vertical_position(left_shoulder, left_wrist) or not get_arm_vertical_position(right_shoulder, right_wrist):
                    if keybindings["arm_lowered"].startswith("mouse_"):
                        direction = keybindings["arm_lowered"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
            except (AttributeError, IndexError):
                pass

        # Jump detection
        if toggles.get("jump", False):
            try:
                right_hip_y = landmarks[24].y
                right_knee_y = landmarks[26].y

                if right_knee_y < right_hip_y and not spaceLock:
                    spaceLock = True
                    if keybindings["jump"].startswith("mouse_"):
                        direction = keybindings["jump"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        jump_key = get_key(keybindings["jump"])
                        keyboard.press(jump_key)
                        keyboard.release(jump_key)
                        print(f"Jump: {keybindings['jump']}")
                elif right_knee_y > right_hip_y:
                    spaceLock = False
            except (AttributeError, IndexError):
                pass

        # Squat detection
        if toggles.get("squat", False):
            try:
                left_hip_y = landmarks[23].y
                left_knee_y = landmarks[25].y

                if left_knee_y < left_hip_y:
                    if keybindings["squat"].startswith("mouse_"):
                        direction = keybindings["squat"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        squat_key = get_key(keybindings["squat"])
                        keyboard.press(squat_key)
                        keyboard.release(squat_key)
                        print(f"Squat: {keybindings['squat']}")
            except (AttributeError, IndexError):
                pass

    cv2.imshow("MediaPipe Pose", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()