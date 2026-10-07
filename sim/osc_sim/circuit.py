"""Switch-level DC model of the joined boards (F1).

Every part is found in the netlists and modelled from its datasheet limits in
sim/reference/devices.json: resistors as resistors, driven outputs as
Thevenin sources, LEDs as a forward drop, MOSFET channels as RDS(on), relays
by their coil voltage and triacs by the opto that fires them. Only guaranteed
points are trusted (VIH/VIL, VGS at which RDS(on) is specified, maximum IFT,
must-operate voltage); between them a device is undefined ('X') and so is
everything it feeds. The solution is found twice, once with every undefined
device conducting and once with all of them open, and a result is only
definite when both agree.
"""
import json
from collections import deque
from dataclasses import dataclass, field

from . import netlist, parts
from .model import Node

ON, OFF, X = True, False, None
DIODE_RD = 2.0       # ohm, slope of a conducting LED in the solve
CONTACT_OHMS = 0.05  # closed switch or contact


def nodal(edges, fixed, inject=None):
    """Node voltages over resistive edges. Floating nets come back as None.

    edges: (a, b, ohms); fixed: {net: volts}; inject: {net: amps into the net}.
    """
    inject = inject or {}
    adj = {}
    for a, b, ohms in edges:
        if a == b:
            continue
        g = 1.0 / max(ohms, 1e-6)
        adj.setdefault(a, []).append((b, g))
        adj.setdefault(b, []).append((a, g))
    result = dict(fixed)
    seen = set(fixed)
    for start in list(adj) + list(inject):
        if start in seen:
            continue
        comp, touches, queue = [], False, deque([start])
        seen.add(start)
        while queue:
            n = queue.popleft()
            comp.append(n)
            for m, _ in adj.get(n, []):
                if m in fixed:
                    touches = True
                elif m not in seen:
                    seen.add(m)
                    queue.append(m)
        if not touches:
            for n in comp:
                result[n] = None
            continue
        index = {n: i for i, n in enumerate(comp)}
        size = len(comp)
        mat = [[0.0] * (size + 1) for _ in range(size)]
        for n in comp:
            i = index[n]
            mat[i][size] += inject.get(n, 0.0)
            for m, g in adj.get(n, []):
                mat[i][i] += g
                if m in index:
                    mat[i][index[m]] -= g
                else:
                    mat[i][size] += g * fixed[m]
        for col in range(size):
            piv = max(range(col, size), key=lambda r: abs(mat[r][col]))
            mat[col], mat[piv] = mat[piv], mat[col]
            p = mat[col][col]
            for r in range(size):
                if r != col and mat[r][col]:
                    f = mat[r][col] / p
                    row, prow = mat[r], mat[col]
                    for c in range(col, size + 1):
                        row[c] -= f * prow[c]
        for n in comp:
            i = index[n]
            result[n] = mat[i][size] / mat[i][i]
    return result


def level(v, vih, vil):
    if v is None:
        return X
    if v >= vih:
        return ON
    if v <= vil:
        return OFF
    return X


@dataclass
class Device:
    ref: str            # 'board:REF'
    kind: str
    params: dict
    pins: dict          # physical name -> global net
    state: object = OFF
    why: str = ''


@dataclass
class Run:
    volts: dict
    states: dict        # ref (and 'ref.1Y', 'ref.mode') -> state
    why: dict           # ref -> explanation of an undefined state
    live: set           # nets carrying the mains phase
    currents: dict = field(default_factory=dict)
    sources: list = field(default_factory=list)  # (label, amps out of the source, limit or None)


