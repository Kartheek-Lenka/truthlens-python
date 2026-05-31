"""
services/ml_model.py — Forensic Deepfake Detection Engine
Multi-signal image forensics for detecting AI-generated and manipulated media.

Uses 8 independent forensic detectors that each produce a continuous score,
combined with weighted averaging for a final verdict. Every image gets a
genuinely different score based on its actual pixel content.

Fully offline — no network calls, no external APIs.
"""

import logging
import math
from typing import Optional, TypedDict, Tuple, List, Dict

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class MLModelResult(TypedDict):
    """Result from ML model inference."""
    isFake: bool
    confidence: int  # 0-100
    reasoning: str
    model_name: str


# ═══════════════════════════════════════════════════════════════════════════════
# Individual Forensic Detectors
# Each returns (score: 0.0–1.0, finding: str)
#   score → 0.0 = definitely real, 1.0 = definitely fake
# ═══════════════════════════════════════════════════════════════════════════════

def _noise_consistency_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    Analyse noise level consistency across image blocks.
    Real camera photos have uniform sensor noise; deepfakes/AI images have
    inconsistent noise because different regions are generated independently.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float64)
        # Extract noise via high-pass (original minus median-blurred)
        blurred = cv2.medianBlur(gray.astype(np.uint8), 5).astype(np.float64)
        noise = np.abs(gray - blurred)

        h, w = noise.shape
        block = 64
        block_stds = []
        for y in range(0, h - block, block):
            for x in range(0, w - block, block):
                patch = noise[y:y+block, x:x+block]
                block_stds.append(np.std(patch))

        if len(block_stds) < 4:
            return 0.3, "Insufficient resolution for noise analysis"

        block_stds = np.array(block_stds)
        mean_std = np.mean(block_stds)
        coeff_var = np.std(block_stds) / (mean_std + 1e-8)

        # High coefficient of variation → inconsistent noise → likely fake
        # Real images: CoV typically 0.3–0.7
        # AI images: CoV can be > 1.0 or < 0.15 (too uniform = also suspicious)
        if coeff_var > 1.2:
            score = min(1.0, 0.6 + (coeff_var - 1.2) * 0.5)
            finding = f"Highly inconsistent noise distribution (CoV={coeff_var:.2f}), suggesting synthetic regions"
        elif coeff_var < 0.15:
            score = min(1.0, 0.5 + (0.15 - coeff_var) * 3.0)
            finding = f"Unnaturally uniform noise (CoV={coeff_var:.2f}), atypical of camera sensors"
        elif coeff_var > 0.85:
            score = 0.3 + (coeff_var - 0.85) * 0.8
            finding = f"Moderately inconsistent noise patterns (CoV={coeff_var:.2f})"
        else:
            score = max(0.05, coeff_var * 0.3)
            finding = f"Natural noise distribution (CoV={coeff_var:.2f}), consistent with camera capture"

        return np.clip(score, 0.0, 1.0), finding

    except Exception as e:
        logger.debug("Noise analysis error: %s", e)
        return 0.3, "Noise analysis inconclusive"


