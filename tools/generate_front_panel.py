"""Generate the review-only front panel schematic and an independent SVG preview.

Standard library only. Does not generate a PCB or manufacturing files. After manual
KiCad edits, stop using this generator or port those edits here before regeneration.
"""
import csv
import html
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/front-panel'
PROJECT = 'front-panel-reva'
PARTS = json.loads((ROOT/'hardware/assembly/parts-catalog.json').read_text())['parts']
VCC, GND = '3V3_UI', 'GND_UI'
UPLINK = [VCC, GND, 'LCD_SCLK', GND, 'LCD_MOSI', GND,
          'LCD_CS_N', 'LCD_DC', 'LCD_RST_N', 'LCD_BL_PWM',
          'KEY_SCL', 'KEY_SDA', 'KEY_INT_N', GND, GND, None]
DISPLAY = [VCC, GND, 'LCD_MOSI', 'LCD_SCLK', 'LCD_CS_N',
           'LCD_DC', 'LCD_RST_N', 'LCD_BL_PWM']
# SWn -> original key position (hardware/front-panel/mechanical.md). P0-P3 (left side
# of U1) serve the left column and PB8; P4-P6 (right side, bottom to top) serve the
# right column bottom to top, so both fan-outs route without crossings on F.Cu.
KEYS = ['PB1', 'PB2', 'PB3', 'PB8', 'PB4/PB6', 'PB5', 'PB7']
SWITCH_FP = 'OpenSaeco:SW_HRO_K2-1102SP-A4SC-04'


def uid(name):
    return str(uuid5(NAMESPACE_URL, f'open-saeco/{PROJECT}/{name}'))


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def effects(size=1.0, justify='', hide=False):
    return (f'(effects (font (size {size} {size}))'
            + (f' (justify {justify})' if justify else '')
            + (' hide' if hide else '') + ')')


def prop(name, value, x, y, hide=False):
    return f'(property {q(name)} {q(value)} (at {x} {y} 0) {effects(hide=hide)})'


# Pins: number, name, electrical type, x, y (library coordinates), angle.
def connector(count):
    return [(str(i + 1), str(i + 1), 'passive', -7.62,
             (count - 1) * 1.905 - i * 3.81, 0) for i in range(count)]


IC_LEFT = [('16', 'VCC', 'power_in'), ('8', 'GND', 'power_in'),
           ('14', 'SCL', 'input'), ('15', 'SDA', 'bidirectional'),
           ('13', '~{INT}', 'open_collector'), ('1', 'A0', 'input'),
           ('2', 'A1', 'input'), ('3', 'A2', 'input')]
IC_RIGHT = [(str(pin), f'P{i}', 'bidirectional')
            for i, pin in enumerate([4, 5, 6, 7, 9, 10, 11, 12])]
IC_PINS = [(n, name, kind, side * 12.7, 13.335 - i * 3.81,
            0 if side < 0 else 180)
           for side, pins in [(-1, IC_LEFT), (1, IC_RIGHT)]
           for i, (n, name, kind) in enumerate(pins)]
TWO = [('1', '~', 'passive', -5.08, 0, 0),
       ('2', '~', 'passive', 5.08, 0, 180)]
DEFS = {'R': (TWO, 2.54, 1.0), 'C': (TWO, 2.54, 1.5),
        'SW': (TWO, 2.54, 1.5), 'J16': (connector(16), 5.08, 31.75),
        'J8': (connector(8), 5.08, 16.51),
        'TCA9534': (IC_PINS, 10.16, 16.51)}
DEFS['PWR_FLAG'] = ([('1', 'pwr', 'power_out', -5.08, 0, 0)], 2.54, 1.27)
DEFS['LED'] = ([('1', 'K', 'passive', -5.08, 0, 0),
                ('2', 'A', 'passive', 5.08, 0, 180)], 2.54, 1.5)


def body(kind, width, height):
    stroke = '(stroke (width 0.254) (type default))'
    if kind == 'LED':
        return (f'(polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) {stroke} (fill (type none)))'
                f'(polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) {stroke} (fill (type none)))'
                f'(polyline (pts (xy -2.54 0) (xy 2.54 0)) {stroke} (fill (type none)))')
    if kind in ('C', 'SW'):
        paths = ([(-2.54, 0, -0.635, 0), (0.635, 0, 2.54, 0),
                  (-0.635, -1.5, -0.635, 1.5), (0.635, -1.5, 0.635, 1.5)]
                 if kind == 'C' else [(-2.54, 0, 1.9, 1.5)])
        return ''.join(f'(polyline (pts (xy {a} {b}) (xy {c} {d})) '
                       f'{stroke} (fill (type none)))' for a, b, c, d in paths)
    return (f'(rectangle (start {-width} {height}) (end {width} {-height})'
            f' {stroke} (fill (type background)))')


