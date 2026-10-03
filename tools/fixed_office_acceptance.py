from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/'web/index.html').read_text(encoding='utf-8')
js=(root/'web/assets/app.js').read_text(encoding='utf-8')
assert 'data-view="growth"' not in html
assert 'navigator.geolocation' not in js and 'open-meteo' not in js
assert 'fixed-office.js' in html and 'characters.js' in html
for endpoint in ('/api/dashboard','/api/todos','/api/replay','/api/settings'):
    assert endpoint in js
print('Fixed office UI contract: PASS')
