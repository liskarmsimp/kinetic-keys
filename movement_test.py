import cv2
import mediapipe as mp
from pynput.keyboard import Controller, Key
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController
import math
import json
import time
from collections import defaultdict

# Initialize MediaPipe Pose and controllers
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils
keyboard = Controller()
mouse = MouseController()

# Initialize timing and state tracking
last_action_time = defaultdict(float)  # Store last action time for each movement
cooldown = 0.3  # 0.3 seconds cooldown
previous_states = defaultdict(bool)  # Store previous states of movements

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

def calculate_head_tilt(landmarks):
    # Get the coordinates of the ears (using the more reliable ear points)
    left_ear = landmarks[4]  # Left ear (landmark index 4)
    right_ear = landmarks[1]  # Right ear (landmark index 1)

    # Calculate the difference in y and x coordinates
    delta_y = right_ear.y - left_ear.y
    delta_x = right_ear.x - left_ear.x

    # Calculate the angle in radians
    angle_radians = math.atan2(delta_y, delta_x)

    # Convert radians to degrees
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees

def check_head_tilt(landmarks, neutral_angle):
    angle_difference = calculate_head_tilt(landmarks)
    if abs(angle_difference) > threshold:
        if angle_difference > 0:
            return neutral_angle, "tiltLeft"
        elif angle_difference < 0:
            return neutral_angle, "tiltRight"
    return neutral_angle, "tiltCenter"

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

def can_perform_action(action_name, current_time, bypass_cooldown=False):
    """Check if enough time has passed to perform the action again"""
    if bypass_cooldown:  # For space bar (jump)
        return True
    time_since_last = current_time - last_action_time[action_name]
    return time_since_last >= cooldown

