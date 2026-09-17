"""Read the partial main schematic and check MCU rails, debug and UART wiring.

This limited endpoint/label checker is not the KiCad parser, ERC or DRC.
"""
import json
from datetime import date
from pathlib import Path
from check_front_panel import parse, children, one, point

ROOT = Path(__file__).resolve().parents[1]


def read_connections(path):
    root = parse(path.read_text())
    assert not children(root, 'sheet'), 'Only single-sheet drafts supported'
    parent = {}

    def find(p):
        parent.setdefault(p, p)
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

    for wire in children(root, 'wire'):
        a, b = [point(p) for p in children(one(wire, 'pts'), 'xy')]
        parent[find(a)] = find(b)
    labels = {}
    for label in children(root, 'label'):
        p = point(one(label, 'at'))
        assert p in parent, 'Unattached label'
        labels.setdefault(find(p), set()).add(label[1])
    assert all(len(v) == 1 for v in labels.values()), 'Conflicting net labels'
    nc = {point(one(x, 'at')) for x in children(root, 'no_connect')}
    libs = {s[1]: s for s in children(one(root, 'lib_symbols'), 'symbol')}
    nets, fields = {}, {}
    for symbol in children(root, 'symbol'):
        props = {p[1]: p[2] for p in children(symbol, 'property')}
        ref = props['Reference']
        if ref.startswith('#'):
            continue
        assert ref not in nets, 'Duplicate reference'
        fields[ref] = props
        nets[ref] = {}
        at = one(symbol, 'at')
        assert float(at[3]) == 0 and not children(symbol, 'mirror')
        x, y = point(at)
        for unit in children(libs[one(symbol, 'lib_id')[1]], 'symbol'):
            for pin in children(unit, 'pin'):
                dx, dy = point(one(pin, 'at'))
                p = round(x+dx, 4), round(y-dy, 4)
                n = one(pin, 'number')[1]
                assert n not in nets[ref]
                if p in nc:
                    assert p not in parent
                    nets[ref][n] = None
                else:
                    assert p in parent and find(p) in labels, f'Dangling {ref}.{n}'
                    nets[ref][n] = next(iter(labels[find(p)]))
    return nets, fields


