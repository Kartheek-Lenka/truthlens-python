"""
utils/metrics.py — Performance Metrics Module
CPU timing and memory usage helpers using time and psutil.
"""

import logging
import time
from typing import Tuple

import psutil

logger = logging.getLogger(__name__)


# ── Timing ─────────────────────────────────────────────────────────────────────

def start_timer() -> float:
    """Return current high-resolution time (seconds since epoch)."""
    return time.perf_counter()


def get_cpu_time(start: float, end: float) -> str:
    """
    Compute elapsed wall-clock time between two perf_counter snapshots.

    Args:
        start: Value from a previous start_timer() call.
        end:   Value from a later perf_counter() call.

    Returns:
        Human-readable string, e.g. "423.12 ms" or "1.23 s".
    """
    elapsed_ms = (end - start) * 1000.0
    if elapsed_ms < 1000:
        return f"{elapsed_ms:.1f} ms"
    return f"{elapsed_ms / 1000:.2f} s"


# ── Memory ─────────────────────────────────────────────────────────────────────

def get_memory_usage() -> str:
    """
    Return the current process's Resident Set Size (RSS) as a human-readable string.

    Uses psutil to query the actual OS-level memory allocation for this Python
    process — much more accurate than sys.getsizeof for total footprint.

    Returns:
        Human-readable string, e.g. "128.4 MB" or "1.02 GB".
    """
    process = psutil.Process()
    rss_bytes: int = process.memory_info().rss  # Resident Set Size in bytes

    rss_mb = rss_bytes / (1024 ** 2)
    if rss_mb < 1024:
        readable = f"{rss_mb:.1f} MB"
    else:
        readable = f"{rss_mb / 1024:.2f} GB"

    logger.debug("Process RSS: %s", readable)
    return readable


def get_metrics_snapshot() -> Tuple[float, str]:
    """
    Convenience: return (perf_counter_start, current_memory_string).
    Call this before inference, then call get_cpu_time(start, perf_counter()) after.
    """
    return start_timer(), get_memory_usage()