def _frequency_spectrum_analysis(gray: np.ndarray) -> Tuple[float, str]:
    """
    FFT-based spectral analysis. GANs leave characteristic grid-like artifacts
    in the frequency domain. Also checks for unnatural spectral fall-off.
    """
    try:
        # Resize for consistent analysis
        h, w = gray.shape[:2]
        size = min(h, w, 512)
        if h != size or w != size:
            gray = cv2.resize(gray, (size, size))

        f = np.fft.fft2(gray.astype(np.float64))
        f_shift = np.fft.fftshift(f)
        magnitude = np.log1p(np.abs(f_shift))

        center = size // 2

        # 1. Azimuthal variance — real images have smooth radial falloff;
        #    GANs show peaks at specific angles
        radial_profiles = []
        for r in range(20, center - 10, 8):
            ring_vals = []
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                x = int(center + r * math.cos(rad))
                y = int(center + r * math.sin(rad))
                x = np.clip(x, 0, size - 1)
                y = np.clip(y, 0, size - 1)
                ring_vals.append(magnitude[y, x])
            radial_profiles.append(np.std(ring_vals) / (np.mean(ring_vals) + 1e-8))

        azimuthal_score = np.mean(radial_profiles) if radial_profiles else 0.3

        # 2. High-frequency energy ratio — AI images often lack natural
        #    high-frequency detail or have artificial HF patterns
        total_energy = np.sum(magnitude)
        r_threshold = center // 3
        y_grid, x_grid = np.ogrid[:size, :size]
        dist = np.sqrt((x_grid - center)**2 + (y_grid - center)**2)
        hf_energy = np.sum(magnitude[dist > r_threshold]) / (total_energy + 1e-8)

        # Real photos: hf_energy typically 0.55–0.75
        # AI images: often < 0.5 (too smooth) or unusual patterns
        hf_deviation = abs(hf_energy - 0.65)

        # 3. Spectral periodicity — check for periodic peaks (GAN grid artifacts)
        row_spectrum = magnitude[center, center+10:]
        if len(row_spectrum) > 20:
            # Autocorrelation to detect periodicity
            row_norm = row_spectrum - np.mean(row_spectrum)
            autocorr = np.correlate(row_norm, row_norm, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            autocorr = autocorr / (autocorr[0] + 1e-8)
            # Check for secondary peaks (periodic artifacts)
            peaks = []
            for i in range(3, len(autocorr) - 1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1] and autocorr[i] > 0.3:
                    peaks.append(autocorr[i])
            periodicity_score = max(peaks) if peaks else 0.0
        else:
            periodicity_score = 0.0

        # Combine
        score = (azimuthal_score * 0.4 + hf_deviation * 2.0 * 0.3 + periodicity_score * 0.3)
        score = np.clip(score, 0.0, 1.0)

        findings = []
        if azimuthal_score > 0.5:
            findings.append(f"angular spectral irregularities ({azimuthal_score:.2f})")
        if hf_deviation > 0.15:
            findings.append(f"atypical high-frequency energy distribution")
        if periodicity_score > 0.3:
            findings.append(f"periodic spectral peaks detected (GAN fingerprint)")

        if findings:
            finding = "Frequency analysis: " + "; ".join(findings)
        else:
            finding = "Frequency spectrum appears natural with smooth radial falloff"

        return float(score), finding

    except Exception as e:
        logger.debug("Frequency analysis error: %s", e)
        return 0.3, "Frequency analysis inconclusive"


def _jpeg_ghost_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    Double-JPEG compression detection. Re-compresses frame at multiple
    quality levels and measures error — doubly compressed images show
    characteristic error minima at the original quality level.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        errors = []
        qualities = list(range(50, 100, 5))

        for q in qualities:
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, q])
            recompressed = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
            if recompressed is None:
                continue
            if recompressed.shape != gray.shape:
                recompressed = cv2.resize(recompressed, (gray.shape[1], gray.shape[0]))
            err = np.mean(np.abs(gray.astype(np.float64) - recompressed.astype(np.float64)))
            errors.append(err)

        if len(errors) < 5:
            return 0.3, "JPEG analysis inconclusive"

        errors = np.array(errors)
        # Look for a distinct minimum (sign of prior compression)
        min_idx = np.argmin(errors)
        min_err = errors[min_idx]
        mean_err = np.mean(errors)

        # How much does the minimum stand out?
        dip_ratio = min_err / (mean_err + 1e-8)

        # Strong dip at a specific quality → evidence of prior compression
        # This itself isn't proof of fakery, but combined with other signals...
        if dip_ratio < 0.4:
            score = 0.5
            finding = f"Strong JPEG re-compression artifact at quality ~{qualities[min_idx]} (dip={dip_ratio:.2f})"
        elif dip_ratio < 0.7:
            score = 0.3
            finding = f"Moderate JPEG compression signature at quality ~{qualities[min_idx]}"
        else:
            score = 0.1
            finding = "No significant double-compression artifacts detected"

        return float(np.clip(score, 0.0, 1.0)), finding

    except Exception as e:
        logger.debug("JPEG ghost analysis error: %s", e)
        return 0.2, "JPEG analysis inconclusive"


