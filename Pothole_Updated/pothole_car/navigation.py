FRAME_WIDTH = 320

system_ready = True

def decide_action(detected, x, y):

    # Safety check
    if not system_ready:
        return "S"

    # No pothole detected
    if not detected:
        return "F"

    # Pothole on LEFT side
    if x < FRAME_WIDTH // 3:

        # reverse + right
        return "RR"

    # Pothole on RIGHT side
    elif x > 2 * FRAME_WIDTH // 3:

        # reverse + left
        return "RL"

    # Pothole in CENTER
    else:

        # reverse + turn
        return "RC"