def main():
    base = ROOT/'hardware/controller'
    nets, fields = read_connections(base/'kicad/controller-core-reva.kicad_sch')
    v, g = '3V3_CORE', 'GND_UI'
    assert len(nets['U101']) == 64 and len(nets['U201']) == 41
    # Independent checks against ST DS12589 LQFP64 supply / debug pin table.
    for pin in (1,13,19,20,32,48,64):
        assert nets['U101'][str(pin)] == v, f'STM power pad {pin}'
    for pin in (12,18,31,47,63):
        assert nets['U101'][str(pin)] == g, f'STM ground pad {pin}'
    for pin, net in {7:'STM_NRST',43:'STM_TX_RAW',44:'ESP_TO_STM',49:'STM_SWDIO',
                     50:'STM_SWCLK',56:'STM_SWO',61:'STM_BOOT0',27:'UI_PWR_EN'}.items():
        assert nets['U101'][str(pin)] == net
    assert nets['U201']['2'] == v
    for pin in (1,40,41):
        assert nets['U201'][str(pin)] == g, f'ESP ground/EP pad {pin}'
    for pin in (28,29,30):
        assert nets['U201'][str(pin)] is None, 'Do not use octal PSRAM pins'
    for pin, net in {3:'ESP_EN',27:'ESP_BOOT0',10:'ESP_TX_RAW',11:'STM_TO_ESP',
                     4:'KEY_SDA',5:'KEY_SCL',6:'KEY_INT_N',7:'BL_RAW',12:'RST_RAW',
                     17:'DC_RAW',18:'CS_RAW',19:'MOSI_RAW',20:'SCLK_RAW'}.items():
        assert nets['U201'][str(pin)] == net
    expected_link = ['3V3_UI',g,'LCD_SCLK',g,'LCD_MOSI',g,'LCD_CS_N','LCD_DC',
                     'LCD_RST_N','LCD_BL_PWM','KEY_SCL','KEY_SDA','KEY_INT_N',g,g,None]
    assert nets['J104'] == dict(zip(map(str, range(1,17)), expected_link))
    for ref,a,b in [('R211','STM_TX_RAW','STM_TO_ESP'),('R212','ESP_TX_RAW','ESP_TO_STM'),
                    ('R213','SCLK_RAW','LCD_SCLK'),('R214','MOSI_RAW','LCD_MOSI'),
                    ('R215','CS_RAW','LCD_CS_N'),('R216','DC_RAW','LCD_DC'),
                    ('R217','RST_RAW','LCD_RST_N'),('R218','BL_RAW','LCD_BL_PWM')]:
        assert nets[ref] == {'1':a,'2':b}
        assert fields[ref]['Value'] == '33'
    for ref, val, a, b in [('R101','10k',v,'STM_NRST'),('C101','100nF','STM_NRST',g),
                           ('R102','10k','STM_BOOT0',g),('R201','10k',v,'ESP_EN'),
                           ('C201','1uF','ESP_EN',g),('R202','10k',v,'ESP_BOOT0')]:
        assert nets[ref] == {'1':a,'2':b} and fields[ref]['Value'] == val
    for ref in [f'C{i}' for i in range(102,112)] + ['C202','C203']:
        assert nets[ref] == {'1':v,'2':g}, f'Decoupling missing at {ref}'
    assert nets['J101'] == {'1':'12V_ISO_RAW','2':g}
    assert nets['F301'] == {'1':'12V_ISO_RAW','2':'12V_FUSED'}
    assert nets['D301'] == {'2':'12V_FUSED','1':'12V_PROTECTED'}
    assert nets['D302'] == {'2':g,'1':'12V_PROTECTED'}
    assert nets['U301'] == {'1':v,'2':'12V_PROTECTED','3':'12V_PROTECTED',
                            '6':'BST_NODE','5':'SW_NODE','4':g}
    assert nets['C303'] == {'1':'BST_NODE','2':'SW_NODE'}
    assert nets['L301'] == {'1':'SW_NODE','2':v}
    for ref in ('C304','C305','C306'):
        assert nets[ref] == {'1':v,'2':g}
    assert nets['U302'] == {'1':v,'2':g,'3':'UI_PWR_EN','6':'3V3_UI',
                            '5':'3V3_UI','4':'UI_RISE'}
    assert nets['R301'] == {'1':v,'2':'UI_PWR_EN'}
    assert nets['C307'] == {'1':'UI_RISE','2':g}
    assert nets['C308'] == {'1':v,'2':g}
    assert nets['C309'] == {'1':'3V3_UI','2':g}
    exported = json.loads((base/'design-nets.json').read_text())
    assert nets == {c['reference']:c['pins'] for c in exported['components']}

    catalog = json.loads((ROOT/'hardware/assembly/parts-catalog.json').read_text())['parts']
    by_code = {p['lcsc']:p for p in catalog.values()}
    for board, path in [('main', base/'kicad/controller-core-reva.kicad_sch'),
                        ('front', ROOT/'hardware/front-panel/kicad/front-panel-reva.kicad_sch')]:
        _, props = read_connections(path)
        matched = 0
        for ref, p in props.items():
            code = p.get('lcsc')
            if not code:
                assert ref.startswith(('J','SW')), f'Unsourced electronic part {board}:{ref}'
                continue
            part = by_code[code]
            assert p['mpn'] == part['mpn'] and p['Footprint'] == part['footprint']
            assert part['stock_observed'] > 0, f'No stock at last check: {code}'
            checked = date.fromisoformat(part['stock_checked_on'])
            assert (date.today()-checked).days <= 7, f'Stale stock observation: {code}'
            matched += 1
        print(f'{board}: {matched}/{len(props)} positions have MPN + JLC code; remainder mechanical TBD.')
    print('Core rail, UART, debug and sourcing checks pass. This checker does not run native ERC/DRC.')


if __name__ == '__main__':
    main()
