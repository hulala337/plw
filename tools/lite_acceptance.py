from pathlib import Path
import re
root = Path(__file__).resolve().parents[1]
html = (root / 'web/index.html').read_text(encoding='utf-8')
js = (root / 'web/assets/lite.js').read_text(encoding='utf-8')
ids = set(re.findall(r'id="([^"]+)"', html))
required = set(re.findall(r"\$\('([^']+)'\)", js))
assert not required - ids, required - ids
assert 'visual-v36' not in html and '/assets/app.js' not in html
for endpoint in ('/api/dashboard', '/api/replay', '/api/todos', '/api/settings', '/api/forget-today', '/api/export/csv', '/api/export/xlsx'):
    assert endpoint in js or endpoint in html, endpoint
print('Lightweight UI contract: PASS')