def library(kind):
    pins, width, height = DEFS[kind]
    physical = 'no' if kind == 'PWR_FLAG' else 'yes'
    pin_text = ''.join(
        f'(pin {typ} line (at {x} {y} {angle}) (length 2.54)'
        f' (name {q(name)} {effects(0.9)}) (number {q(n)} {effects(0.8)}))'
        for n, name, typ, x, y, angle in pins)
    return (f'(symbol "OpenSaeco:{kind}" (pin_names (offset 0.508))'
            f' (in_bom {physical}) (on_board {physical})'
            f' {prop("Reference", kind[0], 0, height + 3)}'
            f' {prop("Value", kind, 0, height + 1.5)}'
            f' (symbol "{kind}_0_1" {body(kind, width, height)})'
            f' (symbol "{kind}_1_1" {pin_text}))')


components, objects, svg = [], [], []


def svg_text(x, y, text, size=1.05, anchor='start', color='#213b50'):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" '
               f'text-anchor="{anchor}" fill="{color}">{html.escape(text)}</text>')


def note(text, x, y, size=1.5):
    objects.append(f'(text {q(text)} (at {x} {y} 0) '
                   f'{effects(size, "left")} (uuid {uid(text)}))')
    svg_text(x, y, text, size)


def add(ref, kind, value, x, y, nets, footprint='', status='candidate', part_key=None):
    pins, width, height = DEFS[kind]
    # Every pin and wire endpoint must land on KiCad's 50 mil connection grid.
    # Odd/even pin counts give different symbol-center offsets.
    x = round(round(x / 1.27) * 1.27, 4)
    y = round(round((y - pins[0][4]) / 1.27) * 1.27 + pins[0][4], 4)
    physical = 'no' if kind == 'PWR_FLAG' else 'yes'
    assert len(nets) == len(pins)
    key = part_key or (f'{kind}:{value.split(" / ")[0]}' if kind in ('R', 'C') else value)
    part = PARTS.get(key)
    if part:
        assert footprint == part['footprint'], f'Package mismatch for {ref}'
    sourcing = {field: part[field] if part else '' for field in
                ('manufacturer', 'mpn', 'lcsc', 'jlc_class', 'pcba_type')}
    properties = [prop('Reference', ref, x, y-height-5),
                  prop('Value', value, x, y-height-2.5),
                  prop('Footprint', footprint, x, y, True)]
    properties += [prop(field, val, x, y, True) for field, val in sourcing.items() if val]
    objects.append(
        f'(symbol (lib_id "OpenSaeco:{kind}") (at {x} {y} 0) (unit 1)'
        f' (in_bom {physical}) (on_board {physical}) (dnp no) (uuid {uid(ref)})'
        + ''.join(properties)
        + ''.join(f'(pin {q(p[0])} (uuid {uid(ref+"/"+p[0])}))' for p in pins)
        + f'(instances (project "{PROJECT}" (path "/{uid("root")}"'
          f' (reference {q(ref)}) (unit 1)))))')
    if kind == 'C':
        svg.append(f'<path d="M {x-width} {y} H {x-.635} M {x+.635} {y} H {x+width}'
                   f' M {x-.635} {y-1.5} V {y+1.5} M {x+.635} {y-1.5} V {y+1.5}"'
                   ' stroke="#213b50" stroke-width=".25" fill="none"/>')
    elif kind == 'SW':
        svg.append(f'<path d="M {x-width} {y} L {x+1.9} {y-1.5}"'
                   ' stroke="#213b50" stroke-width=".25" fill="none"/>')
    elif kind == 'LED':
        svg.append(f'<path d="M {x-width} {y} H {x+width} M {x+1.27} {y-1.27} V {y+1.27} L {x-1.27} {y} Z'
                   f' M {x-1.27} {y-1.27} V {y+1.27}" stroke="#213b50" stroke-width=".25" fill="none"/>')
    else:
        svg.append(f'<rect x="{x-width}" y="{y-height}" width="{2*width}" '
                   f'height="{2*height}" fill="#f3f7fa" stroke="#213b50" stroke-width=".25"/>')
    svg_text(x, y-height-5, ref, anchor='middle')
    svg_text(x, y-height-2.5, value, anchor='middle')
    for (n, name, typ, dx, dy, angle), net in zip(pins, nets):
        px, py = round(x+dx, 4), round(y-dy, 4)
        sign = -1 if dx < 0 else 1
        ex = round(px+sign*2.54, 4)
        svg.append(f'<path d="M {x+sign*width} {py} H {ex}" '
                   'stroke="#27856d" stroke-width=".22"/>')
        if name != '~':
            svg_text(x+sign*(width-0.7), py+0.3, name.replace('~{INT}', '/INT'),
                     .9, 'start' if sign < 0 else 'end')
            svg_text(px-sign*.6, py-.5, n, .65, 'middle')
        if net is None:
            objects.append(f'(no_connect (at {px} {py}) (uuid {uid(ref+n+"nc")}))')
            svg_text(ex, py+.3, 'NC', .85)
            continue
        objects.append(f'(wire (pts (xy {px} {py}) (xy {ex} {py}))'
                       f' (stroke (width 0) (type default)) (uuid {uid(ref+n+"wire")}))')
        # Left-end labels face left; right-end labels face right.
        objects.append(f'(label {q(net)} (at {ex} {py} {180 if sign < 0 else 0})'
                       f' {effects(.9, "right bottom" if sign < 0 else "left bottom")} (uuid {uid(ref+n+"label")}))')
        svg_text(ex+sign*.4, py-.5, net, .9, 'end' if sign < 0 else 'start', '#23745f')
    if physical == 'no':
        return
    components.append({'reference': ref, 'value': value, 'footprint': footprint,
                       'status': status, **sourcing,
                       'pins': dict(zip((p[0] for p in pins), nets))})


