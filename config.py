"""
config.py — TruthLens Global Configuration
All tuneable knobs and environment-variable lookups live here.
"""

import os
import logging

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Gemini API ─────────────────────────────────────────────────────────────────
# Set via environment variable:  GEMINI_API_KEY=<your_key>
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL: str = "gemini-2.5-flash-preview-05-20"  # latest fast model
GEMINI_TIMEOUT: int = 30  # seconds

# ── Frame Extraction ──────────────────────────────────────────────────────────
FRAME_JPEG_QUALITY: int = 90           # 0-100 — higher = better quality, larger payload
FRAME_MAX_DIM: int = 1024              # Resize longest edge to this before sending to Gemini

# ── Local Model Simulation ────────────────────────────────────────────────────
LOCAL_MODEL_MIN_LATENCY_MS: int = 300   # Simulate fast GPU inference
LOCAL_MODEL_MAX_LATENCY_MS: int = 1200  # Simulate slow CPU inference

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.path.join(os.path.dirname(__file__), "database", "truthlens.db")

# ── UI ─────────────────────────────────────────────────────────────────────────
APP_TITLE: str = "TruthLens 🔍"
APP_ICON: str = "🔍"
APP_DESCRIPTION: str = (
    "AI-powered deepfake & manipulated video detection — "
    "powered by MobileNetV3 simulation + Gemini 2.5 Flash"
)
