#!/usr/bin/env python3
"""Give the controller board its four-layer JLCPCB stack-up.

Plain text edit of the .kicad_pcb, idempotent: it adds In1.Cu and In2.Cu to the
layer table and (re)writes the physical stack-up in the setup section. The
numbers are JLCPCB's default 1.6 mm four-layer build, JLC04161H-7628, as
published on https://jlcpcb.com/impedance (read 2026-09-23): 1 oz outer copper,
0.5 oz inner copper, 7628 prepreg under each outer layer and a 1.065 mm core.

Layer use (see hardware/controller/manufacturing.md):
  F.Cu    components and signals
  In1.Cu  GND_UI plane on the SELV side, 0.21 mm under F.Cu
  In2.Cu  3V3_CORE plane on the SELV side
  B.Cu    signals
No inner copper enters the mains domain.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'hardware/controller/kicad/controller-core-reva.kicad_pcb'

INNER_LAYERS = '\t\t(4 "In1.Cu" signal)\n\t\t(6 "In2.Cu" signal)\n'

PREPREG = '(type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02)'
STACKUP = f'''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" {PREPREG})
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 3" {PREPREG})
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "HAL lead-free")
\t\t\t(dielectric_constraints no)
\t\t)
'''


def main():
    text = BOARD.read_text()
    if '"In1.Cu" signal' not in text:
        text = text.replace('\t\t(0 "F.Cu" signal)\n', '\t\t(0 "F.Cu" signal)\n' + INNER_LAYERS, 1)
        assert '"In1.Cu" signal' in text, 'layer table not found'
    # Drop any earlier stack-up, then put ours first in (setup).
    text = re.sub(r'\t\t\(stackup\n.*?\n\t\t\)\n', '', text, count=1, flags=re.S)
    text = text.replace('\t(setup\n', '\t(setup\n' + STACKUP, 1)
    BOARD.write_text(text)
    print('Four-layer JLC04161H-7628 stack-up written.')


if __name__ == '__main__':
    main()
