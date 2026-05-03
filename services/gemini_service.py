"""
services/gemini_service.py — Google Gemini API Integration
Sends a video frame to Gemini 2.5 Flash for advanced multimodal forensic analysis.

API Key: Set the environment variable GEMINI_API_KEY before running.
         Never hardcode secrets in source files.
"""

import base64
import json
import logging
import time
from pathlib import Path
from typing import Optional, TypedDict

import cv2
import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT, FRAME_JPEG_QUALITY, FRAME_MAX_DIM

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "gemini_prompt.txt"

def _load_prompt() -> str:
    """Load the system prompt from the prompts/ directory."""
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.warning("Prompt file not found at %s — using inline fallback.", _PROMPT_PATH)
        return (
            "Analyze this image for deepfake/AI-manipulation artifacts. "
            "Respond ONLY with JSON: {\"isFake\": bool, \"confidence\": int, \"reasoning\": string}"
        )


# ── Image helpers ─────────────────────────────────────────────────────────────

def _frame_to_base64(frame: np.ndarray, quality: int = FRAME_JPEG_QUALITY) -> str:
    """
    Convert a BGR numpy frame to a Base64-encoded JPEG string.

    Optionally resizes the frame so its longest side ≤ FRAME_MAX_DIM,
    reducing payload while preserving forensic detail.
    """
    h, w = frame.shape[:2]
    if max(h, w) > FRAME_MAX_DIM:
        scale = FRAME_MAX_DIM / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug("Frame resized to %dx%d for Gemini payload.", new_w, new_h)

    success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not success:
        raise ValueError("cv2.imencode failed — cannot convert frame to JPEG.")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


# ── Result Schema ──────────────────────────────────────────────────────────────

class GeminiResult(TypedDict):
    isFake: bool
    confidence: int
    reasoning: str


# ── Main API call ─────────────────────────────────────────────────────────────

def analyze_with_gemini(
    image: np.ndarray,
    api_key: Optional[str] = None,
) -> GeminiResult:
    """
    Send a frame to Gemini 2.5 Flash for deepfake forensic analysis.

    Args:
        image:   BGR numpy array (from extract_frame).
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.

    Returns:
        GeminiResult with isFake, confidence, reasoning.

    Raises:
        RuntimeError: If the API call fails and no fallback is available.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        raise RuntimeError(
            "No Gemini API key provided. "
            "Set the GEMINI_API_KEY environment variable or pass api_key= explicitly."
        )

    # Lazy import so the module loads fine even without google-generativeai installed
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai package is not installed. "
            "Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=key)

    prompt_text = _load_prompt()
    image_b64 = _frame_to_base64(image)

    # Build multipart content: text prompt + inline image
    model = genai.GenerativeModel(GEMINI_MODEL)

    logger.info("Sending frame to Gemini (%s) …", GEMINI_MODEL)
    start = time.perf_counter()

    try:
        response = model.generate_content(
            contents=[
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ],
            generation_config=genai.GenerationConfig(
                temperature=0.1,           # Low temp → deterministic forensic judgment
                max_output_tokens=512,
            ),
            request_options={"timeout": GEMINI_TIMEOUT},
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.error("Gemini API call failed after %.1fs: %s", elapsed, exc)
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    elapsed = time.perf_counter() - start
    logger.info("Gemini responded in %.2fs", elapsed)

    # ── Parse response ────────────────────────────────────────────────────
    raw_text = response.text.strip()
    logger.debug("Gemini raw response: %s", raw_text)

    # Strip markdown fences if the model adds them despite the prompt
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON: %s\nRaw: %s", exc, raw_text)
        raise RuntimeError(f"Gemini returned non-JSON output: {raw_text[:200]}") from exc

    # Normalise and validate fields
    result: GeminiResult = {
        "isFake": bool(data.get("isFake", False)),
        "confidence": max(0, min(100, int(data.get("confidence", 50)))),
        "reasoning": str(data.get("reasoning", "No reasoning provided.")),
    }

    logger.info(
        "Gemini result → isFake=%s  confidence=%d%%  reasoning=%s",
        result["isFake"], result["confidence"], result["reasoning"][:80],
    )
    return result
