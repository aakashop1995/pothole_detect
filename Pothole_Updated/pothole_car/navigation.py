import time

FRAME_WIDTH = 320

system_ready = True

# Recovery variables
recovery_mode = False
recovery_direction = None
recovery_start_time = 0

RECOVERY_DELAY = 3


def decide_action(detected, x, y):

    global recovery_mode
    global recovery_direction
    global recovery_start_time

    current_time = time.time()

    # =====================================
    # SAFETY
    # =====================================

    if not system_ready:
        return "S"

    # =====================================
    # RETURN TO ORIGINAL PATH
    # =====================================

    if recovery_mode:

        # Wait 3 seconds while moving forward
        if current_time - recovery_start_time < RECOVERY_DELAY:

            return "F"

        # Move opposite direction once
        recovery_mode = False

        if recovery_direction == "LEFT_RETURN":

            print("Returning LEFT")

            return "L"

        elif recovery_direction == "RIGHT_RETURN":

            print("Returning RIGHT")

            return "R"

    # =====================================
    # NO POTHOLE
    # =====================================

    if not detected:

        return "F"

    # =====================================
    # POTHOLE LEFT
    # Move RIGHT first
    # =====================================

    if x < FRAME_WIDTH // 3:

        print("Pothole LEFT -> Move RIGHT")

        recovery_mode = True
        recovery_direction = "LEFT_RETURN"
        recovery_start_time = current_time

        return "RR"

    # =====================================
    # POTHOLE RIGHT
    # Move LEFT first
    # =====================================

    elif x > 2 * FRAME_WIDTH // 3:

        print("Pothole RIGHT -> Move LEFT")

        recovery_mode = True
        recovery_direction = "RIGHT_RETURN"
        recovery_start_time = current_time

        return "RL"

    # =====================================
    # POTHOLE CENTER
    # =====================================

    else:

        print("Pothole CENTER")

        return "RC"
