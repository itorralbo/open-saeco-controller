"""Worst-case drive check (F1).

Each order of the contract that names a 'drive' must move its load at both
ends of the supply ranges: on when the MCU drives it active, off when it
drives it inactive, at its reset level with the MCU in reset and, for the
interlocked orders, off when STM_NRST is low even if the pin stayed driven.
The levels come from sim/osc_sim/circuit.py, so a gate below the voltage at
which its MOSFET is specified, a logic input between VIL and VIH or an opto
below its IFT shows up here as an undefined load.
"""
from .circuit import ON, OFF, X, Circuit
from .model import Node

CORNERS = (0, 1)
CORNER_NAME = {0: 'rails al mínimo', 1: 'rails al máximo'}
WANT_TEXT = {ON: 'activa', OFF: 'parada', X: 'indefinida'}


class Bench:
    """The boards on the bench: supplies at a corner and the STM32 pins set."""

    def __init__(self, checker, circuit=None):
        self.k = checker
        self.s = checker.s
        self.c = checker.c
        self.circuit = circuit or Circuit(self.s)
        spec = self.c['mcus']['stm32']
        self.vdd_net = self.s.find(spec['vdd'])
        board, ref = spec['ref'].split(':')
        self.mcu_board, self.mcu_ref = board, ref
        self.caps = checker.mcu_ref[self.s.comp(board, ref).mpn]
        self.switched = {d.pins['VOUT'] for d in self.circuit.devices if d.kind == 'load_switch'}
        self.nrst = self.s.find(self.c['interlock_net'])

    def rails(self, corner=None):
        r = {n: v for n, v in self.s.voltages.items() if n not in self.switched}
        for net, span in self.c.get('rail_range', {}).items():
            if ':' in net and corner is not None:
                r[self.s.find(net)] = span[corner]
        return r

    def loads(self):
        out = []
        for ld in self.c.get('loads', []):
            a, b = (self.s.net_of(self.s.endpoint(e)) for e in ld['between'])
            out.append(('r', a, b, ld['ohms']))
        return out

    def outputs(self, levels, vdd):
        """Every STM32 order driven: active if levels[name], inactive otherwise."""
        drives = []
        for (mcu, name), r in sorted(self.k.signals.items()):
            if mcu != 'stm32' or r.pad is None or r.function not in ('gpio_out', 'pwm'):
                continue
            high = bool(levels.get(name)) == (r.spec.get('active', 'high') == 'high')
            drives.append(self.circuit.mcu_drive(mcu, self.s.net_of(r.pad), high, vdd, f'{r.pin} ({name})'))
        return drives

    def reset_pulls(self, vdd):
        out = []
        gnd = self.circuit.gnd
        comp = self.s.comp(self.mcu_board, self.mcu_ref)
        for num in comp.pins:
            node = Node(self.mcu_board, self.mcu_ref, num)
            pull = self.caps['reset_pulls'].get(self.s.physical_name(node))
            net = self.s.net_of(node)
            if pull and net:
                out.append((net, vdd if pull == 'up' else 0.0, self.caps['reset_pull_ohms']))
        return out

    def run(self, corner=None, levels=None, running=True, supervisor_reset=False, extra_loads=(), faults=(),
            vf_low=False):
        rails = self.rails(corner)
        vdd = rails[self.vdd_net]
        mcu = self.circuit.mcus['stm32']
        # NRST's own weak pull-up, at its weakest.
        drives = [(self.nrst, vdd, mcu['nrst_pullup_ohms'][1])]
        drives += self.outputs(levels or {}, vdd) if running else self.reset_pulls(vdd)
        return self.circuit.evaluate(rails, drives, self.loads() + list(extra_loads),
                                     supervisor_reset=supervisor_reset, faults=faults, vf_low=vf_low)