def _edge_coherence_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    Compare edge maps across colour channels. Real images have highly
    correlated edges in R/G/B; spliced or GAN images often show
    channel-wise edge inconsistencies.
    """
    try:
        channels = cv2.split(frame)
        edge_maps = []
        for ch in channels:
            edges = cv2.Canny(ch, 80, 200)
            edge_maps.append(edges.astype(np.float64))

        # Cross-channel edge correlation
        correlations = []
        for i in range(3):
            for j in range(i+1, 3):
                flat_i = edge_maps[i].flatten()
                flat_j = edge_maps[j].flatten()
                norm_i = np.linalg.norm(flat_i) + 1e-8
                norm_j = np.linalg.norm(flat_j) + 1e-8
                corr = np.dot(flat_i, flat_j) / (norm_i * norm_j)
                correlations.append(corr)

        mean_corr = np.mean(correlations)

        # Real images: correlation typically > 0.85
        # Manipulated: often 0.5–0.8
        if mean_corr < 0.5:
            score = 0.8
            finding = f"Severe cross-channel edge inconsistency (corr={mean_corr:.3f})"
        elif mean_corr < 0.7:
            score = 0.55
            finding = f"Moderate edge coherence issues across colour channels (corr={mean_corr:.3f})"
        elif mean_corr < 0.85:
            score = 0.3
            finding = f"Slight edge variations between channels (corr={mean_corr:.3f})"
        else:
            score = 0.08
            finding = f"Strong cross-channel edge coherence (corr={mean_corr:.3f}), consistent with authentic capture"

        return float(np.clip(score, 0.0, 1.0)), finding

    except Exception as e:
        logger.debug("Edge coherence error: %s", e)
        return 0.3, "Edge analysis inconclusive"


def _saturation_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    Analyse colour saturation distribution. AI-generated images often
    have unusual saturation profiles — either oversaturated or with
    unnatural uniformity in hue/saturation space.
    """
    try:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1].astype(np.float64)
        value_ch = hsv[:, :, 2].astype(np.float64)

        sat_mean = np.mean(saturation)
        sat_std = np.std(saturation)
        sat_skew = float(np.mean(((saturation - sat_mean) / (sat_std + 1e-8)) ** 3))

        # Hue histogram entropy
        hue = hsv[:, :, 0].flatten()
        hist, _ = np.histogram(hue, bins=36, range=(0, 180))
        hist = hist.astype(np.float64)
        hist = hist / (hist.sum() + 1e-8)
        entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))

        # AI images tend to have: low hue entropy, unusual saturation skew
        # Natural images: entropy typically 3.5–5.0, skew -0.5 to 1.5
        score = 0.0
        findings = []

        if entropy < 2.5:
            score += 0.35
            findings.append(f"low colour diversity (entropy={entropy:.2f})")
        elif entropy > 5.2:
            score += 0.15
            findings.append(f"unusually broad hue distribution")

        abs_skew = abs(sat_skew)
        if abs_skew > 2.0:
            score += 0.3
            findings.append(f"extreme saturation skew ({sat_skew:.2f})")
        elif abs_skew > 1.5:
            score += 0.15

        # Check for banding in saturation (common in AI art)
        sat_hist, _ = np.histogram(saturation, bins=64, range=(0, 256))
        sat_hist_norm = sat_hist.astype(np.float64) / (sat_hist.sum() + 1e-8)
        sat_entropy = -np.sum(sat_hist_norm[sat_hist_norm > 0] * np.log2(sat_hist_norm[sat_hist_norm > 0]))
        if sat_entropy < 3.5:
            score += 0.2
            findings.append("saturation banding detected")

        score = np.clip(score, 0.0, 1.0)

        if findings:
            finding = "Colour analysis: " + "; ".join(findings)
        else:
            finding = f"Natural colour distribution (hue entropy={entropy:.2f}, sat skew={sat_skew:.2f})"

        return float(score), finding

    except Exception as e:
        logger.debug("Saturation analysis error: %s", e)
        return 0.3, "Colour analysis inconclusive"


