from collections import deque

from .config import SAMPLE_RATE, WINDOW_SECONDS

MAX_SAMPLES = int(WINDOW_SECONDS * SAMPLE_RATE)


def init_user_state():
    return {
        "window": deque(maxlen=MAX_SAMPLES),
        "state": "NORMAL",
        "last_fall_ts": None,
    }