def check(checker):
    bench = Bench(checker)
    s = checker.s
    over = {}
    for (mcu, name), r in sorted(checker.signals.items()):
        d = r.spec.get('drive')
        if not d or r.pad is None:
            continue
        load = s.net_of(s.endpoint(d['load']))
        with_ = {w: True for w in d.get('with', [])}
        active_high = r.spec.get('active', 'high') == 'high'
        reset_on = r.spec.get('reset') is not None and (r.spec['reset'] == 'high') == active_high
        cases = [('el MCU la activa', {name: True, **with_}, True, False, ON),
                 ('el MCU la desactiva', with_, True, False, OFF),
                 ('el MCU está en reset', {}, False, True, ON if reset_on else OFF)]
        if r.spec.get('interlocked'):
            cases.append(('el pin sigue activo con STM_NRST bajo', {name: True, **with_}, True, True, OFF))
        failed = False
        checker.drive_rows.append((name, d['load'], margins(bench, {name: True, **with_}, with_)))
        for corner in CORNERS:
            rails = bench.rails(corner)
            supply = rails.get(s.find(d['supply'])) if 'supply' in d else None
            for label, levels, running, sup, want in cases:
                out = bench.run(corner, levels, running, sup)
                for run in (out.lo, out.hi):
                    for src, amps, limit in run.sources:
                        if limit and abs(amps) > limit * 1.001:
                            over.setdefault(src, (amps, limit, label, name, corner))
                got = out.classify(load, d['on'], supply)
                if got == want or failed:
                    continue
                failed = True
                causes = '; '.join(w for _, w in out.undefined()) or 'sin dispositivo indefinido'
                checker.add('error', 'drive',
                            f'stm32.{name} ({r.pin}): cuando {label}, con {CORNER_NAME[corner]}, '
                            f'{d["load"]} queda {WANT_TEXT[got]} y debería quedar {WANT_TEXT[want]}. '
                            f'Causa: {causes}.', r.pad)
    for src, (amps, limit, label, name, corner) in sorted(over.items()):
        checker.add('error', 'drive-current',
                    f'{src} entrega {abs(amps) * 1000:.1f} mA (límite {limit * 1000:.0f} mA) cuando '
                    f'{label} {name}, con {CORNER_NAME[corner]}.')
    check_limits(checker, bench)


def margins(bench, active, inactive):
    """What the order switches, at the low corner: each device that changes state and its margin."""
    on, off = bench.run(0, active).lo, bench.run(0, inactive).lo
    rows = []
    for d in bench.circuit.devices:
        key = f'{d.ref}.mode' if d.kind == 'h_bridge' else d.ref
        if on.states.get(key) == off.states.get(key) or on.states.get(d.ref) is not True:
            continue
        p, ref, v = d.params, d.ref.split(':')[1], on.volts
        if d.kind == 'nmos':
            vgs = v[d.pins['G']] - v[d.pins['S']]
            rows.append(f'{ref} VGS {vgs:.2f} V ≥ {p["vgs_on"]} V')
        elif d.kind == 'opto_triac':
            rows.append(f'{ref} IF {on.currents[d.ref] * 1000:.1f} mA ≥ {p["ift"] * 1000:.0f} mA')
        elif d.kind == 'relay':
            vc = v[d.pins['COIL_A']] - v[d.pins['COIL_B']]
            rows.append(f'{ref} bobina {vc:.1f} V ≥ {p["operate_frac"] * p["v_rated"]:.1f} V')
        elif d.kind == 'gate_driver':
            rows.append(f'{ref} IN+ {v[d.pins["IN+"]]:.2f} V ≥ {p["vih"]} V')
        elif d.kind == 'h_bridge':
            rows.append(f'{ref} {on.states[key]}: ' + ', '.join(
                f'{n} {v[d.pins[n]]:.2f} V' for n in ('nSLEEP', 'EN/IN1', 'PH/IN2')) + f' (VIH {p["vih"]} V)')
        elif d.kind == 'load_switch':
            rows.append(f'{ref} ON {v[d.pins["ON"]]:.2f} V ≥ {p["vih"]} V')
        elif d.kind == 'triac':
            rows.append(f'{ref} disparado')
    return '; '.join(rows)


def check_limits(checker, bench):
    """Absolute limits with every order active at the high corner."""
    levels = {name: True for (mcu, name), r in checker.signals.items()
              if mcu == 'stm32' and r.spec.get('drive')}
    out = bench.run(1, levels, vf_low=True)
    off = bench.run(1, {})
    for d in bench.circuit.devices:
        p = d.params
        if d.kind == 'opto_triac':
            # LED current at the lowest forward drop.
            amps = out.lo.currents.get(d.ref, 0.0)
            if amps > p['if_max']:
                checker.add('error', 'drive-limit',
                            f'{d.ref.split(":")[1]}: IF de hasta {amps * 1000:.1f} mA, por encima de '
                            f'{p["if_max"] * 1000:.0f} mA.')
        elif d.kind == 'relay':
            amps = out.lo.currents.get(d.ref)
            if amps is not None and amps * p['coil_ohms'] > p['max_frac'] * p['v_rated']:
                checker.add('error', 'drive-limit',
                            f'{d.ref.split(":")[1]}: bobina a {amps * p["coil_ohms"]:.1f} V, por encima del '
                            f'{p["max_frac"]:.0%} de {p["v_rated"]:g} V.')
        elif d.kind == 'nmos':
            vd = off.lo.volts.get(d.pins['D'])
            if vd is not None and vd + 1.0 > p['vds_max']:
                checker.add('error', 'drive-limit',
                            f'{d.ref.split(":")[1]}: el drenador llega a {vd:.1f} V (+1 V de rueda libre) '
                            f'con VDS máxima de {p["vds_max"]} V.')