@dataclass
class Outcome:
    """Both solutions: undefined devices open (lo) and conducting (hi)."""
    lo: Run
    hi: Run

    def state(self, ref):
        a, b = self.lo.states.get(ref, OFF), self.hi.states.get(ref, OFF)
        return a if a == b else X

    def volts(self, net):
        return self.lo.volts.get(net), self.hi.volts.get(net)

    def undefined(self):
        """(ref, why) of every device left between its guaranteed points."""
        out = {}
        for run in (self.lo, self.hi):
            for ref, st in run.states.items():
                if st is X and ref in run.why:
                    out.setdefault(ref, run.why[ref])
        return sorted(out.items())

    def classify(self, net, mode, supply=None):
        """ON/OFF/X of a load node: 'live' (mains phase), 'high' or 'low' (sinks to ground)."""
        got = [_classify(run, net, mode, supply) for run in (self.lo, self.hi)]
        return got[0] if got[0] == got[1] else X


def _classify(run, net, mode, supply):
    if mode == 'live':
        return net in run.live
    v = run.volts.get(net)
    if v is None:
        return OFF
    hi, lo = 0.9 * supply, 0.1 * supply
    if mode == 'high':
        return ON if v >= hi else (OFF if v <= lo else X)
    return ON if v <= lo else (OFF if v >= hi else X)