def _texture_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    Local Binary Pattern-inspired texture analysis.
    Computes local texture statistics and checks for unnaturally smooth
    or repetitive patterns.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Laplacian variance — measure of focus/detail
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = np.var(laplacian)
        lap_mean = np.mean(np.abs(laplacian))

        # Gradient magnitude statistics
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(gx**2 + gy**2)
        grad_mean = np.mean(grad_mag)
        grad_std = np.std(grad_mag)

        # Gradient kurtosis — AI images often have unusual gradient distributions
        grad_flat = grad_mag.flatten()
        grad_norm = (grad_flat - np.mean(grad_flat)) / (np.std(grad_flat) + 1e-8)
        kurtosis = float(np.mean(grad_norm ** 4)) - 3.0  # excess kurtosis

        score = 0.0
        findings = []

        # Very low Laplacian variance = too smooth (possible AI generation)
        if lap_var < 100:
            score += 0.4
            findings.append(f"very low texture detail (Laplacian var={lap_var:.1f})")
        elif lap_var < 500:
            score += 0.15
            findings.append(f"moderate texture smoothness")

        # Unusual kurtosis
        if kurtosis > 15:
            score += 0.25
            findings.append(f"unusual gradient kurtosis ({kurtosis:.1f})")
        elif kurtosis < 0:
            score += 0.2
            findings.append(f"platykurtic gradient distribution")

        # Ratio of gradient std to mean — AI images often have different ratios
        grad_ratio = grad_std / (grad_mean + 1e-8)
        if grad_ratio > 3.0:
            score += 0.2
            findings.append(f"high gradient variability (ratio={grad_ratio:.2f})")

        score = np.clip(score, 0.0, 1.0)

        if findings:
            finding = "Texture analysis: " + "; ".join(findings)
        else:
            finding = f"Natural texture patterns (Laplacian var={lap_var:.0f}, grad kurtosis={kurtosis:.1f})"

        return float(score), finding

    except Exception as e:
        logger.debug("Texture analysis error: %s", e)
        return 0.3, "Texture analysis inconclusive"


