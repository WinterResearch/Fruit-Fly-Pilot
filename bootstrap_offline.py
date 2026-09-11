"""Unpack the user-downloaded Linux wheels into this project only."""
from pathlib import Path
import os
import re
import zipfile

ROOT = Path(__file__).resolve().parent
target = ROOT / '.deps'
target.mkdir(exist_ok=True)
for wheel in (ROOT / 'downloads').glob('*.whl'):
    print('Unpacking', wheel.name)
    with zipfile.ZipFile(wheel) as z:
        z.extractall(target)
for archive in (ROOT / 'downloads').glob('*headless*.zip'):
    with zipfile.ZipFile(archive) as z:
        z.extractall(target)
for base, dirs, files in os.walk(target):
    for name in files:
        p = Path(base) / name
        if name in ('headless_shell', 'chrome_crashpad_handler', 'node') or name.startswith('ffmpeg-'):
            p.chmod(p.stat().st_mode | 0o111)

# Bundle the pinned self-contained Three.js module into a classic script. This
# keeps the showcase usable by double-clicking index.html, without a server.
src = ROOT / 'web/vendor/three.module.js'
if src.exists():
    code = src.read_text()
    match = re.search(r'export\s*\{([^}]+)\};?\s*$', code)
    if not match:
        raise RuntimeError('Unexpected Three.js export format')
    props = []
    for entry in match.group(1).split(','):
        parts = entry.strip().split(' as ')
        props.append((parts[-1] + ':' + parts[0]).strip())
    bundled = '(function(){\n' + code[:match.start()] + '\nwindow.THREE={' + ','.join(props) + '};\n})();\n'
    (src.parent / 'three.global.js').write_text(bundled)
print('Project dependencies prepared.')