class Circuit:
    """The boards as one DC network around the devices found in the netlists."""

    def __init__(self, system, devices=None):
        self.s = system
        root = system.root
        self.ref = devices or json.loads((root / 'sim/reference/devices.json').read_text(encoding='utf-8'))['parts']
        self.c = system.contract
        self.gnd = next(g for g, v in system.voltages.items() if v == 0)
        self.resistors = [(a, b, ohms) for _, a, b, ohms in system.resistors() if ohms]
        self.devices = []
        for board, b in system.boards.items():
            for ref, comp in sorted(b.components.items()):
                p = self.ref.get(comp.mpn)
                if p is None or p['kind'] == 'mcu':
                    continue
                pins = {}
                for num in comp.pins:
                    node = Node(board, ref, num)
                    pins.setdefault(system.physical_name(node), system.net_of(node))
                self.devices.append(Device(f'{board}:{ref}', p['kind'], p, pins))
        self.by_ref = {d.ref: d for d in self.devices}
        mains = self.c.get('mains', {})
        self.phase = system.find(mains['phase']) if mains else None
        self.fuses = [tuple(system.net_of(Node(board, ref, n)) for n in sorted(comp.pins))
                      for board, b in system.boards.items() for ref, comp in b.components.items()
                      if comp.part == 'FUSE']
        self.bridges = []
        for board, b in system.boards.items():
            for ref, comp in b.components.items():
                if comp.part == 'BRIDGE_KBP':
                    pins = {system.physical_name(Node(board, ref, n)): system.net_of(Node(board, ref, n))
                            for n in comp.pins}
                    self.bridges.append(pins)
        self.mcus = {}
        for name, spec in self.c['mcus'].items():
            board, ref = spec['ref'].split(':')
            self.mcus[name] = self.ref.get(self.s.comp(board, ref).mpn)

    # -- evaluation -----------------------------------------------------------
    def evaluate(self, rails, drives=(), loads=(), supervisor_reset=False, faults=(), vf_low=False,
                 bridge_amps=None, sense_amps=None):
        """Operating point of the boards.

        rails: {net: volts} for every supply (including ground).
        drives: (net, volts, ohms) Thevenin sources, e.g. MCU outputs.
        loads: elements of the plant: ('r', a, b, ohms), ('src', net, volts, ohms), ('i', net, amps) or
            ('vr', a, b, volts, ohms), a series source of 'volts' from a to b (a motor's back-EMF).
        supervisor_reset: the TPS3828 holds RESET low.
        faults: refs of open-drain fault outputs pulled low (DRV8876 nFAULT).
        vf_low: LEDs at their lowest forward drop (highest current) instead of the highest.
        bridge_amps: {ref: load current} of each H-bridge, mirrored on IPROPI.
        sense_amps: {ref: current from IN+ to IN-} of each Hall current sensor.
        """
        amps = bridge_amps or {}
        sense = sense_amps or {}
        return Outcome(*(self._solve(rails, drives, loads, supervisor_reset, faults, x_on, vf_low, amps, sense)
                         for x_on in (False, True)))

    def _solve(self, rails, drives, loads, supervisor_reset, faults, x_on, vf_low, bridge_amps,
               sense_amps=None):
        fixed = {self.s.find(n) if n in self.s._parent else n: v for n, v in rails.items()}
        states = {d.ref: OFF for d in self.devices}
        why = {}
        for _ in range(12):
            edges = list(self.resistors)
            inject = {}
            fx = dict(fixed)
            currents = {}
            srcs = []

            def src(name, net, volts, ohms, limit=None, label=None):
                fx[name] = volts
                edges.append((name, net, ohms))
                srcs.append((label or name, name, net, volts, ohms, limit))

            def vr(a, b, volts, ohms):
                # Source of 'volts' (a side positive) in series with ohms.
                edges.append((a, b, ohms))
                inject[a] = inject.get(a, 0.0) + volts / ohms
                inject[b] = inject.get(b, 0.0) - volts / ohms

            for i, (net, volts, ohms, *extra) in enumerate(drives):
                src(f'drive{i}', net, volts, ohms, *extra)
            for i, el in enumerate(loads):
                if el[0] == 'r':
                    edges.append((el[1], el[2], el[3]))
                elif el[0] == 'src':
                    src(f'load{i}', el[1], el[2], el[3])
                elif el[0] == 'i':
                    inject[el[1]] = inject.get(el[1], 0.0) + el[2]
                else:
                    vr(el[1], el[2], el[3], el[4])
            on = {ref: (st is ON or (st is X and x_on)) for ref, st in states.items()}
            diodes = []
            for d in self.devices:
                p, pin = d.params, d.pins
                k = d.kind
                if k == 'logic':
                    vcc = fixed.get(pin['VCC'])
                    rout = (vcc - p['voh_16ma']) / p['io_max'] if vcc else 50.0
                    for y in ('1Y', '2Y'):
                        st = states.get(f'{d.ref}.{y}', OFF)
                        level_v = vcc if (st is ON or (st is X and x_on)) else 0.0
                        src(f'{d.ref}.{y}', pin[y], level_v, rout, p['io_max'], f'{_short(d.ref)}.{y}')
                elif k in ('schmitt_buffer', 'nand_schmitt'):
                    vcc = fixed.get(pin['VCC'])
                    rout = (vcc - p['voh_16ma']) / p['io_max'] if vcc else 50.0
                    high = on[d.ref]
                    src(f'{d.ref}.Y', pin['Y'], vcc if high else 0.0, rout, p['io_max'], f'{_short(d.ref)}.Y')
                elif k == 'nmos':
                    if on[d.ref]:
                        edges.append((pin['D'], pin['S'], p['rds_on']))
                elif k == 'gate_driver':
                    # Held low below UVLO, so the output is always driven.
                    vdd = fixed.get(pin['VDD'], 0.0)
                    high = on[d.ref]
                    src(f'{d.ref}.OUT', pin['OUT'], vdd if high else 0.0, p['roh'] if high else p['rol'])
                elif k == 'h_bridge':
                    for name in ('EN/IN1', 'PH/IN2', 'nSLEEP'):
                        edges.append((pin[name], self.gnd, p['rpd']))
                    mode = states.get(f'{d.ref}.mode', 'sleep')
                    vm = fixed.get(pin['VM'], 0.0)
                    if mode == 'fwd':
                        src(f'{d.ref}.O1', pin['OUT1'], vm, 0.35)
                        src(f'{d.ref}.O2', pin['OUT2'], 0.0, 0.35)
                    elif mode == 'rev':
                        src(f'{d.ref}.O1', pin['OUT1'], 0.0, 0.35)
                        src(f'{d.ref}.O2', pin['OUT2'], vm, 0.35)
                    elif mode == 'brake':
                        src(f'{d.ref}.O1', pin['OUT1'], 0.0, 0.35)
                        src(f'{d.ref}.O2', pin['OUT2'], 0.0, 0.35)
                    if d.ref in faults:
                        src(f'{d.ref}.nF', pin['nFAULT'], 0.0, 50.0)
                    if mode in ('fwd', 'rev', 'brake'):
                        i_load = abs(bridge_amps.get(d.ref, 0.0))
                        inject[pin['IPROPI']] = inject.get(pin['IPROPI'], 0.0) + p['aipropi'] * i_load
                elif k == 'load_switch':
                    vin, _, vout = parts.switch_pins(pin)
                    if on[d.ref]:
                        fx[vout] = fixed.get(vin, 0.0)
                    else:
                        fx[vout] = 0.0  # QOD on VOUT, or a bleed resistor, discharges the rail
                elif k == 'supervisor':
                    if supervisor_reset:
                        src(f'{d.ref}.RST', pin['~{RESET}'], 0.0, p['vol'] / p['iol'])
                elif k == 'opto_triac':
                    vf = p['vf'][0 if vf_low else 1]
                    diodes.append((d, pin['A'], pin['K'], vf))
                    if states.get(f'{d.ref}.led', ON):
                        vr(pin['A'], pin['K'], vf, DIODE_RD)
                elif k == 'relay':
                    edges.append((pin['COIL_A'], pin['COIL_B'], p['coil_ohms'] * (1 + p['coil_tol'])))
                elif k == 'hall_current':
                    # VS/2 plus the sensitivity times the input current, inside
                    # the output swing; Hi-Z below the minimum supply.
                    edges.append((pin['IN+'], pin['IN-'], p['rin']))
                    vs = fixed.get(pin['VS'], 0.0)
                    if vs >= p['vs_min']:
                        lo, hi = p['swing']
                        vo = vs / 2 + p['sensitivity_v_per_a'] * (sense_amps or {}).get(d.ref, 0.0)
                        src(f'{d.ref}.VOUT', pin['VOUT'], min(vs - hi, max(lo, vo)), p['rout'])
            v = nodal(edges, fx, inject)

            def vget(net):
                return v.get(net) if net is not None else None

            new = dict(states)
            for d, a, kk, vf in diodes:
                if new.get(f'{d.ref}.led', ON):
                    va, vk = vget(a), vget(kk)
                    if va is None or vk is None or (va - vk - vf) / DIODE_RD < 0:
                        new[f'{d.ref}.led'] = OFF
                else:
                    va, vk = vget(a), vget(kk)
                    if va is not None and vk is not None and va - vk > vf:
                        new[f'{d.ref}.led'] = ON
            for d in self.devices:
                p, pin, k = d.params, d.pins, d.kind
                if k == 'logic':
                    vcc = fixed.get(pin['VCC'], 0.0)
                    for y, ins in (('1Y', ('1A', '1B')), ('2Y', ('2A', '2B'))):
                        lv = [level(vget(pin[i]), p['vih'], p['vil']) for i in ins]
                        out = OFF if OFF in lv else (ON if all(x is ON for x in lv) else X)
                        if vcc < 1.65:
                            out = X
                        new[f'{d.ref}.{y}'] = out
                        if out is X:
                            why[f'{d.ref}.{y}'] = (f'{d.ref.split(":")[1]}.{y}: entradas ' + ', '.join(
                                f'{i}={_fmt(vget(pin[i]))}' for i in ins) +
                                f' (VIH {p["vih"]} V, VIL {p["vil"]} V)')
                    new[d.ref] = ON
                elif k == 'schmitt_buffer':
                    # Hysteresis: between VT- and VT+ the output keeps its last level.
                    lv = level(vget(pin['A']), p['vih'], p['vil'])
                    va = vget(pin['A'])
                    new[d.ref] = lv if lv is not X else (states.get(d.ref, OFF) if va is not None else X)
                    if new[d.ref] is X:
                        why[d.ref] = f'{_short(d.ref)}: entrada A flotante'
                elif k == 'nand_schmitt':
                    ins = [vget(pin[n]) for n in ('A', 'B')]
                    lv = [level(v, p['vih'], p['vil']) for v in ins]
                    if None in ins:
                        out = X
                    elif OFF in lv:
                        out = ON          # any input low: output high
                    elif all(x is ON for x in lv):
                        out = OFF
                    else:
                        out = states.get(d.ref, OFF)  # inside the hysteresis band
                    new[d.ref] = out
                    if out is X:
                        why[d.ref] = f'{_short(d.ref)}: entrada flotante'
                elif k == 'nmos':
                    vg, vs = vget(pin['G']), vget(pin['S'])
                    if vg is None or vs is None:
                        st, w = X, f'{_short(d.ref)}: puerta flotante'
                    else:
                        vgs = vg - vs
                        st = ON if vgs >= p['vgs_on'] else (OFF if vgs <= p['vgs_th'][0] else X)
                        w = (f'{_short(d.ref)}: VGS = {vgs:.2f} V; el fabricante garantiza RDS(on) a partir de '
                             f'{p["vgs_on"]} V y VGS(th) llega a {p["vgs_th"][1]} V')
                    new[d.ref] = st
                    if st is X:
                        why[d.ref] = w
                    vd = vget(pin['D'])
                    if st is not OFF and vd is not None and vs is not None:
                        currents[d.ref] = (vd - vs) / p['rds_on']
                elif k == 'gate_driver':
                    vdd = fixed.get(pin['VDD'], 0.0)
                    a = level(vget(pin['IN+']), p['vih'], p['vil'])
                    b = level(vget(pin['IN-']), p['vih'], p['vil'])
                    st = OFF if (a is OFF or b is ON or vdd < p['uvlo']) else (ON if a is ON and b is OFF else X)
                    new[d.ref] = st
                    if st is X:
                        why[d.ref] = (f'{_short(d.ref)}: IN+ = {_fmt(vget(pin["IN+"]))}, IN- = {_fmt(vget(pin["IN-"]))} '
                                      f'(VIN_H {p["vih"]} V, VIN_L {p["vil"]} V)')
                elif k == 'h_bridge':
                    lv = {n: level(vget(pin[n]), p['vih'], p['vil']) for n in ('EN/IN1', 'PH/IN2', 'nSLEEP')}
                    if lv['nSLEEP'] is OFF:
                        mode = 'sleep'
                    elif X in lv.values():
                        mode = X
                    elif lv['EN/IN1'] is OFF:
                        mode = 'brake'
                    else:
                        mode = 'fwd' if lv['PH/IN2'] is ON else 'rev'
                    new[f'{d.ref}.mode'] = mode if mode is not X else 'sleep'
                    new[d.ref] = ON if mode in ('fwd', 'rev') else (X if mode is X else OFF)
                    if mode is X:
                        why[d.ref] = f'{_short(d.ref)}: ' + ', '.join(f'{n}={_fmt(vget(pin[n]))}' for n in lv) + \
                                     f' (VIH {p["vih"]} V, VIL {p["vil"]} V)'
                elif k == 'load_switch':
                    _, en, _ = parts.switch_pins(pin)
                    st = level(vget(en), p['vih'], p['vil'])
                    new[d.ref] = st
                    if st is X:
                        why[d.ref] = f'{_short(d.ref)}: ON = {_fmt(vget(en))}'
                elif k == 'supervisor':
                    new[d.ref] = ON if supervisor_reset else OFF
                elif k == 'opto_triac':
                    va, vk = vget(pin['A']), vget(pin['K'])
                    i_led = 0.0
                    if new.get(f'{d.ref}.led', ON) and va is not None and vk is not None:
                        i_led = max(0.0, (va - vk - p['vf'][0 if vf_low else 1]) / DIODE_RD)
                    currents[d.ref] = i_led
                    st = ON if i_led >= p['ift'] else (OFF if i_led < 5e-5 else X)
                    new[d.ref] = st
                    if st is X:
                        why[d.ref] = (f'{_short(d.ref)}: IF = {i_led * 1000:.2f} mA con VF {p["vf"][1]} V, '
                                      f'por debajo de IFT {p["ift"] * 1000:.0f} mA')
                elif k == 'relay':
                    va, vb = vget(pin['COIL_A']), vget(pin['COIL_B'])
                    vc = None if va is None or vb is None else va - vb
                    rated = p['v_rated']
                    if vc is None:
                        st = OFF
                    else:
                        st = ON if vc >= p['operate_frac'] * rated else (OFF if vc <= p['release_frac'] * rated else X)
                    new[d.ref] = st
                    if st is X:
                        why[d.ref] = (f'{_short(d.ref)}: bobina a {vc:.2f} V; cierra garantizado a '
                                      f'{p["operate_frac"] * rated:.1f} V y abre a {p["release_frac"] * rated:.1f} V')
                    if vc is not None:
                        currents[d.ref] = vc / p['coil_ohms']
                elif k == 'triac':
                    opto = next((o for o in self.devices if o.kind == 'opto_triac' and o.pins.get('MT_G') == pin['G']), None)
                    new[d.ref] = new.get(opto.ref, OFF) if opto else OFF
                    if new[d.ref] is X:
                        why[d.ref] = f'{_short(d.ref)}: depende de {_short(opto.ref)}'
            if new == states:
                break
            states = new
        live = self._live(states, x_on)
        clean = {d.ref: states.get(d.ref, OFF) for d in self.devices}
        for d in self.devices:
            if d.kind == 'logic':
                for y in ('1Y', '2Y'):
                    clean[f'{d.ref}.{y}'] = states.get(f'{d.ref}.{y}', OFF)
            if d.kind == 'h_bridge':
                clean[f'{d.ref}.mode'] = states.get(f'{d.ref}.mode', 'sleep')
        sources = [(label, (volts - v[net]) / ohms if v.get(net) is not None else 0.0, limit)
                   for label, _, net, volts, ohms, limit in srcs]
        return Run(v, clean, why, live, currents, sources)

    def _live(self, states, x_on):
        """Nets carrying the mains phase through fuses, closed contacts and fired triacs."""
        if self.phase is None:
            return set()
        links = list(self.fuses)
        for d in self.devices:
            st = states.get(d.ref)
            if st is ON or (st is X and x_on):
                if d.kind == 'relay':
                    links += [(d.pins['COM_A'], d.pins['NO_A']), (d.pins['COM_B'], d.pins['NO_B'])]
                elif d.kind == 'triac':
                    links.append((d.pins['A2'], d.pins['A1']))
        for b in self.bridges:
            links += [(b['AC1'], b['+'])]
        for d in self.devices:
            if d.kind == 'hall_current':
                links.append((d.pins['IN+'], d.pins['IN-']))
        adj = {}
        for a, b in links:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        seen, queue = {self.phase}, deque([self.phase])
        while queue:
            n = queue.popleft()
            for m in adj.get(n, ()):
                if m not in seen:
                    seen.add(m)
                    queue.append(m)
        return seen

    # -- helpers ----------------------------------------------------------------
    def mcu_drive(self, mcu, net, high, vdd, label=None):
        """Thevenin source of an MCU output at its guaranteed VOH/VOL."""
        p = self.mcus[mcu]
        if high:
            return (net, vdd, p['voh_drop'] / p['io_max'], p['io_max'], label)
        return (net, 0.0, p['vol'] / p['io_max'], p['io_max'], label)


def _short(ref):
    return ref.split(':')[1]


def _fmt(v):
    return 'flotante' if v is None else f'{v:.2f} V'
