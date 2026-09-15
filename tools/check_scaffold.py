"""Check links and inert recipe; not electrical validation."""
import json
import re
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for path in root.rglob('*.md'):
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' not in link and not link.startswith('#'):
            if not (path.parent / link.split('#')[0]).exists():
                raise SystemExit(f'Broken link: {path}: {link}')
recipe = json.loads((root / 'recipes/example.simulation.json').read_text())
if recipe['simulation_only'] is not True or recipe['steps'] != []:
    raise SystemExit('Example must remain non-executable')
print('Scaffold checks passed; no hardware validation performed.')
