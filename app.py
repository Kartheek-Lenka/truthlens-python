"""
app.py — TruthLens Streamlit UI
Upload a video → extract frame → analyze → display verdict + history.
"""

import io
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import streamlit as st

# ── Path fix so relative imports work when launched from any CWD ───────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import APP_TITLE, APP_ICON, APP_DESCRIPTION
from utils.video_utils import extract_frame
from services.analyzer import analyze_frame, AnalysisResult
from database.db import save_result, get_history, clear_history

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# Page config — MUST be first Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# Custom CSS — dark glassmorphism theme
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root tokens ─────────────────────────────────────────────────────── */
:root {
    --bg-primary:   #0d1117;
    --bg-card:      rgba(22, 27, 34, 0.95);
    --bg-glass:     rgba(255, 255, 255, 0.05);
    --border:       rgba(255, 255, 255, 0.08);
    --accent:       #7c3aed;
    --accent-light: #a78bfa;
    --success:      #10b981;
    --danger:       #ef4444;
    --warning:      #f59e0b;
    --text-primary: #e6edf3;
    --text-muted:   #8b949e;
    --radius:       12px;
    --shadow:       0 8px 32px rgba(0,0,0,0.4);
}

/* ── Global ─────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Cards ─────────────────────────────────────────────────────────── */
.tl-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
    backdrop-filter: blur(16px);
}

