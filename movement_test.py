import cv2
import mediapipe as mp
from pynput.keyboard import Controller, Key
import math

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils
keyboard = Controller()

cap = cv2.VideoCapture(1) 
neutral_angle = 0

threshold = 30 

tiltLock = False
spaceLock = False

def calculate_head_tilt(landmarks):
    left_ear = landmarks[4]
    right_ear = landmarks[1]

    delta_y = right_ear.y - left_ear.y
    delta_x = right_ear.x - left_ear.x

    angle_radians = math.atan2(delta_y, delta_x)

    angle_degrees = math.degrees(angle_radians)

    return angle_degrees

def detect_knee_clap(landmarks):

    left_knee = landmarks[25]
    right_knee = landmarks[26]

    knee_distance = abs(left_knee.x - right_knee.x)

    if knee_distance < 0.05:
        keyboard.press(Key.shift)
        keyboard.release(Key.shift)

def check_head_tilt(landmarks, neutral_angle):
    angle_difference = calculate_head_tilt(landmarks)
    if abs(angle_difference) > threshold:
        if angle_difference > 0:
            return neutral_angle,
        elif angle_difference < 0:
            return neutral_angle,
    else:
        return neutral_angle,

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
        left_shoulder = [landmarks[11].x, landmarks[11].y]
        left_elbow = [landmarks[13].x, landmarks[13].y]
        left_wrist = [landmarks[15].x, landmarks[15].y]
        left_arm_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

        if left_arm_angle < 60:
            keyboard.press(Key.left)
        else:
            keyboard.release(Key.left)

        right_shoulder = [landmarks[12].x, landmarks[12].y]
        right_elbow = [landmarks[14].x, landmarks[14].y]
        right_wrist = [landmarks[16].x, landmarks[16].y]
        right_arm_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

        if right_arm_angle < 60:
            keyboard.press(Key.right)
        else:
            keyboard.release(Key.right)

        cv2.putText(frame, tilt_status, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if tilt_status == "tiltLeft" and not tiltLock:
            tiltLock = True
            keyboard.press("z")
            keyboard.release("z")
        elif tilt_status == "tiltRight" and not tiltLock:
            tiltLock = True
            keyboard.press("x")
            keyboard.release("x")
        elif tilt_status == "tiltCenter" and tiltLock:
            tiltLock = False

        left_hip_y = landmarks[23].y
        right_hip_y = landmarks[24].y
        left_knee_y = landmarks[25].y
        right_knee_y = landmarks[26].y

        if right_knee_y < right_hip_y and not spaceLock:
            spaceLock = True
            keyboard.press(Key.space)
            keyboard.release(Key.space)
        elif right_knee_y > right_hip_y:
            spaceLock = False

        if left_knee_y < left_hip_y:
            keyboard.press(Key.down)
            keyboard.release(Key.down)

        detect_knee_clap(landmarks)
    cv2.imshow("Media Pipe Pose", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()