"""Cache public EasyEDA/LCSC models for the placement audit (read-only HTTP).

Raw third-party library files stay in the supplied scratch directory, not the repo.
Run: python tools/fetch_jlc_placement_models.py CACHE_DIRECTORY
"""
import csv
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://easyeda.com/api/products/{}/svgs'


def main():
    cache = Path(sys.argv[1])
    cache.mkdir(parents=True, exist_ok=True)
    codes = sorted({p['lcsc'] for board in ('controller', 'front-panel')
                    for p in csv.DictReader((ROOT/'hardware'/board/'bom-draft.csv').open())
                    if p['lcsc']})

    def fetch(code):
        path = cache/f'{code}-svg.json'
        if path.exists():
            return code, 'cached'
        try:
            request = urllib.request.Request(API.format(code), headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=40) as response:
                data = response.read()
            parsed = json.loads(data)
            path.write_bytes(data)
            time.sleep(.25)
            if not parsed.get('success') or not parsed.get('result'):
                return code, 'no model (response cached)'
            return code, 'downloaded'
        except Exception as error:
            return code, str(error)

    failed = False
    with ThreadPoolExecutor(max_workers=1) as pool:
        for code, status in pool.map(fetch, codes):
            print(code, status, flush=True)
            failed |= status not in ('cached', 'downloaded', 'no model (response cached)')
    if failed:
        raise SystemExit('Some models could not be fetched; audit will mark them unresolved.')


if __name__ == '__main__':
    main()
