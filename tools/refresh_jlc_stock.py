"""Refresh the JLCPCB stock observations in hardware/assembly/parts-catalog.json.

Queries JLCPCB's public component list API (read-only, the same request the
parts search page makes) for every catalog part with an LCSC code and records
the stock, the orderable quantity where the catalog tracks it, and today's
date. The rest of each entry, including selection and JLC class, is left to a
person: the script only reports parts whose stock dropped to zero or whose
library type no longer matches the recorded class.

Run with any Python 3: python3 tools/refresh_jlc_stock.py
"""
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'hardware/assembly/parts-catalog.json'
API = ('https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/'
       'smtGood/selectSmtComponentList')
SOURCE = 'JLCPCB component list API (selectSmtComponentList), read-only'
CLASS = {'base': 'Basic', 'expand': 'Extended'}
# Evidence clauses that described an older stock reading and no longer apply.
STALE = ('stock', 'not observed', 'not exposed', 'requires refresh', 'quantity')


def lookup(code):
    body = json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 10}).encode()
    request = urllib.request.Request(API, data=body,
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    assert data.get('code') == 200, f'{code}: API answered {data.get("code")}'
    matches = [c for c in data['data']['componentPageInfo']['list']
               if c['componentCode'] == code]
    return matches[0] if matches else None


def evidence(old):
    """Swap the leading source clause for the API and drop stale stock notes."""
    kept = [c for c in (old or '').split('; ')[1:]
            if not any(word in c.lower() for word in STALE)]
    return '; '.join([SOURCE]+kept)


def main():
    text = CATALOG.read_text()
    catalog = json.loads(text)
    today = date.today().isoformat()
    warnings = []
    refreshed = 0
    for key, part in catalog['parts'].items():
        code = part.get('lcsc')
        if not code:
            continue
        found = lookup(code)
        time.sleep(0.3)
        if found is None:
            warnings.append(f'{key} {code}: not listed by JLCPCB')
            continue
        if found['componentModelEn'] != part['mpn']:
            warnings.append(f'{key} {code}: JLCPCB lists {found["componentModelEn"]}, '
                            f'catalog has {part["mpn"]}')
        part['stock_observed'] = found['stockCount'] or 0
        if 'available_order_qty_observed' in part:
            # JLCPCB reports reservations beyond stock as a negative quantity.
            part['available_order_qty_observed'] = max(0, found['canPresaleNumber'] or 0)
        part['stock_checked_on'] = today
        part['stock_evidence'] = evidence(part.get('stock_evidence'))
        refreshed += 1
        listed = CLASS.get(found['componentLibraryType'], found['componentLibraryType'])
        if part.get('jlc_class') != listed:
            warnings.append(f'{key} {code}: JLCPCB class {listed}, catalog has '
                            f'{part.get("jlc_class")}')
        if not part['stock_observed']:
            warnings.append(f'{key} {code}: no stock ({part["selection"]})')
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False)+'\n')
    print(f'{refreshed} parts refreshed on {today}.')
    for line in warnings:
        print('  '+line)


if __name__ == '__main__':
    main()
