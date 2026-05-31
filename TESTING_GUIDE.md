# 🧪 TRUTHLENS v2.0 - COMPREHENSIVE TESTING GUIDE

## 📋 Pre-Testing Checklist

### Environment Setup
- [ ] Python 3.10+ installed
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Application file permissions verified

### Code Verification
- [x] No syntax errors (verified)
- [x] All imports valid (verified)
- [x] No Gemini API references (verified)
- [x] ML model properly integrated (verified)
- [x] Configuration updated (verified)

---

## 🚀 HOW TO RUN THE APPLICATION

### Step 1: Install Dependencies
```bash
cd c:\Users\karth\Downloads\TruthLens\Truthlens
pip install -r requirements.txt
```

**What happens:**
- Streamlit will be installed
- TensorFlow will be installed (~500MB)
- OpenCV, NumPy, and other ML libraries will be installed
- First-time setup takes 5-10 minutes

### Step 2: Launch Streamlit Application
```bash
streamlit run app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your-ip>:8501

Press CTRL+C to stop the server.
```

### Step 3: Open in Browser
Navigate to: `http://localhost:8501`

---

## 🧪 FUNCTIONAL TESTING SCENARIOS

### Test 1: Application Startup ✓

**Steps:**
1. Run `streamlit run app.py`
2. Wait for "Local URL:" message
3. Open `http://localhost:8501` in browser

**Expected Results:**
- [ ] Streamlit server starts successfully
- [ ] No error messages in terminal
- [ ] Browser loads TruthLens interface
- [ ] Dark theme displays correctly
- [ ] "TruthLens 🔍" header visible
- [ ] "Offline Mode Active" message in sidebar
- [ ] No API key input field present

**Screenshots to verify:**
- Header with gradient text
- Sidebar with "Offline Mode Active" info box
- Upload area for video files
- Analysis history section

---

### Test 2: Requirement 1 - No Gemini Integration ✓

**Evidence to verify in UI:**
- [ ] No "Enter Gemini API Key" field in sidebar
- [ ] No "Cloud mode" or "Cloud/Offline mode" toggle
- [ ] Sidebar shows: "🟢 Offline Mode Active"
- [ ] Engine badge always shows: "🧠 Local ML Model (Offline)"
- [ ] No reference to "Gemini 2.5 Flash"
- [ ] No option to switch between Gemini and local

**Code verification (in browser console):**
- No network requests to `generativeai.googleapis.com`
- No Google API calls

**Pass Criteria:**
- User cannot see or use any Gemini-related features
- Application runs without Gemini

---

### Test 3: Requirement 2 - ML Model Present ✓

**Steps:**
1. Upload the `test_video.mp4` (included in project)
2. Click "🔍 Analyze for Deepfakes"
3. Wait for analysis to complete

**Expected Results:**
- [ ] Analysis starts without errors
- [ ] Processing shows "Extracting frame & running inference…"
- [ ] Analysis completes in 3-10 seconds
- [ ] Results display with:
  - Binary verdict (REAL or MANIPULATED)
  - Confidence score (0-100%)
  - Engine badge: "🧠 Local ML Model (Offline)"
  - Forensic reasoning explanation
  - CPU time metric
  - Memory usage metric

**ML Model Verification:**
- [ ] Result contains reasonable confidence (not always 50/50)
- [ ] Reasoning explains detection (e.g., artifact types)
- [ ] No API calls made during analysis (check browser network tab)
- [ ] Process completes locally in reasonable time

**First Analysis Note:**
- First run will take 1-2 minutes (TensorFlow initializing + model download)
- Subsequent analyses: 3-10 seconds

---

### Test 4: Requirement 3 - Offline Availability ✓

#### Sub-test 4a: Works Without Internet
**Steps:**
1. Disconnect from internet (unplug network/disable WiFi)
2. Reload application or try new analysis
3. Upload video and analyze

**Expected Results:**
- [ ] Application continues to work
- [ ] Analysis completes successfully
- [ ] No error about "no internet connection"
- [ ] Results display normally
- [ ] History still accessible

**Pass Criteria:**
- Application works in airplane mode
- No network errors
- All features functional offline

#### Sub-test 4b: No External API Calls
**Steps:**
1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Perform analysis
4. Check network traffic

**Expected Results:**
- [ ] Zero network requests to external APIs
- [ ] Only local connections (localhost:8501)
- [ ] No calls to Google, AWS, or cloud services
- [ ] No API key transmission
- [ ] Browser cache/localStorage only for UI

**URLs to NOT appear in network traffic:**
- ❌ `generativeai.googleapis.com`
- ❌ `openai.com`
- ❌ Any AWS endpoints
- ❌ Any cloud provider endpoints

**Pass Criteria:**
- All computation is local
- No external dependencies during analysis

#### Sub-test 4c: Model Caching
**Steps:**
1. First analysis (model downloads)
2. Monitor `~/.truthlens/models/` directory
3. Perform second analysis (should use cache)
4. Compare execution times

**Expected Results:**
- [ ] First analysis: 60-120 seconds (model download + inference)
- [ ] Second analysis: 3-10 seconds (cache hit)
- [ ] Model files present in `~/.truthlens/models/`
- [ ] File size: ~50-100MB
- [ ] No re-download on second run

---

### Test 5: User Interface

**Layout Tests:**
- [ ] Two-column layout works on desktop
- [ ] Upload area on left, results on right
- [ ] Sidebar collapses on narrow screens
- [ ] Dark theme applies correctly
- [ ] Glassmorphism effects visible

**Upload Functionality:**
- [ ] Drag-and-drop works
- [ ] File picker works
- [ ] Multiple formats accepted (MP4, AVI, MOV, etc.)
- [ ] Video preview shows
- [ ] File size displayed

**Results Display:**
- [ ] Verdict banner shows (red or green)
- [ ] Confidence bar visualizes percentage
- [ ] Color-coded: Red (Fake), Green (Real)
- [ ] Reasoning text readable
- [ ] Metrics displayed with icons

**Sidebar:**
- [ ] "Offline Mode Active" info visible
- [ ] History limit slider works
- [ ] Refresh button functional
- [ ] Clear history button functional
- [ ] Version info shown

---

### Test 6: Analysis History

**Steps:**
1. Perform 3-5 analyses
2. Scroll to "Analysis History" section
3. Test history controls

**Expected Results:**
- [ ] Previous analyses listed at bottom
- [ ] Most recent first
- [ ] Shows verdict (🔴 FAKE or 🟢 REAL)
- [ ] Shows confidence score
- [ ] Shows reasoning preview
- [ ] Shows CPU time
- [ ] Shows memory usage
- [ ] Shows timestamp

**History Controls:**
- [ ] Refresh button updates history
- [ ] Clear button removes all entries
- [ ] Slider controls how many to show (5-50)
- [ ] SQLite database creates: `database/truthlens.db`
- [ ] Data persists after restart

---

### Test 7: Error Handling

**Test 7a: Invalid Video File**
- [ ] Try uploading non-video file
- [ ] Expected: Error message, no analysis
- [ ] Error message helpful

**Test 7b: Corrupted Video**
- [ ] Try uploading empty/invalid video file
- [ ] Expected: "Frame extraction failed" error
- [ ] Error message helpful

**Test 7c: Very Small Video**
- [ ] Try video < 1 second
- [ ] Expected: Should still work or show error
- [ ] No crash

---

### Test 8: Performance Metrics

**CPU Time:**
- [ ] Should be 1000-5000ms for typical video
- [ ] Format: "X.X ms" (milliseconds)
- [ ] Measurable difference between analyses

**Memory Usage:**
- [ ] Should be 50-300MB depending on system
- [ ] Format: "X.X MB"
- [ ] No memory leak (doesn't grow indefinitely)

---

### Test 9: Offline ML Model Verification

**Test 9a: TensorFlow Availability**
- [ ] Check console for "TensorFlow model loaded"
- [ ] Analysis results contain "model_name" field
- [ ] Results are consistent (not random)

**Test 9b: Lightweight Fallback**
- [ ] If TensorFlow unavailable: Falls back to heuristics
- [ ] Lightweight mode still produces results
- [ ] Confidence ranges reasonable (not always 50%)

---

## 📊 TEST REPORT TEMPLATE

```
═══════════════════════════════════════════════════════════════════
                TRUTHLENS v2.0 TEST REPORT
═══════════════════════════════════════════════════════════════════

Date: _______________
Tester: _______________
Environment: Windows / Mac / Linux
Python Version: _______________

═══════════════════════════════════════════════════════════════════
REQUIREMENT VERIFICATION
═══════════════════════════════════════════════════════════════════

[✓] Req 1: Gemini Integration Removed
    - [ ] No API key input field
    - [ ] No cloud mode option
    - [ ] No Gemini references in UI
    - [ ] No API calls made
    Notes: _________________________________________________

[✓] Req 2: ML Model Added
    - [ ] Analysis completes successfully
    - [ ] Results show confidence/reasoning
    - [ ] Model inference works locally
    - [ ] Reasonable detection logic
    Notes: _________________________________________________

[✓] Req 3: Offline Availability
    - [ ] Works without internet
    - [ ] No external API calls
    - [ ] Model cached locally
    - [ ] Performance good
    Notes: _________________________________________________

═══════════════════════════════════════════════════════════════════
FUNCTIONALITY TESTS
═══════════════════════════════════════════════════════════════════

Application Startup:        [ ] Pass  [ ] Fail  [ ] N/A
Video Upload:              [ ] Pass  [ ] Fail  [ ] N/A
Analysis Execution:        [ ] Pass  [ ] Fail  [ ] N/A
Results Display:           [ ] Pass  [ ] Fail  [ ] N/A
History Tracking:          [ ] Pass  [ ] Fail  [ ] N/A
Error Handling:            [ ] Pass  [ ] Fail  [ ] N/A
UI/UX Quality:             [ ] Pass  [ ] Fail  [ ] N/A
Performance Metrics:       [ ] Pass  [ ] Fail  [ ] N/A
Offline Mode:              [ ] Pass  [ ] Fail  [ ] N/A

═══════════════════════════════════════════════════════════════════
ISSUES FOUND
═══════════════════════════════════════════════════════════════════

Issue 1: _____________________________________________
  Severity: [ ] Critical [ ] High [ ] Medium [ ] Low
  Steps to Reproduce: ___________________________________
  Expected: ____________________________________________
  Actual: ______________________________________________

Issue 2: _____________________________________________
  (repeat as needed)

═══════════════════════════════════════════════════════════════════
OVERALL ASSESSMENT
═══════════════════════════════════════════════════════════════════

Status:           [ ] ✅ PASS  [ ] ⚠️  CONDITIONAL  [ ] ❌ FAIL
Ready for Release: [ ] YES   [ ] NO
Notes:  __________________________________________________

═══════════════════════════════════════════════════════════════════
```

---

## 🎯 SUCCESS CRITERIA

### ALL Requirements Met ✓
- [ ] No Gemini API integration
- [ ] Local ML model running
- [ ] Works completely offline

### Application Quality ✓
- [ ] No syntax/runtime errors
- [ ] Responsive UI
- [ ] Reasonable inference speed (< 15 seconds)
- [ ] Persistent history
- [ ] Clear error messages

### User Experience ✓
- [ ] Intuitive interface
- [ ] Clear instructions
- [ ] Results understandable
- [ ] Metrics displayed
- [ ] Professional appearance

---

## 📝 TESTING NOTES

### Known First-Run Behavior
- First analysis: 1-2 minutes (TensorFlow init + model download)
- Subsequent: 3-10 seconds
- This is **expected and normal**

### Expected Analysis Results
- Real videos: Typically 60-90% confidence
- Deepfakes: Typically 70-95% confidence
- Varies based on video quality and GAN artifacts

### Offline Verification
- Test in airplane mode after first run
- Test with network disabled
- Verify no external requests in browser DevTools

---

## ✅ SIGN-OFF

When all tests pass and requirements verified:

**Application Status:** ✅ **PRODUCTION READY**

**Tested By:** _______________________
**Date:** _______________________
**Approved:** _______________________

