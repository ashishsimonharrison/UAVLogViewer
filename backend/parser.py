"""
parser.py
──────────
Light-weight ArduPilot .bin log parser.

• Produces a one-shot flight “summary” (tiny JSON-serialisable dict)
• Writes a 1 Hz time-series parquet snapshot for on-demand deep dives
• Returns both so the rest of the stack can stay stateless
"""
from __future__ import annotations

import os
import uuid
import tempfile
from typing import Tuple, Dict, Any, List

import pandas as pd
from pymavlink import mavutil


# --------------------------------------------------------------------------- #
#   Public API
# --------------------------------------------------------------------------- #

def parse_bin(file_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Parameters
    ----------
    file_path : str
        Path to the uploaded .bin file.

    Returns
    -------
    summary : dict
        Key scalar metrics & event lists, small enough to send in every LLM call.
    parquet_path : str
        Absolute path of the on-disk 1 Hz parquet snapshot (Tier-B storage).
    """
    tmp_dir = tempfile.gettempdir()
    parquet_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.parquet")

    rows_ts: List[dict] = []
    events:   List[dict] = []

    # Use pymavlink to iterate once through the log
    mav = mavutil.mavlink_connection(file_path, dialect="ardupilotmega")

    # State for 1 Hz bucketing
    next_mark = 0.0                       # seconds
    have_start_time = False
    first_ts = last_ts = 0.0

    # Running max/min
    max_altitude = float("-inf")
    max_temp     = float("-inf")

    gps_fix_state = "UNKNOWN"
    first_gps_loss = None
    first_rc_loss  = None

    while True:
        msg = mav.recv_match(blocking=False)
        if msg is None:
            break                         # end-of-file

        t = getattr(msg, "_timestamp", None)
        if t is None:
            continue

        if not have_start_time:
            first_ts = t
            have_start_time = True
        last_ts = t

        msg_type = msg.get_type()

        # ------------------------------------------------------------------- #
        # Per-second snapshot (1 Hz)                                           #
        # ------------------------------------------------------------------- #
        if t >= next_mark:
            rows_ts.append({
                "t"      : t,
                "alt"    : getattr(msg, "Alt",  None),
                "volt"   : getattr(msg, "Volt", None),
                "temp"   : getattr(msg, "Temp", None),
                "gps_fix": gps_fix_state,
            })
            next_mark += 1.0

        # ------------------------------------------------------------------- #
        # Scalar stats & quick-flags                                          #
        # ------------------------------------------------------------------- #
        if hasattr(msg, "Alt"):
            max_altitude = max(max_altitude, msg.Alt)
        if hasattr(msg, "Temp"):
            max_temp = max(max_temp, msg.Temp)

        # ------------------------------------------------------------------- #
        # Event / error capture                                               #
        # ------------------------------------------------------------------- #
        if msg_type in ("ERR", "STATUSTEXT", "EV"):
            level = getattr(msg, "Severity", getattr(msg, "ECode", "INFO"))
            text  = getattr(msg, "Message", getattr(msg, "Text", ""))
            events.append({"t": t, "level": str(level), "text": text})

            # cheap heuristics for common flags
            txt_lower = text.lower()
            if "gps" in txt_lower and ("lost" in txt_lower or "no fix" in txt_lower):
                if first_gps_loss is None:
                    first_gps_loss = t
            if "rc" in txt_lower and "lost" in txt_lower:
                if first_rc_loss is None:
                    first_rc_loss = t

        # ------------------------------------------------------------------- #
        # GPS-FIX state machine (none / 2D / 3D)                              #
        # ------------------------------------------------------------------- #
        if msg_type == "GPS" and hasattr(msg, "Status"):
            gps_fix_state = str(msg.Status)

    # ----------------------------------------------------------------------- #
    # Persist Tier-B snapshot (pandas → parquet)                             #
    # ----------------------------------------------------------------------- #
    df = pd.DataFrame(rows_ts)
    df.to_parquet(parquet_path, index=False)

    # ----------------------------------------------------------------------- #
    # Build ultra-compact summary dict                                       #
    # ----------------------------------------------------------------------- #
    summary: Dict[str, Any] = {
        "max_altitude_m": None if max_altitude == float("-inf") else max_altitude,
        "max_batt_temp_c": None if max_temp == float("-inf") else max_temp,
        "flight_time_s": last_ts - first_ts,
        "first_gps_loss_s": first_gps_loss,
        "first_rc_loss_s" : first_rc_loss,
        # keep only CRITICAL / ERROR lines
        "critical_errors": [
            e for e in events if e["level"] in ("CRITICAL", "ERROR", "4", "5")
        ],
    }

    return summary, parquet_path