def passive(ref, kind, value, x, y, net1, net2):
    fp = {'R': 'Resistor_SMD:R_0603_1608Metric',
          'C': 'Capacitor_SMD:C_0603_1608Metric'}.get(kind, '')
    add(ref, kind, value, x, y, [net1, net2], fp,
        'mechanical_TBD' if kind == 'SW' else 'candidate')


def main():
    note('OPEN SAECO / FRONTAL Rev A.0 — BORRADOR ELÉCTRICO', 12, 12, 2.5)
    note('Contorno y pulsadores según hardware/front-panel/mechanical.md. Borrador en revisión. Validación: tools/validate_kicad.py.', 12, 19)
    note('01 / Enlace nuevo a ESP32', 12, 30)
    add('J1', 'J16', 'UI_LINK / IDC 2x8 2.54mm', 55, 72, UPLINK,
        'Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical',
        status='candidate', part_key='CONN:IDC_2X8_2.54')
    note('J1 NO corresponde a JP21 Saeco.', 12, 111)
    note('16 sin conectar. Vista eléctrica, no del cable.', 12, 116, 1.2)
    add('#FLG01', 'PWR_FLAG', 'External supply via J1', 75, 96, [VCC])
    add('#FLG02', 'PWR_FLAG', 'External return via J1', 75, 105, [GND])
    note('02 / Botones I2C — dirección 0x20', 116, 30)
    icnets = [VCC, GND, 'KEY_SCL', 'KEY_SDA', 'KEY_INT_N', GND, GND, GND]
    icnets += [f'KEY_{i}_N' for i in range(1, 8)] + ['LED_STBY_N']
    add('U1', 'TCA9534', 'TCA9534PWR', 164, 65, icnets,
        'Package_SO:TSSOP-16_4.4x5mm_P0.65mm')
    passive('C1', 'C', '100nF', 146, 98, VCC, GND)
    passive('C2', 'C', '1uF', 195, 98, VCC, GND)
    note('03 / Adaptador LCD SPI, lógica 3V3', 230, 30)
    add('J2', 'J8', 'LCD_ADAPTER / JST PH 8', 280, 63, DISPLAY,
        'Connector_JST:JST_PH_B8B-PH-K_1x08_P2.00mm_Vertical', part_key='CONN:JST_PH_8_V')
    note('Orden del cable PH 2,0 del módulo Waveshare 2": VCC GND DIN CLK CS DC RST BL.', 228, 97, 1.2)
    note('BL: entrada lógica de módulo; no LED desnudo.', 228, 92, 1.2)
    note('04 / Polarización y reserva de desacoplo', 322, 30)
    for ref, value, net1, net2, y in [
        ('R1', '4.7k', VCC, 'KEY_SCL', 43),
        ('R2', '4.7k', VCC, 'KEY_SDA', 56),
        ('R3', '10k', VCC, 'KEY_INT_N', 69),
        ('R4', '10k', VCC, 'LCD_CS_N', 82),
        ('R5', '10k', VCC, 'LCD_RST_N', 95),
        ('R6', '100k', 'LCD_BL_PWM', GND, 108)]:
        passive(ref, 'R', value, 361, y, net1, net2)
    passive('C3', 'C', '10uF', 260, 108, VCC, GND)
    note('05 / Siete pulsadores en las posiciones originales; P7 enciende el LED STBY (activo a 0)', 12, 130)
    for i, original in enumerate(KEYS, 1):
        x = 52 + ((i-1) % 4)*98
        y = 143 + ((i-1)//4)*60
        key, raw = f'KEY_{i}_N', f'SW_{i}_RAW'
        passive(f'R{10+i}', 'R', '10k / pull-up', x, y, VCC, key)
        passive(f'R{20+i}', 'R', '1k / serie', x, y+13, key, raw)
        add(f'SW{i}', 'SW', f'KEY {i} / {original}', x, y+26, [raw, GND], SWITCH_FP,
            part_key='SW:TACT_6X6X4.3_SMD')
        passive(f'C{10+i}', 'C', '100nF / filtro', x, y+39, key, GND)
    passive('R7', 'R', '470 / LED', 52 + 3*98, 203, VCC, 'LED_STBY_A')
    add('D1', 'LED', 'KT-0603R / STBY', 52 + 3*98, 216, ['LED_STBY_N', 'LED_STBY_A'],
        'LED_SMD:LED_0603_1608Metric', part_key='LED:RED_0603')
    note('LED: 3V3 - R7 - D1 - P7. P7 arranca como entrada: LED apagado hasta configurarlo.', 330, 236, 1.2)
    note('Entradas activas a 0. Los pulsadores son órdenes de UI, no interlocks ni corte de emergencia.', 12, 260)
    note('100nF: X7R; 1uF/10uF: X5R, temperatura y DC bias pendientes. SW: HRO K2-1102SP-A4SC-04, 6x6x4,3 mm.', 12, 267, 1.2)
    note('Vista SVG auxiliar del generador; no sustituye apertura, exportación de netlist y ERC en KiCad.', 12, 274, 1.2)
    write_outputs('Open Saeco front panel / REVIEW ONLY', preview='front-panel.svg')


def write_outputs(title, paper='A3', width=420, height=297, preview='core.svg'):
    schematic = (f'(kicad_sch (version 20231120) (generator "open_saeco_generator")'
                 f' (uuid {uid("root")}) (paper "{paper}")'
                 f' (title_block (title {q(title)})'
                 ' (date "2026-09-16") (rev "A.0-draft")'
                 ' (comment 1 "Draft under review: footprints assigned, layout in progress; see validation report."))'
                 ' (lib_symbols ' + '\n'.join(library(k) for k in DEFS) + ')\n'
                 + '\n'.join(objects) + '\n(sheet_instances (path "/" (page "1")))\n)\n')
    (OUT/'kicad').mkdir(parents=True, exist_ok=True)
    (OUT/'preview').mkdir(parents=True, exist_ok=True)
    (OUT/'kicad'/f'{PROJECT}.kicad_sch').write_text(schematic, encoding='utf-8')
    # Project-local symbols keep the embedded definitions reviewable/editable.
    symbols = '\n'.join(library(k).replace(f'"OpenSaeco:{k}"', q(k), 1) for k in DEFS)
    (OUT/'kicad/OpenSaeco.kicad_sym').write_text(
        '(kicad_symbol_lib (version 20231120) (generator "open_saeco_generator")\n'
        + symbols + '\n)\n', encoding='utf-8')
    (OUT/'kicad/sym-lib-table').write_text(
        '(sym_lib_table (version 7) (lib (name "OpenSaeco") (type "KiCad") '
        '(uri "${KIPRJMOD}/OpenSaeco.kicad_sym") (options "") (descr "Project draft symbols")))\n')
    project_path = OUT/'kicad'/f'{PROJECT}.kicad_pro'
    if not project_path.exists():
        project_path.write_text(json.dumps({
            'meta': {'filename': project_path.name, 'version': 1},
            'board': {'design_settings': {'drc_exclusions': []}},
            'erc': {'erc_exclusions': []}, 'net_settings': {'classes': [], 'meta': {'version': 0}},
            'libraries': {'pinned_footprint_libs': [], 'pinned_symbol_libs': []},
            'sheets': [[uid('root'), '']], 'text_variables': {}
        }, indent=2)+'\n')
    (OUT/'preview'/preview).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*4}" height="{height*4}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="white"/>'
        '<g font-family="Arial, sans-serif">' + '\n'.join(svg) + '</g></svg>\n', encoding='utf-8')
    with (OUT/'bom-draft.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, lineterminator='\n',
                                fieldnames=['reference', 'value', 'footprint', 'status',
                                            'manufacturer', 'mpn', 'lcsc', 'jlc_class', 'pcba_type'])
        writer.writeheader()
        writer.writerows({k: v for k, v in c.items() if k != 'pins'} for c in components)
    (OUT/'design-nets.json').write_text(json.dumps(
        {'status': 'review_only_not_fabricable', 'components': components},
        indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Generated {len(components)} components. KiCad/ERC validation still required.')


if __name__ == '__main__':
    main()
