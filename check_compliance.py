import os

checks = {}

# Check analyzer.py doesn't import gemini
with open(os.path.join('services', 'analyzer.py'), encoding='utf-8') as f:
    analyzer_code = f.read()
    checks['Gemini NOT in analyzer'] = 'gemini' not in analyzer_code.lower()

# Check app.py doesn't import gemini
with open('app.py', encoding='utf-8') as f:
    app_code = f.read()
    has_gemini = 'gemini_service' in app_code or 'analyze_with_gemini' in app_code
    checks['Gemini NOT in app.py'] = not has_gemini

# Check ml_model.py has no external API calls
with open(os.path.join('services', 'ml_model.py'), encoding='utf-8') as f:
    ml_code = f.read()
    has_api = 'requests.get' in ml_code or 'requests.post' in ml_code
    checks['No external API in ml_model'] = not has_api

# Check gemini_service.py existence
checks['gemini_service.py still exists'] = os.path.exists(os.path.join('services', 'gemini_service.py'))

# Check requirements.txt for google-generativeai
with open('requirements.txt', encoding='utf-8') as f:
    req_code = f.read()
    checks['No google-generativeai in requirements'] = 'google-generativeai' not in req_code

print('=== Requirements Compliance Check ===')
for check, val in checks.items():
    tag = 'PASS' if val else 'FAIL'
    print(f'  [{tag}] {check}')
