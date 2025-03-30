import cv2
import time
from config import load_keybindings, load_toggles, CAMERA_INDEX
from pose_detection import PoseDetector
from movement_handlers import (
    handle_arm_movement,
    handle_head_tilt,
    handle_vertical_movements,
    handle_jump,
    handle_knee_clap,
    handle_left_knee_raise
)


def main():
    # Load configuration
    keybindings = load_keybindings()
    toggles = load_toggles()

    # Initialize camera and pose detection
    cap = cv2.VideoCapture(CAMERA_INDEX)
    pose_detector = PoseDetector()

    # Initialize state variables
    neutral_angle = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        results = pose_detector.process_frame(frame)
        current_time = time.time()

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Handle arm movements
            handle_arm_movement(landmarks, "left", keybindings, toggles)
            handle_arm_movement(landmarks, "right", keybindings, toggles)

            # Handle head tilt
            if toggles.get("tilt_left", False) or toggles.get("tilt_right", False):
                neutral_angle, tilt_status = handle_head_tilt(
                    landmarks,
                    keybindings,
                    toggles,
                    neutral_angle,
                    current_time
                )
                pose_detector.draw_status(frame, tilt_status)

            # Handle vertical arm positions
            handle_vertical_movements(
                landmarks,
                keybindings,
                toggles,
                current_time
            )

            # Handle jump, squat, and knee clap
            handle_jump(landmarks, keybindings, toggles, current_time)
            handle_left_knee_raise(landmarks, keybindings, toggles, current_time)
            handle_knee_clap(landmarks, keybindings, toggles, current_time)

        cv2.imshow("MediaPipe Pose", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
