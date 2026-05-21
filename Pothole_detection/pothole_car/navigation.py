FRAME_WIDTH = 320

def decide_action(detected, x, y):

    if not detected:
        return "F"

    # LEFT SIDE
    if x < FRAME_WIDTH // 3:
        return "R"

    # RIGHT SIDE
    elif x > 2 * FRAME_WIDTH // 3:
        return "L"

    # CENTER
    else:
        return "S"
