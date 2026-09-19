#!/usr/bin/env python3
"""Autoroute the remaining SELV nets with Freerouting and store the result.

Run with KiCad's Python after route_controller_pcb.py. The reviewed scripted
copper is exported as fixed wiring; the mains domain and every Mains-class net
are withheld, so Freerouting only touches SELV nets. The new tracks and vias are
written to hardware/controller/routing/selv-autoroute.json, which
route_controller_pcb.py replays. Freerouting itself is not needed to rebuild the
board, only to regenerate that file after placement changes.
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'hardware/controller'
BOARD_PATH = BASE / 'kicad/controller-core-reva.kicad_pcb'
OUTPUT = BASE / 'routing/selv-autoroute.json'
FREEROUTING = os.environ.get('FREEROUTING', '/Applications/freerouting.app/Contents/MacOS/freerouting')
PASSES = int(os.environ.get('FREEROUTING_PASSES', '40'))

# Mains side of the barrier band drawn by layout_controller_pcb.py. The band
# itself is already a keepout; this keeps SELV copper out of the domain behind it.
MAINS_DOMAIN_UM = [(55000, -64000), (141600, -64000), (141600, -135200),
                   (55000, -135200), (55000, -64000)]


def prepare_dsn(text):
    points = '  '.join(f'{x} {y}' for x, y in MAINS_DOMAIN_UM)
    keepouts = ''.join(f'(keepout "mains domain" (polygon {layer} 0  {points}))\n    '
                       for layer in ('F.Cu', 'B.Cu'))
    assert '    (plane /GND_UI' in text
    text = text.replace('    (plane /GND_UI', '    ' + keepouts + '(plane /GND_UI', 1)
    mains_nets = re.search(r'\(class Mains ([^(]*)\(', text).group(1).split()
    for name in mains_nets:
        text, count = re.subn(r'\n    \(net ' + re.escape(name) + r'\n      \(pins [^)]*\)\n    \)',
                              '', text)
        assert count == 1, name
    return text, mains_nets


def signature(item):
    if isinstance(item, pcb.PCB_VIA):
        return ('via', item.GetNetname(), item.GetPosition().x, item.GetPosition().y)
    return ('track', item.GetNetname(), item.GetLayer(), item.GetStart().x, item.GetStart().y,
            item.GetEnd().x, item.GetEnd().y)


def main():
    board = pcb.LoadBoard(str(BOARD_PATH))
    existing = {signature(item) for item in board.GetTracks()}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assert pcb.ExportSpecctraDSN(board, str(tmp / 'board.dsn'))
        text, withheld = prepare_dsn((tmp / 'board.dsn').read_text())
        (tmp / 'selv.dsn').write_text(text)
        subprocess.run([FREEROUTING, '--gui.enabled=false', '-de', str(tmp / 'selv.dsn'),
                        '-do', str(tmp / 'selv.ses'), '-mp', str(PASSES), '-mt', '1'],
                       check=True)
        assert pcb.ImportSpecctraSES(board, str(tmp / 'selv.ses'))

    tracks, vias = [], []
    mm = pcb.ToMM
    for item in board.GetTracks():
        if signature(item) in existing:
            continue
        assert item.GetNetname() not in withheld, f'Mains net autorouted: {item.GetNetname()}'
        if isinstance(item, pcb.PCB_VIA):
            vias.append({'net': item.GetNetname(),
                         'at': [round(mm(item.GetPosition().x), 4), round(mm(item.GetPosition().y), 4)],
                         'diameter': round(mm(item.GetWidth(pcb.F_Cu)), 4),
                         'drill': round(mm(item.GetDrill()), 4)})
        else:
            tracks.append({'net': item.GetNetname(), 'layer': board.GetLayerName(item.GetLayer()),
                           'start': [round(mm(item.GetStart().x), 4), round(mm(item.GetStart().y), 4)],
                           'end': [round(mm(item.GetEnd().x), 4), round(mm(item.GetEnd().y), 4)],
                           'width': round(mm(item.GetWidth()), 4)})
    tracks.sort(key=lambda t: (t['net'], t['layer'], t['start'], t['end']))
    vias.sort(key=lambda v: (v['net'], v['at']))
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps({
        'status': 'autorouted_pending_review_not_fabricable',
        'tool': 'Freerouting v2.4.1, single thread',
        'passes': PASSES,
        'withheld_mains_nets': withheld,
        'tracks': tracks,
        'vias': vias,
    }, indent=1) + '\n')
    print(f'{len(tracks)} tracks and {len(vias)} vias written to {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
