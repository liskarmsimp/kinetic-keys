import math
from config import HEAD_TILT_THRESHOLD

def calculate_angle(a, b, c):
    """Calculate angle between three points"""
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    return angle if angle <= 180 else 360 - angle

def calculate_head_tilt(landmarks):
    """Calculate head tilt angle"""
    left_ear = landmarks[4]  # Left ear (landmark index 4)
    right_ear = landmarks[1]  # Right ear (landmark index 1)

    delta_y = right_ear.y - left_ear.y
    delta_x = right_ear.x - left_ear.x

    angle_radians = math.atan2(delta_y, delta_x)
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees

def check_head_tilt(landmarks, neutral_angle):
    """Check head tilt direction"""
    angle_difference = calculate_head_tilt(landmarks)
    if abs(angle_difference) > HEAD_TILT_THRESHOLD:
        if angle_difference > 0:
            return neutral_angle, "tiltLeft"
        elif angle_difference < 0:
            return neutral_angle, "tiltRight"
    return neutral_angle, "tiltCenter"

def get_arm_vertical_position(shoulder, wrist):
    """Check if arm is raised above shoulder"""
    return wrist.y < shoulder.y

def detect_knee_clap(landmarks):
    """Detect when knees come close together"""
    left_knee = landmarks[25]
    right_knee = landmarks[26]
    knee_distance = abs(left_knee.x - right_knee.x)
    return knee_distance < 0.05