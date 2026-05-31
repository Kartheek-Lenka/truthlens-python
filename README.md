# 🔍 TruthLens — AI-Powered Deepfake Detection

> **Detect manipulated and AI-generated videos in seconds using a local machine learning model — completely offline, no external APIs required.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.13%2B-FF6F00?logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 What is TruthLens?

TruthLens is a **Streamlit web application** that analyzes video files to determine whether they are **authentic or deepfake/AI-generated**. It extracts a key frame from the video, runs forensic analysis using a **locally-trained ML model** (MobileNetV3 backbone), and presents a verdict with a confidence score and detailed reasoning — all through a sleek dark-themed UI.

**Key Difference from v1.0:** TruthLens v2.0 operates **100% offline** using a local machine learning model instead of relying on external APIs. No internet connection required. All computation happens on your device.

---

## 🚨 The Problem It Solves

Deepfakes — AI-generated fake videos of real people — are becoming increasingly convincing and are being used to:
- Spread **misinformation and political propaganda**
- Commit **identity fraud and impersonation**
- Create **non-consensual synthetic media**
- Undermine **trust in video evidence**

Most people have **no reliable tool** to quickly check whether a video is real or fabricated. TruthLens bridges this gap.

---

## ✅ How It Solves It

```
Upload Video → Extract Middle Frame → Run Local ML Analysis → Display Verdict
```

1. **Frame Extraction** — OpenCV extracts the most informative frame from the middle of the video
2. **ML-Based Analysis (Local)** — Transfer learning model (MobileNetV3 backbone) performs forensic analysis:
   - Face detection and feature extraction
   - Spectral domain analysis (frequency artifacts)
   - Channel-wise statistical anomalies
   - GAN upsampling fingerprints
   - Unnatural blending seams and edge inconsistencies
3. **Fallback Detection** — Lightweight heuristic-based analysis if TensorFlow unavailable
4. **Result Persistence** — Every analysis is saved to a local SQLite database for history tracking
5. **Verdict Display** — Clear confidence score (0–100%), color-coded verdict, and forensic reasoning

---

## 🖥️ Features

| Feature | Description |
|---|---|
| 🎬 Multi-format support | MP4, AVI, MOV, MKV, WEBM, FLV, WMV |
| 🧠 Local ML model | Transfer learning-based detector (no cloud API needed) |
| 📱 Mobile-first architecture | MobileNetV3 for efficient inference |
| 💻 Fully offline | No internet connection required after installation |
| 📊 Confidence score | 0–100% with visual progress bar |
| 🔬 Forensic reasoning | Detailed explanation of the detection verdict |
| 🗃️ History tracking | SQLite database with past analysis records |
| ⚡ Performance metrics | CPU time and memory usage per analysis |
| 🎨 Premium dark UI | Glassmorphism design with gradient accents |
| 🔒 Privacy-first | All data stays on your device |

---

## 📊 How the ML Model Works

### Model Architecture
- **Backbone:** MobileNetV3Small (pre-trained ImageNet weights)
- **Input:** 224×224 RGB frames (auto-resized)
- **Output:** Binary classification (Real=0, Fake=1)
- **Head Architecture:**
  - Global Average Pooling
  - Dense(256, ReLU) + Dropout(0.5)
  - Dense(128, ReLU) + Dropout(0.3)
  - Dense(64, ReLU)
  - Dense(1, Sigmoid) → confidence score

### Training Data (Reference)
Model trained on datasets including:
- **FaceForensics++** — The gold standard for deepfake detection
- **DFDC** (DeepFake Detection Challenge)
- **CelebA-Spoof**
- **WildDeepfake**

### Detection Techniques
The model analyzes multiple forensic signals:

1. **Frequency Domain Analysis**
   - FFT-based detection of upsampling artifacts
   - Checkerboard pattern detection (common in GAN-generated content)
   - Spectral anomaly scoring

2. **Spatial Analysis**
   - Face detection and landmark analysis
   - Edge consistency checking
   - Lighting/shadow coherence

3. **Statistical Analysis**
   - Color channel variance anomalies
   - Noise distribution profiling
   - Temporal inconsistencies (on video sequences)

---

## 📁 Project Structure

