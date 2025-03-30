import time
from config import last_action_time, previous_states, COOLDOWN
from input_controller import handle_input_action
from movement_utils import (
    calculate_angle,
    get_arm_vertical_position,
    detect_knee_clap,
    check_head_tilt
)


def can_perform_action(action_name, current_time, bypass_cooldown=False):
    """Check if enough time has passed to perform the action again"""
    if bypass_cooldown:  # For space bar (jump)
        return True
    time_since_last = current_time - last_action_time[action_name]
    return time_since_last >= COOLDOWN


def handle_arm_movement(landmarks, side, keybindings, toggles):
    """Handle arm bend detection and actions"""
    try:
        if not toggles.get(f"{side}_arm_bend", False):
            return

        shoulder_idx = 11 if side == "left" else 12
        elbow_idx = 13 if side == "left" else 14
        wrist_idx = 15 if side == "left" else 16

        shoulder = [landmarks[shoulder_idx].x, landmarks[shoulder_idx].y]
        elbow = [landmarks[elbow_idx].x, landmarks[elbow_idx].y]
        wrist = [landmarks[wrist_idx].x, landmarks[wrist_idx].y]

        arm_angle = calculate_angle(shoulder, elbow, wrist)
        is_bent = arm_angle < 60 and landmarks[wrist_idx].y > landmarks[shoulder_idx].y
        was_bent = previous_states[f"{side}_arm_bend"]
        current_time = time.time()

        if is_bent and not was_bent and can_perform_action(f"{side}_arm_bend", current_time):
            handle_input_action(keybindings[f"{side}_arm_bend"], "press")
            last_action_time[f"{side}_arm_bend"] = current_time
        elif not is_bent and was_bent:
            handle_input_action(keybindings[f"{side}_arm_bend"], "release")

        previous_states[f"{side}_arm_bend"] = is_bent

    except (AttributeError, IndexError):
        pass


def handle_head_tilt(landmarks, keybindings, toggles, neutral_angle, current_time):
    """Handle head tilt detection and actions"""
    try:
        neutral_angle, tilt_status = check_head_tilt(landmarks, neutral_angle)
        was_tilted_left = previous_states["tilt_left"]
        was_tilted_right = previous_states["tilt_right"]

        if tilt_status == "tiltLeft" and not was_tilted_left:
            if toggles.get("tilt_left", False) and can_perform_action("tilt_left", current_time):
                handle_input_action(keybindings["tilt_left"], "press")
                last_action_time["tilt_left"] = current_time
        elif tilt_status == "tiltRight" and not was_tilted_right:
            if toggles.get("tilt_right", False) and can_perform_action("tilt_right", current_time):
                handle_input_action(keybindings["tilt_right"], "press")
                last_action_time["tilt_right"] = current_time
        elif tilt_status == "tiltCenter":
            if was_tilted_left:
                handle_input_action(keybindings["tilt_left"], "release")
            if was_tilted_right:
                handle_input_action(keybindings["tilt_right"], "release")

        previous_states["tilt_left"] = (tilt_status == "tiltLeft")
        previous_states["tilt_right"] = (tilt_status == "tiltRight")

        return neutral_angle, tilt_status
    except (AttributeError, IndexError):
        return neutral_angle, "tiltCenter"


def handle_vertical_movements(landmarks, keybindings, toggles, current_time):
    """Handle arm raised and lowered positions"""
    try:
        left_shoulder = landmarks[11]
        left_wrist = landmarks[15]
        right_shoulder = landmarks[12]
        right_wrist = landmarks[16]

        # Handle arm raised
        if toggles.get("arm_raised", False):
            is_raised = (
                    get_arm_vertical_position(left_shoulder, left_wrist) or
                    get_arm_vertical_position(right_shoulder, right_wrist)
            )
            was_raised = previous_states["arm_raised"]

            if is_raised and not was_raised and can_perform_action("arm_raised", current_time):
                handle_input_action(keybindings["arm_raised"], "press")
                last_action_time["arm_raised"] = current_time
            elif not is_raised and was_raised:
                handle_input_action(keybindings["arm_raised"], "release")

            previous_states["arm_raised"] = is_raised

        # Handle arm lowered
        if toggles.get("arm_lowered", False):
            is_lowered = (
                    not get_arm_vertical_position(left_shoulder, left_wrist) or
                    not get_arm_vertical_position(right_shoulder, right_wrist)
            )
            was_lowered = previous_states["arm_lowered"]

            if is_lowered and not was_lowered and can_perform_action("arm_lowered", current_time):
                handle_input_action(keybindings["arm_lowered"], "press")
                last_action_time["arm_lowered"] = current_time
            elif not is_lowered and was_lowered:
                handle_input_action(keybindings["arm_lowered"], "release")

            previous_states["arm_lowered"] = is_lowered

    except (AttributeError, IndexError):
        pass


def handle_jump(landmarks, keybindings, toggles, current_time):
    """Handle jump detection"""
    if not toggles.get("jump", False):
        return False

    try:
        right_hip_y = landmarks[24].y
        right_knee_y = landmarks[26].y

        is_jumping = right_knee_y < right_hip_y
        was_jumping = previous_states["jump"]

        if is_jumping and not was_jumping and can_perform_action("jump", current_time, bypass_cooldown=True):
            handle_input_action(keybindings["jump"], "press")
            last_action_time["jump"] = current_time
        elif not is_jumping and was_jumping:
            handle_input_action(keybindings["jump"], "release")

        previous_states["jump"] = is_jumping
        return is_jumping

    except (AttributeError, IndexError):
        return False


def handle_left_knee_raise(landmarks, keybindings, toggles, current_time):
    """Handle left knee raise detection"""
    if not toggles.get("left_knee_raise", False):  # Update toggle name
        return False

    try:
        left_hip_y = landmarks[23].y
        left_knee_y = landmarks[25].y

        is_raised = left_knee_y < left_hip_y  # Same logic as jump but for left side
        was_raised = previous_states["left_knee_raise"]  # Update state name

        if is_raised and not was_raised and can_perform_action("left_knee_raise", current_time):  # Update action name
            handle_input_action(keybindings["left_knee_raise"], "press")  # Update keybinding name
            last_action_time["left_knee_raise"] = current_time  # Update action name
        elif not is_raised and was_raised:
            handle_input_action(keybindings["left_knee_raise"], "release")  # Update keybinding name

        previous_states["left_knee_raise"] = is_raised  # Update state name
        return is_raised

    except (AttributeError, IndexError):
        return False


def handle_knee_clap(landmarks, keybindings, toggles, current_time):
    """Handle knee clap detection"""
    if not toggles.get("knee_clap", False):
        return False

    try:
        if detect_knee_clap(landmarks) and can_perform_action("knee_clap", current_time):
            handle_input_action(keybindings["knee_clap"], "press")
            last_action_time["knee_clap"] = current_time
            return True
    except (AttributeError, IndexError):
        pass

    return False