def detect_knee_clap(landmarks):
    """Detect when knees come close together"""
    left_knee = landmarks[25]
    right_knee = landmarks[26]
    knee_distance = abs(left_knee.x - right_knee.x)
    return knee_distance < 0.05

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
    current_time = time.time()

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

                # Add vertical position check for more reliable detection
                is_bent = left_arm_angle < 60 and landmarks[15].y > landmarks[11].y
                was_bent = previous_states["left_arm_bend"]

                if is_bent and not was_bent and can_perform_action("left_arm_bend", current_time):
                    if keybindings["left_arm_bend"].endswith("_click"):
                        mouse.press(get_key(keybindings["left_arm_bend"]))
                        print(f"Mouse click: {keybindings['left_arm_bend']}")
                    elif keybindings["left_arm_bend"].startswith("mouse_"):
                        direction = keybindings["left_arm_bend"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        left_key = get_key(keybindings["left_arm_bend"])
                        keyboard.press(left_key)
                        print(f"Left arm: {keybindings['left_arm_bend']}")
                    last_action_time["left_arm_bend"] = current_time
                elif not is_bent and was_bent:
                    if keybindings["left_arm_bend"].endswith("_click"):
                        mouse.release(get_key(keybindings["left_arm_bend"]))
                    elif not keybindings["left_arm_bend"].startswith("mouse_"):
                        left_key = get_key(keybindings["left_arm_bend"])
                        keyboard.release(left_key)

                previous_states["left_arm_bend"] = is_bent
            except (AttributeError, IndexError):
                pass

        # Right arm bend detection
        if toggles.get("right_arm_bend", False):
            try:
                right_shoulder = [landmarks[12].x, landmarks[12].y]
                right_elbow = [landmarks[14].x, landmarks[14].y]
                right_wrist = [landmarks[16].x, landmarks[16].y]
                right_arm_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

                # Add vertical position check for more reliable detection
                is_bent = right_arm_angle < 60 and landmarks[16].y > landmarks[12].y
                was_bent = previous_states["right_arm_bend"]

                if is_bent and not was_bent and can_perform_action("right_arm_bend", current_time):
                    if keybindings["right_arm_bend"].endswith("_click"):
                        mouse.press(get_key(keybindings["right_arm_bend"]))
                        print(f"Mouse click: {keybindings['right_arm_bend']}")
                    elif keybindings["right_arm_bend"].startswith("mouse_"):
                        direction = keybindings["right_arm_bend"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        right_key = get_key(keybindings["right_arm_bend"])
                        keyboard.press(right_key)
                        print(f"Right arm: {keybindings['right_arm_bend']}")
                    last_action_time["right_arm_bend"] = current_time
                elif not is_bent and was_bent:
                    if keybindings["right_arm_bend"].endswith("_click"):
                        mouse.release(get_key(keybindings["right_arm_bend"]))
                    elif not keybindings["right_arm_bend"].startswith("mouse_"):
                        right_key = get_key(keybindings["right_arm_bend"])
                        keyboard.release(right_key)

                previous_states["right_arm_bend"] = is_bent
            except (AttributeError, IndexError):
                pass

        # Head tilt detection using the old, more reliable method
        if toggles.get("tilt_left", False) or toggles.get("tilt_right", False):
            try:
                neutral_angle, tilt_status = check_head_tilt(landmarks, neutral_angle)
                was_tilted_left = previous_states["tilt_left"]
                was_tilted_right = previous_states["tilt_right"]

                if tilt_status == "tiltLeft" and not was_tilted_left and can_perform_action("tilt_left", current_time):
                    if toggles.get("tilt_left", False):
                        if keybindings["tilt_left"].endswith("_click"):
                            mouse.press(get_key(keybindings["tilt_left"]))
                        elif keybindings["tilt_left"].startswith("mouse_"):
                            direction = keybindings["tilt_left"].split("_")[1]
                            move_mouse(direction)
                        else:
                            keyboard.press(get_key(keybindings["tilt_left"]))
                            keyboard.release(get_key(keybindings["tilt_left"]))
                        last_action_time["tilt_left"] = current_time
                        print("Tilt left")
                elif tilt_status == "tiltRight" and not was_tilted_right and can_perform_action("tilt_right", current_time):
                    if toggles.get("tilt_right", False):
                        if keybindings["tilt_right"].endswith("_click"):
                            mouse.press(get_key(keybindings["tilt_right"]))
                        elif keybindings["tilt_right"].startswith("mouse_"):
                            direction = keybindings["tilt_right"].split("_")[1]
                            move_mouse(direction)
                        else:
                            keyboard.press(get_key(keybindings["tilt_right"]))
                            keyboard.release(get_key(keybindings["tilt_right"]))
                        last_action_time["tilt_right"] = current_time
                        print("Tilt right")
                elif tilt_status == "tiltCenter":
                    if was_tilted_left and toggles.get("tilt_left", False):
                        if keybindings["tilt_left"].endswith("_click"):
                            mouse.release(get_key(keybindings["tilt_left"]))
                    if was_tilted_right and toggles.get("tilt_right", False):
                        if keybindings["tilt_right"].endswith("_click"):
                            mouse.release(get_key(keybindings["tilt_right"]))

                previous_states["tilt_left"] = (tilt_status == "tiltLeft")
                previous_states["tilt_right"] = (tilt_status == "tiltRight")

                # Display tilt status on frame
                cv2.putText(frame, tilt_status, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except (AttributeError, IndexError):
                pass

        # Arm raised detection
        if toggles.get("arm_raised", False):
            try:
                left_shoulder = landmarks[11]
                left_wrist = landmarks[15]
                right_shoulder = landmarks[12]
                right_wrist = landmarks[16]

                is_raised = get_arm_vertical_position(left_shoulder, left_wrist) or get_arm_vertical_position(right_shoulder, right_wrist)
                was_raised = previous_states["arm_raised"]

                if is_raised and not was_raised and can_perform_action("arm_raised", current_time):
                    if keybindings["arm_raised"].endswith("_click"):
                        mouse.press(get_key(keybindings["arm_raised"]))
                        print(f"Mouse click: {keybindings['arm_raised']}")
                    elif keybindings["arm_raised"].startswith("mouse_"):
                        direction = keybindings["arm_raised"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    last_action_time["arm_raised"] = current_time
                elif not is_raised and was_raised:
                    if keybindings["arm_raised"].endswith("_click"):
                        mouse.release(get_key(keybindings["arm_raised"]))

                previous_states["arm_raised"] = is_raised
            except (AttributeError, IndexError):
                pass

        # Arm lowered detection
        if toggles.get("arm_lowered", False):
            try:
                left_shoulder = landmarks[11]
                left_wrist = landmarks[15]
                right_shoulder = landmarks[12]
                right_wrist = landmarks[16]

                is_lowered = not get_arm_vertical_position(left_shoulder, left_wrist) or not get_arm_vertical_position(right_shoulder, right_wrist)
                was_lowered = previous_states["arm_lowered"]

                if is_lowered and not was_lowered and can_perform_action("arm_lowered", current_time):
                    if keybindings["arm_lowered"].endswith("_click"):
                        mouse.press(get_key(keybindings["arm_lowered"]))
                        print(f"Mouse click: {keybindings['arm_lowered']}")
                    elif keybindings["arm_lowered"].startswith("mouse_"):
                        direction = keybindings["arm_lowered"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    last_action_time["arm_lowered"] = current_time
                elif not is_lowered and was_lowered:
                    if keybindings["arm_lowered"].endswith("_click"):
                        mouse.release(get_key(keybindings["arm_lowered"]))

                previous_states["arm_lowered"] = is_lowered
            except (AttributeError, IndexError):
                pass

        # Jump detection
        if toggles.get("jump", False):
            try:
                right_hip_y = landmarks[24].y
                right_knee_y = landmarks[26].y

                is_jumping = right_knee_y < right_hip_y
                was_jumping = spaceLock

                if is_jumping and not was_jumping and can_perform_action("jump", current_time, bypass_cooldown=True):
                    spaceLock = True
                    if keybindings["jump"].endswith("_click"):
                        mouse.press(get_key(keybindings["jump"]))
                        print(f"Mouse click: {keybindings['jump']}")
                    elif keybindings["jump"].startswith("mouse_"):
                        direction = keybindings["jump"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        jump_key = get_key(keybindings["jump"])
                        keyboard.press(jump_key)
                        keyboard.release(jump_key)
                        print(f"Jump: {keybindings['jump']}")
                    last_action_time["jump"] = current_time
                elif not is_jumping and was_jumping:
                    spaceLock = False
                    if keybindings["jump"].endswith("_click"):
                        mouse.release(get_key(keybindings["jump"]))
            except (AttributeError, IndexError):
                pass

        # Squat detection
        if toggles.get("squat", False):
            try:
                left_hip_y = landmarks[23].y
                left_knee_y = landmarks[25].y

                is_squatting = left_knee_y < left_hip_y
                was_squatting = previous_states["squat"]

                if is_squatting and not was_squatting and can_perform_action("squat", current_time):
                    if keybindings["squat"].endswith("_click"):
                        mouse.press(get_key(keybindings["squat"]))
                        print(f"Mouse click: {keybindings['squat']}")
                    elif keybindings["squat"].startswith("mouse_"):
                        direction = keybindings["squat"].split("_")[1]
                        move_mouse(direction)
                        print(f"Mouse {direction}")
                    else:
                        squat_key = get_key(keybindings["squat"])
                        keyboard.press(squat_key)
                        keyboard.release(squat_key)
                        print(f"Squat: {keybindings['squat']}")
                    last_action_time["squat"] = current_time
                elif not is_squatting and was_squatting:
                    if keybindings["squat"].endswith("_click"):
                        mouse.release(get_key(keybindings["squat"]))

                previous_states["squat"] = is_squatting
            except (AttributeError, IndexError):
                pass

        # Knee clap detection
        if toggles.get("knee_clap", False):
            try:
                if detect_knee_clap(landmarks) and can_perform_action("knee_clap", current_time):
                    if keybindings["knee_clap"].endswith("_click"):
                        mouse.press(get_key(keybindings["knee_clap"]))
                        mouse.release(get_key(keybindings["knee_clap"]))
                    elif keybindings["knee_clap"].startswith("mouse_"):
                        direction = keybindings["knee_clap"].split("_")[1]
                        move_mouse(direction)
                    else:
                        knee_clap_key = get_key(keybindings["knee_clap"])
                        keyboard.press(knee_clap_key)
                        keyboard.release(knee_clap_key)
                    last_action_time["knee_clap"] = current_time
                    print(f"Knee clap: {keybindings['knee_clap']}")
            except (AttributeError, IndexError):
                pass

    cv2.imshow("MediaPipe Pose", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()