"""
services/analyzer.py — Core Analysis Orchestrator
Routes frames through local ML model for offline deepfake detection.
Measures CPU time and memory usage per analysis run.
"""

import logging
import time
from typing import TypedDict

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.ml_model import predict_deepfake
from utils.metrics import get_cpu_time, get_memory_usage

logger = logging.getLogger(__name__)


# ── Result Schema ──────────────────────────────────────────────────────────────

class AnalysisResult(TypedDict):
    isFake: bool
    confidence: int       # 0–100
    reasoning: str
    cpu_time: str         # e.g. "423.1 ms"
    memory: str           # e.g. "128.4 MB"
    engine: str           # "ml_model"


# ── Orchestrator ───────────────────────────────────────────────────────────────

def analyze_frame(frame: np.ndarray) -> AnalysisResult:
    """
    Analyze a single video frame for deepfake / AI-manipulation.
    
    Uses local ML model for completely offline detection.
    No external API calls or dependencies.

    Performance telemetry (CPU time, memory) is measured for the analysis.

    Args:
        frame: BGR numpy array from extract_frame().

    Returns:
        AnalysisResult dict — always populated, never raises.
    """
    start_time = time.perf_counter()
    engine: str = "ml_model"

    logger.info("Starting analysis with local ML model (offline)")

    try:
        # ── ML Model Inference ─────────────────────────────────────────────
        ml_result = predict_deepfake(frame)
        end_time = time.perf_counter()

        logger.info(
            "Analysis complete — isFake: %s, confidence: %d%%",
            ml_result["isFake"],
            ml_result["confidence"],
        )

        return AnalysisResult(
            isFake=ml_result["isFake"],
            confidence=ml_result["confidence"],
            reasoning=ml_result["reasoning"],
            cpu_time=get_cpu_time(start_time, end_time),
            memory=get_memory_usage(),
            engine=engine,
        )

    except Exception as exc:
        logger.error("Analysis failed: %s", exc)
        end_time = time.perf_counter()
        
        return AnalysisResult(
            isFake=False,
            confidence=50,
            reasoning="Analysis encountered an error. Please try again.",
            cpu_time=get_cpu_time(start_time, end_time),
            memory=get_memory_usage(),
            engine=engine,
        )