```
truthlens-python/
│
├── app.py                  # Main Streamlit application & UI
├── config.py               # Global configuration
├── requirements.txt        # Python dependencies (with TensorFlow)
│
├── services/
│   ├── analyzer.py         # Core analysis pipeline (orchestrator)
│   ├── ml_model.py         # TensorFlow model & inference engine
│   └── local_model.py      # Deprecated (kept for compatibility)
│
├── database/
│   ├── db.py               # SQLite helpers (save, get history, clear)
│   └── truthlens.db        # Auto-created SQLite database (gitignored)
│
├── utils/
│   ├── video_utils.py      # Frame extraction using OpenCV
│   └── metrics.py          # CPU timing and memory usage helpers
│
├── prompts/
│   └── gemini_prompt.txt   # Deprecated (no longer used)
│
└── models/
    └── .truthlens/         # Local model cache directory (~/.truthlens/models/)
        └── (model weights downloaded on first run)
```

---

## ⚙️ Prerequisites

- **Python 3.10 or higher**
- **pip** (comes with Python)
- **~1-2 GB free disk space** (for TensorFlow and model weights)
- **No internet required** after initial setup ✅

---

## 🚀 Quick Start (Installation Guide)

### 1. Clone the repository

```bash
git clone https://github.com/Kartheek-Lenka/truthlens-python.git
cd truthlens-python
```

### 2. Create a virtual environment *(recommended)*

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Streamlit (UI framework)
- OpenCV (video processing)
- TensorFlow (ML model)
- NumPy, PSUtil (utilities)

### 4. Run the app

```bash
# If 'streamlit' is in your PATH:
streamlit run app.py

# Or via Python module:
python -m streamlit run app.py
```

### 5. Open in your browser

The app will automatically open at:
```
http://localhost:8501
```

> **First Run:** The first time you analyze a video, TensorFlow will initialize and download model weights (this may take 1-2 minutes). Subsequent analyses are much faster.

---

## 🎮 How to Use

1. **Open the app** at `http://localhost:8501`
2. **Upload a video** (MP4, MOV, AVI, etc.) using the drag-and-drop area
3. Click **"🔍 Analyze for Deepfakes"**
4. Wait while the local ML model analyzes the video (~3-10 seconds)
5. View the **verdict**, **confidence score**, **forensic reasoning**, and **performance metrics**
6. All results are automatically saved to **Analysis History** at the bottom

---

## 🌐 Analysis Modes

| Mode | When | Engine |
|---|---|---|
| 🧠 **ML Model** | Always available | Local TensorFlow/Keras model |
| 💻 **Lightweight** | TensorFlow unavailable | Heuristic-based detection |
| 🔒 **Offline** | No internet needed | All computation local |

---

## 🛠️ Configuration

Edit `config.py` to customize behavior:

| Setting | Default | Description |
|---|---|---|
| `MODEL_TYPE` | `mobilenet_v3` | Model architecture type |
| `MODEL_SIZE` | `mobile` | `mobile` for speed, `standard` for accuracy |
| `INFERENCE_TIMEOUT` | `30` | Max seconds for analysis |
| `FRAME_JPEG_QUALITY` | `90` | Frame quality (0–100) |
| `FRAME_MAX_DIM` | `1024` | Max frame dimension (pixels) |
| `CONFIDENCE_THRESHOLD` | `0.5` | Threshold for fake classification |

---

## 🔐 Privacy & Security

✅ **100% Offline**
- All analysis happens on your device
- No data sent to external servers
- No cloud API calls

✅ **Data Stays Local**
- Videos are processed in-memory only
- History stored in local SQLite database
- No telemetry or usage tracking

✅ **Open Source**
- Inspect the code yourself
- Contribute improvements
- MIT Licensed

---

## ⚠️ Disclaimer

> TruthLens is intended **for research and educational purposes only**. It is not a certified forensic tool. Do not use it as the sole basis for legal or journalistic decisions. AI-based detection has inherent limitations and can produce false positives/negatives. Always corroborate findings with other forensic methods.

---

## 🚀 What's New in v2.0

### From v1.0 → v2.0

| Feature | v1.0 | v2.0 |
|---|---|---|
| **Analysis Engine** | Gemini 2.5 Flash (Cloud) | Local ML Model (Offline) |
| **Internet Required** | ✅ Yes | ❌ No |
| **Model Location** | Google Servers | Your Device |
| **API Key Required** | ✅ Yes | ❌ No |
| **Speed** | Depends on network | Fast (3-10s) |
| **Privacy** | Data sent to Google | All local |
| **Cost** | Depends on usage | Free |

---

## 🧑‍💻 Author

**Kartheek Lenka** — [GitHub](https://github.com/Kartheek-Lenka)

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute.

---

## 🙏 Acknowledgments

- **FaceForensics++** team for benchmark datasets
- **TensorFlow** community
- **Streamlit** for the awesome UI framework
- **OpenCV** for video processing