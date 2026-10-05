"""How a signal crosses each part, keyed by the symbol's libpart name.

ARCS maps an output pin to the input pins that control it, by physical pin
name (the datasheet name when sim/reference/pinouts.json knows the part).
SERIES parts carry a signal between their two terminals in either direction.
Only control flow is modelled here; F1 adds the electrical behaviour.
"""

SERIES = {'R', 'L', 'FUSE'}

# Pads joined inside the part (a protector's flow-through lines).
THROUGH = {'USBLC6': (('1', '6'), ('3', '4'))}

ARCS = {
    'DUAL_AND': {'1Y': ('1A', '1B'), '2Y': ('2A', '2B')},
    'SCHMITT_BUF': {'Y': ('A',)},
    'UCC27517DBV': {'OUT': ('IN+', 'IN-')},
    'NMOS_SOT23': {'D': ('G',)},
    'OPTO_TRIAC': {'MT_G': ('A', 'K')},
    'TRIAC_TO220': {'A1': ('G',)},
    'DRV8876PWP': {'OUT1': ('EN/IN1', 'PH/IN2', 'nSLEEP'),
                   'OUT2': ('EN/IN1', 'PH/IN2', 'nSLEEP')},
    'RELAY_G5RL': {'NO_A': ('COIL_A', 'COIL_B'), 'NO_B': ('COIL_A', 'COIL_B')},
    'BRIDGE_KBP': {'+': ('AC1', 'AC2'), '-': ('AC1', 'AC2')},
    'TPS22918': {'VOUT': ('ON',)},
    'TPS3828DBV': {'~{RESET}': ('WDI', '~{MR}')},
}

# Logic function of the gates the interlock check reasons about.
AND_GATES = {'DUAL_AND': {'1Y': ('1A', '1B'), '2Y': ('2A', '2B')}}
# Non-inverting buffers: their output carries the input's logic level.
BUFFERS = {'SCHMITT_BUF': {'Y': 'A'}}

SUPPLY_NAMES = {'VDD', 'VCC', 'VM', 'VIN', 'VBAT', '3V3', 'VDDA', 'VREF+'}
GROUND_NAMES = {'GND', 'VSS', 'VSSA', 'PGND', 'EP', 'PAD', 'EP_GND'}
