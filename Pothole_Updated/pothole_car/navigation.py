FRAME_WIDTH = 320

system_ready = False

def decide_action(detected, x, y):

    global system_ready

    # wait until first valid detection cycle
    if not system_ready:
        return "S"

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
