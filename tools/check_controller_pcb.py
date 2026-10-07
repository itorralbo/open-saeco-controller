"""Geometric checks on the routed controller PCB that the netlist cannot see.

Buck input capacitors (issue #3): each converter needs a bulk ceramic and a
small high-frequency one whose pads sit next to its VIN and GND pins, so the
pulsed input current closes in a small loop. For every converter in
DECOUPLING the nearest capacitor of each class, measured pin to pad in a
straight line on both its VIN and GND sides, must be within the limit.

  python3 check_controller_pcb.py              check the board
  python3 check_controller_pcb.py --self-test  also check that the faults
                                               the rules exist for are caught

Run with KiCad's bundled Python from tools/, after route_controller_pcb.py.
"""
import math
import sys
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT/'hardware/controller/kicad/controller-core-reva.kicad_pcb'

# Converter: VIN and GND pads, and per class the capacitance window (uF) and
# the farthest a capacitor's pad may be from its pin (mm). Diodes DS41326:
# "Place the VIN capacitors as close to the device as possible."
DECOUPLING = {
    'U301': {'vin': '3', 'gnd': '4',
             'classes': {'bulk': ((4.7, 100.0), 5.0), 'hf': ((0.01, 1.0), 3.0)}},
    'U303': {'vin': '3', 'gnd': '4',
             'classes': {'bulk': ((4.7, 100.0), 5.0), 'hf': ((0.01, 1.0), 3.0)}},
}
SI = {'p': 1e-6, 'n': 1e-3, 'u': 1.0, 'µ': 1.0}


def microfarads(value):
    head = value.split('/')[0].strip()
    for unit, scale in SI.items():
        if head.endswith(unit + 'F'):
            try:
                return float(head[:-2]) * scale
            except ValueError:
                return None
    return None


def at(pad):
    p = pad.GetPosition()
    return pcb.ToMM(p.x), pcb.ToMM(p.y)


def check(board):
    errors = []
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, spec in DECOUPLING.items():
        pads = {p.GetNumber(): p for p in fps[ref].Pads()}
        vin, gnd = pads[spec['vin']], pads[spec['gnd']]
        vnet, gnet = vin.GetNetname(), gnd.GetNetname()
        found = {}
        for f in fps.values():
            if not f.GetReference().startswith('C'):
                continue
            cp = {p.GetNetname(): p for p in f.Pads()}
            if set(cp) != {vnet, gnet}:
                continue
            uf = microfarads(f.GetValue())
            if uf is None:
                continue
            reach = max(math.dist(at(vin), at(cp[vnet])), math.dist(at(gnd), at(cp[gnet])))
            for name, ((lo, hi), _) in spec['classes'].items():
                if lo <= uf <= hi and reach < found.get(name, (math.inf, ''))[0]:
                    found[name] = (reach, f.GetReference())
        for name, (_, limit) in spec['classes'].items():
            reach, cap = found.get(name, (math.inf, None))
            if cap is None:
                errors.append(f'{ref}: no {name} input capacitor across {vnet} and {gnet}')
            elif reach > limit:
                errors.append(f'{ref}: nearest {name} input capacitor {cap} is {reach:.1f} mm '
                              f'from VIN/GND, limit {limit:g} mm')
    return errors


def self_test():
    """Each rule must catch the layout it was written against."""
    def moved(ref, xy):
        board = pcb.LoadBoard(str(BOARD_PATH))
        board.FindFootprintByReference(ref).SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
        return check(board)

    cases = [
        # C315 removed from U301's pins: only C301, 30 mm of trace away, is left.
        (lambda: moved('C315', (20.0, 125.0)), 'U301: nearest bulk input capacitor C301'),
        # C316 away from U303: it had no high-frequency capacitor at all.
        (lambda: moved('C316', (20.0, 125.0)), 'U303: nearest hf input capacitor C316'),
        # C310 back where it was, ground through two vias.
        (lambda: moved('C310', (117.5, 5.0)), 'U303: nearest bulk input capacitor C310'),
    ]
    failures = []
    for run, expected in cases:
        found = run()
        if not any(expected in e for e in found):
            failures.append(f'self-test: expected "{expected}", got {found}')
    return failures


def main(argv):
    errors = check(pcb.LoadBoard(str(BOARD_PATH)))
    if '--self-test' in argv:
        errors += self_test()
    for e in errors:
        print('ERROR', e)
    if errors:
        return 1
    print('Controller PCB geometry checks pass'
          + (' (with self-test).' if '--self-test' in argv else '.'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