def _face_forensics(frame: np.ndarray) -> Tuple[float, str]:
    """
    Face-specific forensics: detect faces, check symmetry, skin texture
    consistency, and boundary artifacts.
    """
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

        if len(faces) == 0:
            return 0.25, "No faces detected — forensic face analysis not applicable"

        # Analyse the largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        pad = int(w * 0.15)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)
        face_roi = frame[y1:y2, x1:x2]

        if face_roi.size == 0:
            return 0.25, "Face ROI extraction failed"

        face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        fh, fw = face_gray.shape

        score = 0.0
        findings = []

        # 1. Left-right symmetry analysis
        if fw > 20:
            left_half = face_gray[:, :fw//2]
            right_half = cv2.flip(face_gray[:, fw//2:], 1)
            min_w = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_w]
            right_half = right_half[:, :min_w]
            symmetry_error = np.mean(np.abs(left_half.astype(np.float64) - right_half.astype(np.float64)))

            # Deepfakes often have MORE symmetry than real faces (too perfect)
            if symmetry_error < 8.0:
                score += 0.35
                findings.append(f"unnaturally symmetric face (err={symmetry_error:.1f})")
            elif symmetry_error > 40.0:
                score += 0.25
                findings.append(f"high facial asymmetry (err={symmetry_error:.1f})")

        # 2. Skin texture smoothness in face region
        face_lap = cv2.Laplacian(face_gray, cv2.CV_64F)
        face_lap_var = np.var(face_lap)
        if face_lap_var < 50:
            score += 0.3
            findings.append(f"overly smooth facial skin texture (var={face_lap_var:.1f})")
        elif face_lap_var < 150:
            score += 0.1
            findings.append("slightly smooth facial texture")

        # 3. Face boundary analysis — check for blending artifacts
        border_size = max(3, min(pad, 10))
        border_region = face_roi[:border_size, :, :]  # top border
        border_lap = cv2.Laplacian(cv2.cvtColor(border_region, cv2.COLOR_BGR2GRAY), cv2.CV_64F)
        border_sharpness = np.var(border_lap)
        inner_region = face_roi[border_size*2:, :, :]
        if inner_region.size > 0:
            inner_lap = cv2.Laplacian(cv2.cvtColor(inner_region, cv2.COLOR_BGR2GRAY), cv2.CV_64F)
            inner_sharpness = np.var(inner_lap)
            sharpness_ratio = border_sharpness / (inner_sharpness + 1e-8)
            if sharpness_ratio > 3.0 or sharpness_ratio < 0.2:
                score += 0.25
                findings.append(f"face boundary sharpness discontinuity (ratio={sharpness_ratio:.2f})")

        score = np.clip(score, 0.0, 1.0)

        if findings:
            finding = f"Face forensics ({len(faces)} face(s)): " + "; ".join(findings)
        else:
            finding = f"Face analysis ({len(faces)} face(s)): natural symmetry and texture"

        return float(score), finding

    except Exception as e:
        logger.debug("Face forensics error: %s", e)
        return 0.25, "Face forensic analysis inconclusive"


def _benford_law_analysis(frame: np.ndarray) -> Tuple[float, str]:
    """
    First-digit distribution of DCT coefficients should follow Benford's Law
    in natural images. Manipulated images deviate from this distribution.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float64)

        # Compute block-wise DCT (8x8 blocks, like JPEG)
        h, w = gray.shape
        first_digits = []
        for y in range(0, h - 8, 8):
            for x in range(0, w - 8, 8):
                block = gray[y:y+8, x:x+8]
                dct_block = cv2.dct(block)
                # Get non-zero, non-DC coefficients
                coeffs = dct_block.flatten()[1:]  # skip DC
                for c in coeffs:
                    c_abs = abs(c)
                    if c_abs >= 1.0:
                        first_digit = int(str(int(c_abs))[0])
                        if 1 <= first_digit <= 9:
                            first_digits.append(first_digit)

        if len(first_digits) < 100:
            return 0.3, "Insufficient DCT coefficients for Benford analysis"

        # Benford's expected distribution
        observed = np.zeros(9)
        for d in first_digits:
            observed[d - 1] += 1
        observed = observed / (observed.sum() + 1e-8)

        expected = np.array([math.log10(1 + 1/d) for d in range(1, 10)])

        # Chi-squared-like divergence
        divergence = np.sum((observed - expected)**2 / (expected + 1e-8))

        # Natural images: divergence typically < 0.01
        # Manipulated: often > 0.02
        if divergence > 0.05:
            score = min(1.0, 0.6 + divergence * 2)
            finding = f"Strong deviation from Benford's Law (div={divergence:.4f}), suggesting manipulation"
        elif divergence > 0.02:
            score = 0.4 + divergence * 5
            finding = f"Moderate Benford's Law deviation (div={divergence:.4f})"
        elif divergence > 0.01:
            score = 0.2 + divergence * 10
            finding = f"Slight statistical irregularity in DCT coefficients (div={divergence:.4f})"
        else:
            score = divergence * 10
            finding = f"DCT coefficient distribution follows Benford's Law (div={divergence:.4f})"

        return float(np.clip(score, 0.0, 1.0)), finding

    except Exception as e:
        logger.debug("Benford analysis error: %s", e)
        return 0.3, "Statistical analysis inconclusive"


# ═══════════════════════════════════════════════════════════════════════════════
# Main Detector Class
# ═══════════════════════════════════════════════════════════════════════════════

class DeepfakeDetector:
    """
    Multi-signal forensic deepfake detector.
    Runs 8 independent forensic analyses and combines their scores.
    Fully offline — no external dependencies or API calls.
    """

    MODEL_NAME = "truthlens_forensic_v2"
    MODEL_SIZE = "full"

    # Detector weights (sum to 1.0)
    DETECTOR_WEIGHTS = {
        "noise":      0.18,
        "frequency":  0.15,
        "jpeg":       0.08,
        "edge":       0.14,
        "saturation": 0.10,
        "texture":    0.13,
        "face":       0.12,
        "benford":    0.10,
    }

    def __init__(self):
        self.model_loaded = True
        logger.info("TruthLens Forensic Engine v2 initialised (8 detectors)")

    def predict(self, frame: np.ndarray) -> MLModelResult:
        """Run all forensic detectors and combine scores."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Run all detectors
            results: Dict[str, Tuple[float, str]] = {}
            results["noise"] = _noise_consistency_analysis(frame)
            results["frequency"] = _frequency_spectrum_analysis(gray)
            results["jpeg"] = _jpeg_ghost_analysis(frame)
            results["edge"] = _edge_coherence_analysis(frame)
            results["saturation"] = _saturation_analysis(frame)
            results["texture"] = _texture_analysis(frame)
            results["face"] = _face_forensics(frame)
            results["benford"] = _benford_law_analysis(frame)

            # Weighted combination
            weighted_score = 0.0
            for key, (score, _) in results.items():
                weight = self.DETECTOR_WEIGHTS.get(key, 0.1)
                weighted_score += score * weight

            # Convert to confidence percentage
            # weighted_score is 0.0 (real) to 1.0 (fake)
            confidence_fake = int(np.clip(weighted_score * 100, 5, 98))
            is_fake = confidence_fake > 50

            # Report confidence as "how sure we are of our verdict"
            if is_fake:
                display_confidence = confidence_fake
            else:
                display_confidence = 100 - confidence_fake

            # Build reasoning from top contributing signals
            signal_contributions = []
            for key, (score, finding) in results.items():
                signal_contributions.append((score * self.DETECTOR_WEIGHTS.get(key, 0.1), finding, score))

            signal_contributions.sort(reverse=True, key=lambda x: x[0])

            # Top 3 findings for reasoning
            top_findings = [f for _, f, _ in signal_contributions[:3]]
            reasoning = " | ".join(top_findings)

            logger.info(
                "Forensic analysis: score=%.3f, isFake=%s, confidence=%d%%, detectors=%s",
                weighted_score, is_fake, display_confidence,
                {k: f"{v[0]:.2f}" for k, v in results.items()}
            )

            return MLModelResult(
                isFake=is_fake,
                confidence=display_confidence,
                reasoning=reasoning,
                model_name=f"{self.MODEL_NAME}_{self.MODEL_SIZE}",
            )

        except Exception as e:
            logger.error("Forensic analysis failed: %s", e)
            return MLModelResult(
                isFake=False,
                confidence=50,
                reasoning=f"Analysis error: {e}",
                model_name=self.MODEL_NAME,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level API
# ═══════════════════════════════════════════════════════════════════════════════

_detector: Optional[DeepfakeDetector] = None


def get_detector() -> DeepfakeDetector:
    global _detector
    if _detector is None:
        _detector = DeepfakeDetector()
    return _detector


def predict_deepfake(frame: np.ndarray) -> MLModelResult:
    """
    Public API — run forensic deepfake detection on a BGR frame.
    Returns MLModelResult with isFake, confidence, reasoning, model_name.
    """
    detector = get_detector()
    return detector.predict(frame)
