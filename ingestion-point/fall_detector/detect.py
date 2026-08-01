import math
import time

import numpy as np

from .config import *


def acc_magnitude(d):
    return math.sqrt(d["ax"] ** 2 + d["ay"] ** 2 + d["az"] ** 2)


def gyro_magnitude(d):
    return abs(d["gx"]) + abs(d["gy"]) + abs(d["gz"])


def detect_fall(user_state, sample):
    if user_state["last_fall_ts"]:
        if time.time() - user_state["last_fall_ts"] < COOLDOWN_SEC:
            return False
    window = user_state["window"]
    state = user_state["state"]

    acc = acc_magnitude(sample)
    gyro = gyro_magnitude(sample)
    elapsed = time.time() - user_state.get("state_start_ts", 0)
    if (
        (state == "FREE_FALL" and elapsed > 0.5)
        or (state == "IMPACT" and elapsed > 1.0)
        or (state == "POST_FALL" and elapsed > 3.0)
    ):
        user_state["state"] = "NORMAL"
    # NORMAL → FREE FALL
    if state == "NORMAL" and acc < FREE_FALL_ACC:
        print("FREE FALL detected")
        user_state["state"] = "FREE_FALL"
        user_state["state_start_ts"] = time.time()

    # FREE FALL → IMPACT
    elif state == "FREE_FALL" and acc > IMPACT_ACC:
        print("IMPACT detected")
        user_state["state"] = "IMPACT"
        user_state["state_start_ts"] = time.time()

    # IMPACT → POST FALL
    elif state == "IMPACT" and gyro > GYRO_ROTATION:
        print("POST FALL detected")
        user_state["state"] = "POST_FALL"
        user_state["state_start_ts"] = time.time()

    # POST FALL → CONFIRM
    elif state == "POST_FALL" and len(window) > 10:
        print("Checking inactivity...")
        acc_vals = [acc_magnitude(s) for s in window]
        if np.std(acc_vals) < INACTIVITY_STD:
            print("FALL CONFIRMED")
            user_state["state"] = "FALL_CONFIRMED"
            return True

    return False
