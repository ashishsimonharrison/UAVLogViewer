
"""
main.py
───────
FastAPI entry-point.
• /upload  – user posts a .bin file, gets a file_id back
• /chat/{file_id} – chat endpoint for that flight
"""
from __future__ import annotations

import io
import uuid
from typing import Dict, Any, List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from parser import parse_bin
from chatbot import ask_llm

# --------------------------------------------------------------------------- #
#   Globals
# --------------------------------------------------------------------------- #

_DB: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Flight-Aware Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
#   Routes
# --------------------------------------------------------------------------- #

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Accepts an ArduPilot .bin file and returns a file_id for future chat calls.
    """
    if not file.filename.endswith(".bin"):
        raise HTTPException(400, detail="File must have .bin extension")

    raw = await file.read()
    tmp_path = f"/tmp/{uuid.uuid4().hex}.bin"
    with open(tmp_path, "wb") as f:
        f.write(raw)

    # Parse once – might take a few seconds
    summary, ts_parquet = parse_bin(tmp_path)

    file_id = uuid.uuid4().hex
    _DB[file_id] = {
        "summary": summary,
        "timeseries_path": ts_parquet,
        "history": [],           # running dialogue
    }

    return JSONResponse({"file_id": file_id, "summary": summary})


@app.post("/chat/{file_id}")
async def chat(file_id: str, payload: Dict[str, str]):
    """
    Chat endpoint. Expects: {"q": "user question"}
    """
    if file_id not in _DB:
        raise HTTPException(404, detail="Unknown file_id")

    question = payload.get("q", "").strip()
    if not question:
        raise HTTPException(400, detail="Missing 'q' in payload")

    entry = _DB[file_id]
    answer = ask_llm(
        question=question,
        stats=entry["summary"],
        history=entry["history"],
        ts_path=entry["timeseries_path"],
    )

    entry["history"].append({"user": question, "assistant": answer})
    return JSONResponse({"answer": answer})
