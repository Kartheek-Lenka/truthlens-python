"""
services/analyzer.py — Core Analysis Orchestrator
Routes frames through Gemini API (if key present) → local model (fallback).
Also measures CPU time and memory usage per analysis run.
"""

import logging
import time
from typing import Optional, TypedDict

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.gemini_service import analyze_with_gemini
from services.local_model import run_local_model
from utils.metrics import get_cpu_time, get_memory_usage

logger = logging.getLogger(__name__)


# ── Result Schema ──────────────────────────────────────────────────────────────

class AnalysisResult(TypedDict):
    isFake: bool
    confidence: int       # 0–100
    reasoning: str
    cpu_time: str         # e.g. "423.1 ms"
    memory: str           # e.g. "128.4 MB"
    engine: str           # "gemini" | "local" | "local_fallback"


# ── Orchestrator ───────────────────────────────────────────────────────────────

def analyze_frame(
    frame: np.ndarray,
    api_key: Optional[str] = None,
) -> AnalysisResult:
    """
    Analyze a single video frame for deepfake / AI-manipulation.

    Decision logic:
        1. If api_key is provided (non-empty) → attempt Gemini API analysis.
           - On success: return Gemini result.
           - On failure: log the error and fall back to local model.
        2. If no api_key → use local model directly (offline mode).

    Performance telemetry (CPU time, memory) is measured for every path.

    Args:
        frame:   BGR numpy array from extract_frame().
        api_key: Optional Gemini API key string.

    Returns:
        AnalysisResult dict — always populated, never raises.
    """
    start_time = time.perf_counter()
    engine: str = "local"

    logger.info(
        "Starting analysis — engine: %s",
        "gemini (primary)" if api_key else "local (offline)",
    )

    # ── Path A: Gemini API ─────────────────────────────────────────────────
    if api_key and api_key.strip():
        try:
            gemini_result = analyze_with_gemini(image=frame, api_key=api_key.strip())
            end_time = time.perf_counter()
            engine = "gemini"

            return AnalysisResult(
                isFake=gemini_result["isFake"],
                confidence=gemini_result["confidence"],
                reasoning=gemini_result["reasoning"],
                cpu_time=get_cpu_time(start_time, end_time),
                memory=get_memory_usage(),
                engine=engine,
            )

        except Exception as exc:
            logger.warning(
                "Gemini API failed (%s). Falling back to local model …", exc
            )
            engine = "local_fallback"
            # Reset timer so fallback latency is measured independently
            start_time = time.perf_counter()

    # ── Path B: Local model (offline / fallback) ───────────────────────────
    local_result = run_local_model(frame)
    end_time = time.perf_counter()

    return AnalysisResult(
        isFake=local_result["isFake"],
        confidence=local_result["confidence"],
        reasoning=local_result["reasoning"],
        cpu_time=get_cpu_time(start_time, end_time),
        memory=get_memory_usage(),
        engine=engine,
    )
