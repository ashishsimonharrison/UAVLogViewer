"""
chatbot.py
──────────
Provider-agnostic LLM wrapper + prompt builder for telemetry Q&A.
"""
from __future__ import annotations
import pandas as pd
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any


# --------------------------------------------------------------------------- #
#   Provider abstraction
# --------------------------------------------------------------------------- #

PROVIDER = os.getenv("LLM_PROVIDER", "mistral").lower()   # "mistral" | "openai"


# --- right after PROVIDER is defined -------------------------------
def _ctx_role() -> str:
    """
    Role to use for non-dialogue context messages.
    Mistral => 'system'   (because it rejects 'tool')
    OpenAI  => 'tool'     (works fine and keeps messages distinct)
    """
    return "system" if PROVIDER == "mistral" else "tool"


if PROVIDER == "mistral":
    from mistralai.client import MistralClient
    _client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
    _MODEL  = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

elif PROVIDER == "openai":
    import openai
    openai.api_key = os.environ["OPENAI_API_KEY"]
    _MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    _client = openai
else:
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {PROVIDER}")


def _chat_api(messages: List[dict], temperature: float = 0.2) -> str:
    """
    Thin shim so the rest of the code is agnostic to provider.
    """
    if PROVIDER == "mistral":
        resp = _client.chat(model=_MODEL, messages=messages,
                            temperature=temperature)
        return resp.choices[0].message.content

    else:  # openai
        resp = _client.ChatCompletion.create(model=_MODEL,
                                             messages=messages,
                                             temperature=temperature)
        return resp.choices[0].message.content


# --------------------------------------------------------------------------- #
#   Dataclasses
# --------------------------------------------------------------------------- #

@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


# --------------------------------------------------------------------------- #
#   Prompt building helpers
# --------------------------------------------------------------------------- #

_SYSTEM_BLURB = (
    "You are an expert ArduPilot flight-data analyst.\n"
    "- Answer user questions using the telemetry summary and (if provided) the sensor snapshot.\n"
    "- You may consult and cite the official ArduPilot log-message documentation when helpful: https://ardupilot.org/plane/docs/logmessages.html\n"
    "- For anomaly detection, look for sudden changes in altitude (>20 m/s), battery-voltage drops (>0.3 V/s), EKF variances > 1.0, or RC failsafe flags, unless a different threshold appears more appropriate.\n"
    "- Always include the exact timestamp(s) you used in your reasoning.\n"
    "- If information is missing, ask a follow-up question instead of guessing."
)



def fetch_relevant_slice(ts_path: str, question: str) -> str:
    """
    Opens the parquet time-series and returns a down-sampled (≤ 200 rows)
    markdown table covering only the signals that look relevant to the question.
    """
    # Naïve keyword → column mapping
    column_map = {
        "alt": ["alt", "altitude", "height"],
        "volt": ["volt", "voltage", "battery"],
        "temp": ["temp", "temperature"],
        "gps_fix": ["gps", "fix"],
    }

    question_l = question.lower()

    cols = ["t"]  # always include time
    for col, keywords in column_map.items():
        if any(k in question_l for k in keywords):
            cols.append(col)

    if len(cols) == 1:              # no obvious column, just provide all
        cols = ["t", "alt", "volt", "temp", "gps_fix"]

    df = pd.read_parquet(ts_path, columns=list(dict.fromkeys(cols)))  # dedupe
    # Downsample to ≤ 200 rows
    if len(df) > 200:
        df = df.iloc[:: max(1, len(df) // 200)]

    return df.to_markdown(index=False)


_SNAP_PATTERN = re.compile(
    r"\b(when|time|over|duration|drop|trend|anomal(y|ies)|plot)\b", re.I
)

def _need_snapshot(q: str) -> bool:
    return bool(_SNAP_PATTERN.search(q))


def build_prompt(
    question: str,
    summary: dict,
    history: list[dict],
    ts_path: str,
) -> list[dict]:
    """
    Returns a list of message dicts ready for the chat completion API.
    Provider-aware: Mistral gets ONE mega-system message, OpenAI gets tool msgs.
    """
    # ---------- 1. decide if we need a sensor slice -------------------------
    snapshot_text = ""
    if _need_snapshot(question):
        snapshot_text = fetch_relevant_slice(ts_path, question)

    # ---------- 2. Build messages ------------------------------------------
    messages: list[ChatMessage] = []

    if PROVIDER == "mistral":
        # --- ONE big 'system' message with all context ---------------------
        sys_chunks = [
            _SYSTEM_BLURB,
            "FLIGHT-SUMMARY:\n" + json.dumps(summary),
        ]
        if snapshot_text:
            sys_chunks.append("SENSOR-SNAPSHOT:\n" + snapshot_text)

        messages.append(ChatMessage("system", "\n\n".join(sys_chunks)))

    else:  # OpenAI (or any provider that accepts 'tool')
        messages.extend([
            ChatMessage("system", _SYSTEM_BLURB),
            ChatMessage("tool",   "FLIGHT-SUMMARY:\n" + json.dumps(summary)),
        ])
        if snapshot_text:
            messages.append(ChatMessage("tool", "SENSOR-SNAPSHOT:\n" + snapshot_text))

    # --- 3. recent dialogue history ---------------------------------------
    for turn in history[-6:]:
        messages.append(ChatMessage("user",      turn["user"]))
        messages.append(ChatMessage("assistant", turn["assistant"]))

    # --- 4. user’s new question -------------------------------------------
    messages.append(ChatMessage("user", question))

    # --- 5. convert to plain dict list -------------------------------------
    return [m.to_dict() for m in messages]

# --------------------------------------------------------------------------- #
#   Public API
# --------------------------------------------------------------------------- #

def ask_llm(
    question: str,
    stats: Dict[str, Any],
    history: List[Dict[str, str]],
    ts_path: str,
) -> str:
    """
    High-level helper used by main.py.
    """
    prompt = build_prompt(question, stats, history, ts_path)
    return _chat_api(prompt)
