# 🔍 TruthLens — AI-Powered Deepfake Detection

> **Detect manipulated and AI-generated videos in seconds using Google Gemini 2.5 Flash + local computer vision.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-purple?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 What is TruthLens?

TruthLens is a **Streamlit web application** that analyzes video files to determine whether they are **authentic or deepfake/AI-generated**. It extracts a key frame from the video, runs forensic analysis using **Google Gemini 2.5 Flash** (cloud) or a **local simulation engine** (offline), and presents a verdict with a confidence score and detailed reasoning — all through a sleek dark-themed UI.

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
Upload Video → Extract Middle Frame → Run AI Analysis → Display Verdict
```

1. **Frame Extraction** — OpenCV extracts the most informative frame from the middle of the video
2. **AI Analysis (Cloud)** — Google Gemini 2.5 Flash performs multi-signal forensic analysis on the frame:
   - Facial boundary artifacts
   - Unnatural skin texture / blurring
   - Lighting inconsistencies
   - Eye, lip, and hair rendering quality
   - GAN fingerprinting patterns
3. **Local Fallback (Offline)** — If no API key is provided, a MobileNetV3-style simulation engine runs locally
4. **Result Persistence** — Every analysis is saved to a local SQLite database for history tracking
5. **Verdict Display** — Clear confidence score (0–100%), color-coded verdict, and forensic reasoning

---

## 🖥️ Features

| Feature | Description |
|---|---|
| 🎬 Multi-format support | MP4, AVI, MOV, MKV, WEBM, FLV, WMV |
| ☁️ Cloud analysis | Google Gemini 2.5 Flash via API |
| 💻 Offline mode | Local simulation engine (no API key needed) |
| 📊 Confidence score | 0–100% with visual progress bar |
| 🔬 Forensic reasoning | Detailed AI explanation of the verdict |
| 🗃️ History tracking | SQLite database with past analysis records |
| ⚡ Performance metrics | CPU time and memory usage per analysis |
| 🎨 Premium dark UI | Glassmorphism design with gradient accents |

---

## 📁 Project Structure

```
truthlens-python/
│
├── app.py                  # Main Streamlit application & UI
├── config.py               # Global configuration & env variable loading
├── requirements.txt        # Python dependencies
│
├── services/
│   ├── analyzer.py         # Core analysis pipeline (orchestrator)
│   ├── gemini_service.py   # Google Gemini API integration
│   └── local_model.py      # Offline local simulation engine
│
├── database/
│   ├── db.py               # SQLite helpers (save, get history, clear)
│   └── truthlens.db        # Auto-created SQLite database (gitignored)
│
├── utils/
│   ├── video_utils.py      # Frame extraction using OpenCV
│   └── metrics.py          # CPU timing and memory usage helpers
│
└── prompts/
    └── gemini_prompt.txt   # Forensic analysis prompt sent to Gemini
```

---

## ⚙️ Prerequisites

- **Python 3.10 or higher**
- **pip** (comes with Python)
- *(Optional)* A **Google Gemini API key** for cloud-based analysis — [Get one free here](https://aistudio.google.com/app/apikey)

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

### 4. Set your Gemini API Key *(optional but recommended)*

**Option A — Environment variable (recommended):**

```bash
# Windows (Command Prompt)
set GEMINI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"

# macOS / Linux
export GEMINI_API_KEY="your_api_key_here"
```

**Option B — Enter it directly in the app sidebar** after launching (no environment setup needed).

> 💡 If you skip this step entirely, the app runs in **offline mode** using the local simulation engine.

### 5. Run the app

```bash
# If 'streamlit' is in your PATH:
streamlit run app.py

# Or via Python module:
python -m streamlit run app.py
```

### 6. Open in your browser

The app will automatically open at:
```
http://localhost:8501
```

---

## 🎮 How to Use

1. **Open the app** at `http://localhost:8501`
2. *(Optional)* Enter your **Gemini API Key** in the left sidebar for cloud-powered analysis
3. **Upload a video** (MP4, MOV, AVI, etc.) using the drag-and-drop area
4. Click **"🔍 Analyze for Deepfakes"**
5. Wait a few seconds while the AI analyzes the video
6. View the **verdict**, **confidence score**, **forensic reasoning**, and **performance metrics**
7. All results are automatically saved to **Analysis History** at the bottom

---

## 🔑 Getting a Free Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)
5. Paste it into the TruthLens sidebar or set it as an environment variable

> The free tier is sufficient for personal use — no billing setup required.

---

## 🌐 Analysis Modes

| Mode | When | Engine |
|---|---|---|
| ☁️ **Cloud (Gemini)** | API key is provided | Google Gemini 2.5 Flash |
| 💻 **Offline (Local)** | No API key provided | MobileNetV3 simulation |
| ⚡ **Local Fallback** | API call fails | Local simulation (auto) |

---

## 🛠️ Configuration

Edit `config.py` to customize behavior:

| Setting | Default | Description |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.5-flash-preview-05-20` | Gemini model to use |
| `GEMINI_TIMEOUT` | `30` seconds | API request timeout |
| `FRAME_JPEG_QUALITY` | `90` | Frame quality sent to Gemini (0–100) |
| `FRAME_MAX_DIM` | `1024` | Max frame dimension (pixels) |

---

## ⚠️ Disclaimer

> TruthLens is intended **for research and educational purposes only**. It is not a certified forensic tool. Do not use it as the sole basis for legal or journalistic decisions. AI-based detection has inherent limitations and can produce false positives/negatives.

---

## 🧑‍💻 Author

**Kartheek Lenka** — [GitHub](https://github.com/Kartheek-Lenka)

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute.