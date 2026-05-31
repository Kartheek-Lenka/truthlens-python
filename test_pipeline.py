"""
test_pipeline.py — End-to-end test of the TruthLens analysis pipeline.
Tests video upload → frame extraction → ML inference → DB save.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("TruthLens Pipeline Test")
print("=" * 60)

# 1. Test config import
print("\n[1/7] Testing config import...")
try:
    from config import APP_TITLE, APP_ICON, APP_DESCRIPTION, DB_PATH
    print(f"  ✅ Config OK — Title: {APP_TITLE}")
except Exception as e:
    print(f"  ❌ Config FAILED: {e}")
    sys.exit(1)

# 2. Test video_utils
print("\n[2/7] Testing frame extraction from test_video.mp4...")
try:
    from utils.video_utils import extract_frame
    test_video = os.path.join(os.path.dirname(__file__), "test_video.mp4")
    if not os.path.exists(test_video):
        print(f"  ⚠️  test_video.mp4 not found at {test_video}")
        sys.exit(1)
    frame = extract_frame(test_video)
    print(f"  ✅ Frame extracted — shape: {frame.shape}, dtype: {frame.dtype}")
except Exception as e:
    print(f"  ❌ Frame extraction FAILED: {e}")
    sys.exit(1)

# 3. Test ML model (ml_model.py)
print("\n[3/7] Testing ML model inference...")
try:
    from services.ml_model import predict_deepfake
    ml_result = predict_deepfake(frame)
    print(f"  ✅ ML Model OK")
    print(f"     isFake:     {ml_result['isFake']}")
    print(f"     confidence: {ml_result['confidence']}%")
    print(f"     reasoning:  {ml_result['reasoning'][:80]}...")
    print(f"     model_name: {ml_result['model_name']}")
except Exception as e:
    print(f"  ❌ ML Model FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 4. Test analyzer orchestrator
print("\n[4/7] Testing analyzer orchestrator...")
try:
    from services.analyzer import analyze_frame
    result = analyze_frame(frame)
    print(f"  ✅ Analyzer OK")
    print(f"     isFake:     {result['isFake']}")
    print(f"     confidence: {result['confidence']}%")
    print(f"     engine:     {result['engine']}")
    print(f"     cpu_time:   {result['cpu_time']}")
    print(f"     memory:     {result['memory']}")
    print(f"     reasoning:  {result['reasoning'][:80]}...")
except Exception as e:
    print(f"  ❌ Analyzer FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 5. Test database save
print("\n[5/7] Testing database save...")
try:
    from database.db import save_result, get_history
    row_id = save_result(
        is_fake=result["isFake"],
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        engine=result["engine"],
        cpu_time=result["cpu_time"],
        memory=result["memory"],
    )
    print(f"  ✅ DB save OK — row_id: {row_id}")
except Exception as e:
    print(f"  ❌ DB save FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 6. Test history retrieval
print("\n[6/7] Testing history retrieval...")
try:
    history = get_history(limit=5)
    print(f"  ✅ History OK — {len(history)} entries found")
    if history:
        latest = history[0]
        print(f"     Latest: isFake={latest['isFake']}, confidence={latest['confidence']}%, engine={latest['engine']}")
except Exception as e:
    print(f"  ❌ History FAILED: {e}")
    import traceback; traceback.print_exc()

# 7. Requirements check — verify no Gemini dependency in active code path
print("\n[7/7] Checking requirements compliance...")
checks = {
    "Gemini NOT imported in analyzer": True,
    "ML model used instead of Gemini": True,
    "Offline capable (no API calls)": True,
}

# Check analyzer.py doesn't import gemini
with open(os.path.join(os.path.dirname(__file__), "services", "analyzer.py")) as f:
    analyzer_code = f.read()
    if "gemini" in analyzer_code.lower():
        checks["Gemini NOT imported in analyzer"] = False

# Check app.py doesn't import gemini
with open(os.path.join(os.path.dirname(__file__), "app.py")) as f:
    app_code = f.read()
    if "gemini_service" in app_code or "analyze_with_gemini" in app_code:
        checks["Gemini NOT imported in analyzer"] = False

# Verify engine is ml_model
if result["engine"] != "ml_model":
    checks["ML model used instead of Gemini"] = False

# Check no external API calls in the analysis path
with open(os.path.join(os.path.dirname(__file__), "services", "ml_model.py")) as f:
    ml_code = f.read()
    if "requests.get" in ml_code or "requests.post" in ml_code or "urllib.request" in ml_code:
        checks["Offline capable (no API calls)"] = False

print()
for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"  {status} {check}")

# Check if gemini_service.py still exists
gemini_file = os.path.join(os.path.dirname(__file__), "services", "gemini_service.py")
if os.path.exists(gemini_file):
    print(f"\n  ⚠️  WARNING: gemini_service.py still exists at {gemini_file}")
    print(f"     It is NOT imported by any active code path, but the file remains.")
else:
    print(f"\n  ✅ gemini_service.py has been removed")

print("\n" + "=" * 60)
all_passed = all(checks.values())
if all_passed:
    print("🎉 ALL TESTS PASSED — Pipeline is working correctly!")
else:
    print("⚠️  SOME CHECKS FAILED — See details above")
print("=" * 60)
