"""
utils/video_utils.py — Frame Extraction Module
Extracts the middle frame from a video file using OpenCV.
"""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def extract_frame(video_path: str) -> np.ndarray:
    """
    Extract a single representative frame from the **middle** of a video.

    Args:
        video_path: Absolute or relative path to the video file.

    Returns:
        A BGR numpy array (H × W × 3) representing the extracted frame.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the video cannot be opened or yields no usable frame.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.debug("Opening video: %s", video_path)
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise ValueError(f"OpenCV could not open video: {video_path}")

    try:
        total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0

        if total_frames <= 0:
            # Some containers don't report frame count — fall back to first frame
            logger.warning("Frame count unknown; using first available frame.")
            target_frame = 0
        else:
            # Seek to the middle frame for a representative sample
            target_frame = total_frames // 2

        logger.debug(
            "Video info: total_frames=%d  fps=%.1f  target_frame=%d",
            total_frames, fps, target_frame,
        )

        # ── Seek ──────────────────────────────────────────────────────────────
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()

        # If seek failed (some codecs don't support it), try reading sequentially
        if not ret or frame is None:
            logger.warning("Seek failed; reading frames sequentially to frame %d", target_frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            for _ in range(target_frame + 1):
                ret, frame = cap.read()
                if not ret:
                    break

        if not ret or frame is None or frame.size == 0:
            raise ValueError("Could not read any usable frame from the video.")

        logger.info(
            "Extracted frame %d — shape: %s  dtype: %s",
            target_frame, frame.shape, frame.dtype,
        )
        return frame

    finally:
        cap.release()
        logger.debug("VideoCapture released.")
