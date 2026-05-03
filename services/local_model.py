"""
services/local_model.py — Lightweight Local Deepfake Detection (Simulation)
Simulates a quantized MobileNetV3 + LSTM inference pipeline using heuristics.

NOTE: The run_local_model() function is the integration point.
      Replace the heuristic body with actual TFLite / PyTorch model inference
      when a trained checkpoint is available.
"""

import logging
import random
import time
from typing import TypedDict

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import LOCAL_MODEL_MIN_LATENCY_MS, LOCAL_MODEL_MAX_LATENCY_MS

logger = logging.getLogger(__name__)


# ── Result Schema ──────────────────────────────────────────────────────────────

class LocalModelResult(TypedDict):
    isFake: bool
    confidence: int           # 0–100
    reasoning: str


# ── Heuristic helpers ─────────────────────────────────────────────────────────

_FAKE_REASONS = [
    "GAN checkerboard pattern detected in frequency domain.",
    "Inconsistent noise texture around facial boundary region.",
    "Face resolution mismatch with background — possible upscale artifact.",
    "Unnatural pixel correlation at blending seam near jaw/hairline.",
    "Spectral anomaly indicative of generative upsampling (GAN fingerprint).",
    "Irregular JPEG blocking pattern inconsistent with camera sensor noise.",
]

_REAL_REASONS = [
    "Noise distribution consistent with natural camera sensor patterns.",
    "No detectable spectral anomalies in frequency domain analysis.",
    "Pixel correlations match expected JPEG compression artifacts.",
    "Face-background boundary shows natural blending — no seam detected.",
    "Lighting direction and skin texture globally coherent.",
    "No checkerboard or upsampling artifacts detected.",
]


def _compute_heuristic_score(frame: np.ndarray) -> tuple[bool, int]:
    """
    Lightweight heuristic: analyze variance across colour channels and
    pixel-level statistics that often differ between real and synthetic frames.

    This is a *simulation* of what a real MobileNetV3 + LSTM would compute.
    Replace with actual model.predict(preprocessed_tensor) call here.
    """
    # ── Simulate INT8 quantized inference latency ──────────────────────────
    simulated_ms = random.uniform(LOCAL_MODEL_MIN_LATENCY_MS, LOCAL_MODEL_MAX_LATENCY_MS)
    time.sleep(simulated_ms / 1000.0)

    # ── Heuristic: channel variance check ─────────────────────────────────
    # Real camera frames tend to have balanced variance across R, G, B.
    # GANs sometimes introduce subtle channel-specific artifacts.
    if frame is not None and frame.ndim == 3:
        ch_var = [np.var(frame[:, :, c].astype(np.float32)) for c in range(frame.shape[2])]
        var_ratio = max(ch_var) / (min(ch_var) + 1e-6)
        # Extreme ratios hint at GAN artifacts (loose threshold — real model does this better)
        heuristic_fake = var_ratio > 3.5
    else:
        heuristic_fake = False

    # ── Blend heuristic with randomness to simulate probabilistic output ───
    # (In production: replace this entire block with model logits)
    random_weight = random.random()
    if heuristic_fake:
        is_fake = random_weight > 0.25   # Heuristic fires → lean toward fake
        confidence = random.randint(72, 97)
    else:
        is_fake = random_weight > 0.70   # No heuristic → lean toward real
        confidence = random.randint(65, 94)

    return is_fake, confidence


# ── Public API ────────────────────────────────────────────────────────────────

def run_local_model(frame: np.ndarray) -> LocalModelResult:
    """
    Run the local (offline) deepfake detection pipeline on a single frame.

    Args:
        frame: BGR numpy array from extract_frame().

    Returns:
        LocalModelResult dict with isFake, confidence, and reasoning.

    Integration point:
        Replace _compute_heuristic_score() body with:
            preprocessed = preprocess_frame(frame)   # resize, normalize, to tensor
            logits = model(preprocessed)              # TFLite / PyTorch
            is_fake = logits[1] > 0.5
            confidence = int(max(logits) * 100)
    """
    logger.info("Running local model inference (simulated MobileNetV3 + LSTM) …")

    is_fake, confidence = _compute_heuristic_score(frame)
    reasoning = random.choice(_FAKE_REASONS if is_fake else _REAL_REASONS)

    result: LocalModelResult = {
        "isFake": is_fake,
        "confidence": confidence,
        "reasoning": f"[Local Model] {reasoning}",
    }

    logger.info(
        "Local model result → isFake=%s  confidence=%d%%",
        is_fake, confidence,
    )
    return result
