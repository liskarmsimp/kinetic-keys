import cv2
import mediapipe as mp
from pynput.keyboard import Controller, Key
import math
import json

# Initialize MediaPipe Pose and keyboard controller
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils
keyboard = Controller()

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
            "knee_clap": "shift"
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

# Load keybindings and toggles
keybindings = load_keybindings()
toggles = load_toggles()

cap = cv2.VideoCapture(1)  # Use camera index 1 (Mac's built-in webcam)
neutral_angle = 0  # This will store the neutral position's angle

# Set the tilt threshold
threshold = 30  # Degrees of tilt considered as significant

tiltLock = False
spaceLock = False

def calculate_head_tilt(landmarks):
    # Get the coordinates of the ears
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

def detect_knee_clap(landmarks):
    if not toggles["knee_clap"]:  # Skip if disabled
        return

    left_knee = landmarks[25]
    right_knee = landmarks[26]

    knee_distance = abs(left_knee.x - right_knee.x)

    if knee_distance < 0.05:
        key = get_key(keybindings["knee_clap"])
        keyboard.press(key)
        keyboard.release(key)
        print(f"Knee clap: {keybindings['knee_clap']}")

def check_head_tilt(landmarks, neutral_angle):
    angle_difference = calculate_head_tilt(landmarks)
    if abs(angle_difference) > threshold:
        if angle_difference > 0:
            return neutral_angle, "tiltLeft"
        elif angle_difference < 0:
            return neutral_angle, "tiltRight"
    else:
        return neutral_angle, "tiltCenter"

def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    return angle if angle <= 180 else 360 - angle

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = results.pose_landmarks.landmark

        neutral_angle, tilt_status = check_head_tilt(landmarks, neutral_angle)

        # Left arm bent
        if toggles["left_arm_bend"]:  # Only process if enabled
            left_shoulder = [landmarks[11].x, landmarks[11].y]
            left_elbow = [landmarks[13].x, landmarks[13].y]
            left_wrist = [landmarks[15].x, landmarks[15].y]
            left_arm_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

            left_key = get_key(keybindings["left_arm_bend"])
            if left_arm_angle < 60:
                keyboard.press(left_key)
                print(f"Left arm: {keybindings['left_arm_bend']}")
            else:
                keyboard.release(left_key)

        # Right arm bent
        if toggles["right_arm_bend"]:  # Only process if enabled
            right_shoulder = [landmarks[12].x, landmarks[12].y]
            right_elbow = [landmarks[14].x, landmarks[14].y]
            right_wrist = [landmarks[16].x, landmarks[16].y]
            right_arm_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            right_key = get_key(keybindings["right_arm_bend"])
            if right_arm_angle < 60:
                keyboard.press(right_key)
                print(f"Right arm: {keybindings['right_arm_bend']}")
            else:
                keyboard.release(right_key)

        cv2.putText(frame, tilt_status, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Head tilt controls
        if tilt_status == "tiltLeft" and not tiltLock and toggles["tilt_left"]:
            tiltLock = True
            tilt_left_key = get_key(keybindings["tilt_left"])
            keyboard.press(tilt_left_key)
            keyboard.release(tilt_left_key)
            print(f"Tilt left: {keybindings['tilt_left']}")
        elif tilt_status == "tiltRight" and not tiltLock and toggles["tilt_right"]:
            tiltLock = True
            tilt_right_key = get_key(keybindings["tilt_right"])
            keyboard.press(tilt_right_key)
            keyboard.release(tilt_right_key)
            print(f"Tilt right: {keybindings['tilt_right']}")
        elif tilt_status == "tiltCenter" and tiltLock:
            tiltLock = False

        # Jump and squat controls
        left_hip_y = landmarks[23].y
        right_hip_y = landmarks[24].y
        left_knee_y = landmarks[25].y
        right_knee_y = landmarks[26].y

        # Jump (right knee raised)
        if toggles["jump"]:  # Only process if enabled
            jump_key = get_key(keybindings["jump"])
            if right_knee_y < right_hip_y and not spaceLock:
                spaceLock = True
                keyboard.press(jump_key)
                keyboard.release(jump_key)
                print(f"Jump: {keybindings['jump']}")
            elif right_knee_y > right_hip_y:
                spaceLock = False

        # Squat (left knee bent)
        if toggles["squat"]:  # Only process if enabled
            squat_key = get_key(keybindings["squat"])
            if left_knee_y < left_hip_y:
                keyboard.press(squat_key)
                keyboard.release(squat_key)
                print(f"Squat: {keybindings['squat']}")

        detect_knee_clap(landmarks)

    cv2.imshow("MediaPipe Pose", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()