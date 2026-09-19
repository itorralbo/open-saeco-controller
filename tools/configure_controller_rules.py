#!/usr/bin/env python3
"""Install the reviewed controller net classes in the KiCad project."""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / 'hardware/controller/kicad'
PROJECT = KICAD / 'controller-core-reva.kicad_pro'
BOARD = KICAD / 'controller-core-reva.kicad_pcb'
DRU = KICAD / 'controller-core-reva.kicad_dru'

# Provisional primary-SELV barrier from hardware/power/mains-stage.md. It is a
# design margin to be rechecked against the appliance standard before release.
MAINS_BARRIER_MM = 8.0
# Unused pins of mains connectors and netless mechanical holes are not SELV.
SELV = "B.NetClass != 'Mains' && B.NetName != '' && B.NetName != 'unconnected-*'"
DRU_RULES = f'''(version 1)

(rule "mains_functional_copper"
  (condition "A.NetClass == 'Mains' && B.NetClass == 'Mains' && A.Type != 'Pad' && B.Type != 'Pad'")
  (constraint clearance (min 2.5mm)))

(rule "mains_to_selv_clearance"
  (condition "A.NetClass == 'Mains' && {SELV}")
  (constraint clearance (min {MAINS_BARRIER_MM}mm)))

(rule "mains_to_selv_creepage"
  (condition "A.NetClass == 'Mains' && {SELV}")
  (constraint creepage (min {MAINS_BARRIER_MM}mm)))
'''

CLASS_RULES = {
    # Primary-side copper. The 1.2 mm class clearance is set by the 3.96 mm
    # pitch of the original VH mains connectors; copper between different
    # Mains nets is held to 2.5 mm and Mains-to-SELV to 8 mm by DRU_RULES.
    'Mains': {
        'clearance': 1.20, 'track_width': 2.50, 'via_diameter': 1.60,
        'via_drill': 0.80, 'diff_pair_width': 0.20, 'diff_pair_gap': 0.25,
        'diff_pair_via_gap': 0.25,
    },
    'Actuator': {
        'clearance': 0.25, 'track_width': 1.00, 'via_diameter': 1.00,
        'via_drill': 0.50, 'diff_pair_width': 0.20, 'diff_pair_gap': 0.25,
        'diff_pair_via_gap': 0.25,
    },
    'Power': {
        'clearance': 0.20, 'track_width': 0.50, 'via_diameter': 0.80,
        'via_drill': 0.40, 'diff_pair_width': 0.20, 'diff_pair_gap': 0.25,
        'diff_pair_via_gap': 0.25,
    },
    'Switching': {
        'clearance': 0.25, 'track_width': 0.60, 'via_diameter': 0.80,
        'via_drill': 0.40, 'diff_pair_width': 0.20, 'diff_pair_gap': 0.25,
        'diff_pair_via_gap': 0.25,
    },
    'USB': {
        'clearance': 0.20, 'track_width': 0.20, 'via_diameter': 0.60,
        'via_drill': 0.30, 'diff_pair_width': 0.20, 'diff_pair_gap': 0.20,
        'diff_pair_via_gap': 0.25,
    },
}

CLASS_NETS = {
    'Mains': [
        '/MAINS_L_IN', '/MAINS_L_FUSED', '/PSU_L_FUSED', '/MAINS_N',
        '/LOAD_L_ENABLED', '/PUMP_AC_A', '/PUMP_AC_B',
        '/GRINDER_DC_PLUS', '/GRINDER_DC_MINUS',
    ],
    'USB': [
        '/USB_DP_PORT', '/USB_DM_PORT', '/USB_DP_RAW', '/USB_DM_RAW',
        '/USB_DP_DEVICE', '/USB_DM_DEVICE',
    ],
    'Power': [
        '/12V_ISO_RAW', '/12V_FUSED', '/12V_PROTECTED', '/3V3_CORE', '/3V3_UI',
        '/USB_VBUS', '/USB_VBUS_FUSED',
    ],
    'Switching': [
        '/SW_NODE', '/BST_NODE', '/BREW_CPH', '/BREW_CPL', '/BREW_VCP',
    ],
    'Actuator': [
        '/24V_ACT_RAW', '/24V_BREW_FUSED', '/24V_BREW', '/24V_VALVE_FUSED',
        '/24V_VALVE', '/BREW_OUT1', '/BREW_OUT2', '/VALVE_RETURN',
    ],
}


def netclass(name, values):
    result = {
        'bus_width': 12,
        'line_style': 0,
        'microvia_diameter': 0.3,
        'microvia_drill': 0.1,
        'name': name,
        'pcb_color': 'rgba(0, 0, 0, 0.000)',
        'priority': 0,
        'schematic_color': 'rgba(0, 0, 0, 0.000)',
        'tuning_profile': '',
        'wire_width': 6,
    }
    result.update(values)
    return result


def main():
    project = json.loads(PROJECT.read_text())
    settings = project['net_settings']
    default = next(item for item in settings['classes'] if item['name'] == 'Default')
    default = copy.deepcopy(default)
    default.update(clearance=0.20, track_width=0.20, via_diameter=0.60,
                   via_drill=0.30, diff_pair_width=0.20,
                   diff_pair_gap=0.20, diff_pair_via_gap=0.25)
    settings['classes'] = [default] + [netclass(name, values) for name, values in CLASS_RULES.items()]
    settings['netclass_patterns'] = [
        {'netclass': class_name, 'pattern': net_name}
        for class_name, nets in CLASS_NETS.items() for net_name in nets
    ]

    board_nets = set(re.findall(r'\(net\s+"([^"]+)"\)', BOARD.read_text()))
    assigned = {net for nets in CLASS_NETS.values() for net in nets}
    missing = assigned - board_nets
    assert not missing, f'Net-class assignment refers to missing nets: {sorted(missing)}'

    design = project['board']['design_settings']
    design['track_widths'] = [0.20, 0.30, 0.50, 0.60, 1.00, 2.50]
    design['via_dimensions'] = [
        {'diameter': 0.60, 'drill': 0.30},
        {'diameter': 0.80, 'drill': 0.40},
        {'diameter': 1.00, 'drill': 0.50},
        {'diameter': 1.60, 'drill': 0.80},
    ]
    design['diff_pair_dimensions'] = [
        {'gap': 0.20, 'via_gap': 0.25, 'width': 0.20},
    ]
    PROJECT.write_text(json.dumps(project, indent=2, ensure_ascii=False) + '\n')
    DRU.write_text(DRU_RULES)
    print(f'Configured {len(CLASS_RULES)+1} net classes and {len(assigned)} assignments.')


if __name__ == '__main__':
    main()
