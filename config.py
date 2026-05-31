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

# ── ML Model Configuration ────────────────────────────────────────────────────
# Local ML model for offline deepfake detection
MODEL_TYPE: str = "mobilenet_v3"  # Transfer learning model type
MODEL_SIZE: str = "mobile"  # "mobile" for speed, "standard" for accuracy
INFERENCE_TIMEOUT: int = 30  # seconds

# ── Frame Extraction ──────────────────────────────────────────────────────────
FRAME_JPEG_QUALITY: int = 90           # 0-100 — higher = better quality
FRAME_MAX_DIM: int = 1024              # Resize longest edge to this

# ── Detection Settings ─────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD: float = 0.5      # Threshold for fake classification (0-1)
MIN_CONFIDENCE_PERCENT: int = 40       # Minimum reporting confidence

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.path.join(os.path.dirname(__file__), "database", "truthlens.db")

# ── UI ─────────────────────────────────────────────────────────────────────────
APP_TITLE: str = "TruthLens 🔍"
APP_ICON: str = "🔍"
APP_DESCRIPTION: str = (
    "AI-powered deepfake & manipulated video detection — "
    "Offline ML-powered analysis using transfer learning (MobileNetV3)"
)