/* ── Verdict banner ─────────────────────────────────────────────────── */
.verdict-fake {
    background: linear-gradient(135deg, rgba(239,68,68,0.18) 0%, rgba(239,68,68,0.06) 100%);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: var(--radius);
    padding: 1.5rem 2rem;
    text-align: center;
}
.verdict-real {
    background: linear-gradient(135deg, rgba(16,185,129,0.18) 0%, rgba(16,185,129,0.06) 100%);
    border: 1px solid rgba(16,185,129,0.4);
    border-radius: var(--radius);
    padding: 1.5rem 2rem;
    text-align: center;
}
.verdict-label {
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
}
.verdict-fake .verdict-label  { color: #ef4444; }
.verdict-real .verdict-label  { color: #10b981; }
.verdict-sub {
    font-size: 0.9rem;
    color: var(--text-muted);
}

/* ── Metric pills ────────────────────────────────────────────────────── */
.metric-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.metric-pill {
    background: var(--bg-glass);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.82rem;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.metric-pill span.label { color: var(--text-muted); margin-right: 0.3rem; }

/* ── Confidence bar ─────────────────────────────────────────────────── */
.conf-bar-bg {
    background: rgba(255,255,255,0.07);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
    margin: 0.4rem 0 0.8rem 0;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s ease;
}
.bar-fake { background: linear-gradient(90deg, #ef4444, #f97316); }
.bar-real { background: linear-gradient(90deg, #10b981, #34d399); }

/* ── Reasoning box ──────────────────────────────────────────────────── */
.reasoning-box {
    background: rgba(124,58,237,0.08);
    border-left: 3px solid var(--accent-light);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 0.9rem 1.1rem;
    font-size: 0.9rem;
    line-height: 1.55;
    color: var(--text-primary);
    margin-top: 0.5rem;
}

/* ── Engine badge ────────────────────────────────────────────────────── */
.engine-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.badge-gemini  { background: rgba(124,58,237,0.25); color: #a78bfa; border: 1px solid rgba(124,58,237,0.4); }
.badge-local   { background: rgba(245,158,11,0.20); color: #fbbf24; border: 1px solid rgba(245,158,11,0.4); }
.badge-fallback{ background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.4); }

/* ── History table ───────────────────────────────────────────────────── */
.hist-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    background: var(--bg-glass);
    border: 1px solid var(--border);
    font-size: 0.82rem;
}
.hist-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-fake { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
.dot-real { background: #10b981; box-shadow: 0 0 6px #10b981; }

/* ── Header ──────────────────────────────────────────────────────────── */
.tl-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
}
.tl-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
}
.tl-header p { color: var(--text-muted); font-size: 1rem; }

/* ── Streamlit overrides ─────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.5) !important;
}
.stFileUploader {
    background: var(--bg-glass) !important;
    border: 1px dashed rgba(124,58,237,0.5) !important;
    border-radius: var(--radius) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# Session state initialisation
# ══════════════════════════════════════════════════════════════════════════════
if "result" not in st.session_state:
    st.session_state.result: Optional[AnalysisResult] = None
if "frame_img" not in st.session_state:
    st.session_state.frame_img: Optional[np.ndarray] = None
if "video_name" not in st.session_state:
    st.session_state.video_name: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    st.info(
        "🟢 **Offline Mode Active**\n\n"
        "TruthLens is running in fully offline mode using a local ML model. "
        "No internet connection required. All analysis is performed locally on your device.",
        icon="🔒"
    )

    st.markdown("---")
    st.markdown("### 📊 Analysis History")

    history_limit = st.slider("History entries to show", 5, 50, 10)

    col_refresh, col_clear = st.columns(2)
    with col_refresh:
        refresh_hist = st.button("↺ Refresh", use_container_width=True)
    with col_clear:
        if st.button("🗑 Clear", use_container_width=True):
            clear_history()
            st.toast("History cleared.")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem;color:#8b949e;line-height:1.6'>"
        "TruthLens v2.0<br>"
        "Deepfake detection using<br>"
        "Local ML model<br>"
        "(MobileNetV3 backbone)<br><br>"
        "✅ Fully Offline<br>"
        "🔒 Privacy-First<br>"
        "⚡ Fast & Efficient<br><br>"
        "⚠️ For research use only."
        "</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Main content
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<div class="tl-header">
    <h1>🔍 TruthLens</h1>
    <p>AI-powered deepfake & manipulated video detection</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Two-column layout: Upload | Results ───────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="tl-card">', unsafe_allow_html=True)
    st.markdown("#### 📤 Upload Video")

    uploaded_file = st.file_uploader(
        "Drop a video file here",
        type=["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.video(uploaded_file)
        st.caption(f"📹 {uploaded_file.name}  ({uploaded_file.size / 1024:.1f} KB)")

        if uploaded_file.name != st.session_state.video_name:
            # New file uploaded → reset previous result
            st.session_state.result = None
            st.session_state.frame_img = None
            st.session_state.video_name = uploaded_file.name

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Analyze button ────────────────────────────────────────────────────
    analyze_btn = st.button(
        "🔍 Analyze for Deepfakes",
        disabled=uploaded_file is None,
        use_container_width=True,
        type="primary",
    )


# ── Analysis logic (triggered by button) ─────────────────────────────────────
if analyze_btn and uploaded_file is not None:
    with st.spinner("Extracting frame & running inference …"):
        # Write uploaded bytes to a temp file OpenCV can open
        suffix = Path(uploaded_file.name).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            frame = extract_frame(tmp_path)
            st.session_state.frame_img = frame

            result = analyze_frame(frame=frame)
            st.session_state.result = result

            # Persist to SQLite
            save_result(
                is_fake=result["isFake"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                engine=result["engine"],
                cpu_time=result["cpu_time"],
                memory=result["memory"],
            )

        except FileNotFoundError as exc:
            st.error(f"❌ Video file error: {exc}")
        except ValueError as exc:
            st.error(f"❌ Frame extraction failed: {exc}")
        except Exception as exc:
            st.error(f"❌ Unexpected error: {exc}")
            logger.exception("Analysis pipeline error")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ── Result display ────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="tl-card">', unsafe_allow_html=True)
    st.markdown("#### 🧠 Analysis Result")

    result: Optional[AnalysisResult] = st.session_state.result
    frame_img: Optional[np.ndarray] = st.session_state.frame_img

    if result is None:
        st.markdown(
            "<div style='text-align:center;padding:3rem 1rem;color:#8b949e'>"
            "<div style='font-size:3rem'>🎬</div>"
            "<p style='margin-top:1rem'>Upload a video and click <strong>Analyze</strong> to begin.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        # ── Extracted frame thumbnail ─────────────────────────────────────
        if frame_img is not None:
            # Convert BGR → RGB for display
            rgb = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
            st.image(rgb, caption="📸 Extracted frame (middle of video)", use_container_width=True)

        # ── Verdict banner ────────────────────────────────────────────────
        is_fake = result["isFake"]
        verdict_class = "verdict-fake" if is_fake else "verdict-real"
        verdict_emoji = "⚠️" if is_fake else "✅"
        verdict_text = "LIKELY MANIPULATED" if is_fake else "APPEARS AUTHENTIC"
        verdict_color = "#ef4444" if is_fake else "#10b981"
        bar_class = "bar-fake" if is_fake else "bar-real"

        confidence = result["confidence"]

        st.markdown(
            f"""
<div class="{verdict_class}">
    <div class="verdict-label">{verdict_emoji} {verdict_text}</div>
    <div class="verdict-sub">Confidence score</div>
    <div style="font-size:2rem;font-weight:700;color:{verdict_color};">{confidence}%</div>
    <div class="conf-bar-bg">
        <div class="conf-bar-fill {bar_class}" style="width:{confidence}%"></div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Engine badge ──────────────────────────────────────────────────
        engine = result["engine"]
        badge_class = "badge-local"
        engine_label = "🧠 Local ML Model (Offline)"

        st.markdown(
            f'<span class="engine-badge {badge_class}">{engine_label}</span>',
            unsafe_allow_html=True,
        )

        # ── Performance metrics ───────────────────────────────────────────
        st.markdown(
            f"""
<div class="metric-row">
    <div class="metric-pill"><span class="label">⏱ CPU Time</span>{result['cpu_time']}</div>
    <div class="metric-pill"><span class="label">🧠 Memory</span>{result['memory']}</div>
    <div class="metric-pill"><span class="label">📊 Confidence</span>{confidence}%</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Reasoning ─────────────────────────────────────────────────────
        st.markdown("**🔬 Forensic Reasoning**")
        st.markdown(
            f'<div class="reasoning-box">{result["reasoning"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# History section (below main columns)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📋 Analysis History")

history_rows = get_history(limit=history_limit)

if not history_rows:
    st.info("No analysis history yet. Upload and analyze a video to start.")
else:
    for row in history_rows:
        dot_class = "dot-fake" if row["isFake"] else "dot-real"
        verdict_str = "🔴 FAKE" if row["isFake"] else "🟢 REAL"
        engine_str = row.get("engine", "local")
        cpu_str = row.get("cpu_time", "—")
        mem_str = row.get("memory", "—")

        st.markdown(
            f"""
<div class="hist-row">
    <div class="hist-dot {dot_class}"></div>
    <div style="font-weight:600;min-width:90px">{verdict_str}</div>
    <div style="color:#a78bfa;min-width:55px">{row['confidence']}%</div>
    <div style="color:#8b949e;flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">
        {row['reasoning'][:100]}…
    </div>
    <div style="color:#8b949e;font-size:0.75rem;white-space:nowrap">⏱ {cpu_str}</div>
    <div style="color:#8b949e;font-size:0.75rem;white-space:nowrap">🧠 {mem_str}</div>
    <div style="color:#6b7280;font-size:0.72rem;white-space:nowrap">{row['timestamp']}</div>
</div>
""",
            unsafe_allow_html=True,
        )
