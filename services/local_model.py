"""
services/local_model.py — Local ML Model Integration [DEPRECATED]
This module is deprecated. Use services/ml_model.py instead.

The ml_model.py provides the primary offline deepfake detection using TensorFlow
and frequency/statistical analysis. This file is kept for backward compatibility.
"""

import logging
import numpy as np
from typing import TypedDict

logger = logging.getLogger(__name__)


class LocalModelResult(TypedDict):
    isFake: bool
    confidence: int           # 0–100
    reasoning: str


def run_local_model(frame: np.ndarray) -> LocalModelResult:
    """
    DEPRECATED: This function is kept for backward compatibility.
    Use services/ml_model.predict_deepfake() instead.
    
    Args:
        frame: BGR numpy array from extract_frame().

    Returns:
        LocalModelResult dict with isFake, confidence, and reasoning.
    """
    logger.debug("run_local_model() is deprecated. Use ml_model.predict_deepfake() instead.")
    
    try:
        from services.ml_model import predict_deepfake
        ml_result = predict_deepfake(frame)
        
        return LocalModelResult(
            isFake=ml_result["isFake"],
            confidence=ml_result["confidence"],
            reasoning=ml_result["reasoning"],
        )
    except Exception as e:
        logger.error("Local model failed: %s", e)
        return LocalModelResult(
            isFake=False,
            confidence=50,
            reasoning="Local analysis unavailable.",
        )
