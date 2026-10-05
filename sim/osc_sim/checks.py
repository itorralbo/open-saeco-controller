"""Design checks of the joined boards against the firmware contract.

Every check returns Finding objects; errors mean the board, as drawn, cannot
do what the firmware contract needs (or the contract is wrong).
"""
import json
import math
import re
from dataclasses import dataclass, field

from . import dc, drive, parts
from .model import Node


@dataclass
class Finding:
    severity: str  # error | warning | info
    code: str
    message: str
    where: list = field(default_factory=list)


@dataclass
class Resolved:
    mcu: str
    name: str
    net: str
    function: str
    pad: Node | None = None
    pin: str | None = None
    periph: str | None = None
    af: int | None = None
    adc: tuple | None = None  # (instance, channel)
    path: list = field(default_factory=list)
    reset_level: str | None = None
    spec: dict = field(default_factory=dict)


class Checker:
    def __init__(self, system):
        self.s = system
        self.c = system.contract
        self.mcu_ref = json.loads((system.root / 'sim/reference/mcus.json').read_text(encoding='utf-8'))
        self.findings = []
        self.signals = {}  # (mcu, name) -> Resolved
        self.analog = []   # report rows
        self.drive_rows = []  # (signal, load, margins) at the low corner

    def add(self, severity, code, message, *where):
        self.findings.append(Finding(severity, code, message, [str(w) for w in where]))

    def run(self):
        self.check_pinouts()
        self.check_supplies()
        self.check_harness()
        for mcu in self.c['mcus']:
            self.resolve(mcu)
        for mcu in self.c['mcus']:
            self.check_coverage(mcu)
        for r in self.signals.values():
            self.check_paths(r)
            self.check_reset(r)
            self.check_pull(r)
            self.check_analog(r)
        self.check_keypad()
        self.check_ui_domain()
        self.check_backfeed()
        drive.check(self)
        order = {'error': 0, 'warning': 1, 'info': 2}
        self.findings.sort(key=lambda f: order[f.severity])
        return self.findings

    # -- symbols and supplies -----------------------------------------------
    def check_pinouts(self):
        for board, b in self.s.boards.items():
            for ref, comp in sorted(b.components.items()):
                ref_part = self.s.reference.get(comp.mpn)
                if ref_part is None:
                    continue
                wrong = []
                for num, pin in sorted(comp.pins.items(), key=lambda kv: (len(kv[0]), kv[0])):
                    want = ref_part['pins'].get(num)
                    if want is None:
                        wrong.append(f'{num} {pin.name}→(no existe)')
                    elif pin.name not in want.split('|'):
                        wrong.append(f'{num} {pin.name}→{want.split("|")[0]}')
                missing = sorted(set(ref_part['pins']) - set(comp.pins), key=lambda x: (len(x), x))
                wrong += [f'{n} (falta en el símbolo)' for n in missing]
                if wrong:
                    self.add('error', 'symbol-pinout',
                             f'{ref} ({comp.mpn}): el símbolo no coincide con la referencia en '
                             f'{len(wrong)} pads (pad símbolo→real): {", ".join(wrong)}. '
                             f'Fuente: {ref_part["source"]}', f'{board}:{ref}')

    def check_supplies(self):
        for board, b in self.s.boards.items():
            for ref, comp in sorted(b.components.items()):
                if comp.mpn not in self.s.reference:
                    continue
                outs = set(parts.ARCS.get(comp.part, {}))
                for num in comp.pins:
                    node = Node(board, ref, num)
                    name = self.s.physical_name(node)
                    g = self.s.net_of(node)
                    shown = g or 'sin conexión'
                    v = self.s.voltages.get(g)
                    if name in parts.SUPPLY_NAMES and (g not in self.s.rails or v == 0):
                        self.add('error', 'supply-pad',
                                 f'{ref}.{num} es {name} y queda en {shown}, que no es un rail de alimentación.', node)
                    elif name in parts.GROUND_NAMES and v != 0:
                        self.add('error', 'ground-pad',
                                 f'{ref}.{num} es {name} y queda en {shown}, no en masa.', node)
                    elif name in outs and v is not None and self.s.pin(node).type != 'power_out':
                        self.add('error', 'output-on-rail',
                                 f'{ref}.{num} es la salida {name} y queda unida al rail {g}.', node)

    def check_harness(self):
        for name, n, ba, ra, pa, bb, rb, pb in self.s.harness_pairs:
            if pa is None or pb is None:
                self.add('error', 'harness', f'{name} pin {n}: falta en {ra if pa is None else rb}.')
            elif (pa.net is None) != (pb.net is None):
                self.add('error', 'harness',
                         f'{name} pin {n}: {ba}:{ra} lleva {pa.net} y {bb}:{rb} lleva {pb.net}.')
            elif pa.net != pb.net:
                self.add('error', 'harness',
                         f'{name} pin {n}: nombres distintos a cada lado ({pa.net} / {pb.net}).')

    # -- signal resolution ----------------------------------------------------
    def resolve(self, mcu):
        spec_mcu = self.c['mcus'][mcu]
        board, ref = spec_mcu['ref'].split(':')
        comp = self.s.comp(board, ref)
        caps = self.mcu_ref[comp.mpn]
        for spec in spec_mcu['signals']:
            r = Resolved(mcu, spec['name'], spec['net'], spec['function'], spec=spec)
            self.signals[(mcu, spec['name'])] = r
            if spec['net'] not in self.s.boards[board].nets:
                self.add('error', 'signal-net', f'{mcu}.{r.name}: la red {spec["net"]} no existe en {board}.')
                continue
            g = self.s.gnet(board, spec['net'])
            pads = [n for n in self.s.members.get(g, []) if n.board == board and n.ref == ref]
            if len(pads) != 1:
                self.add('error', 'signal-pad',
                         f'{mcu}.{r.name}: {spec["net"]} llega a {len(pads)} pads de {ref}.', *pads)
                continue
            r.pad = pads[0]
            r.pin = self.s.physical_name(r.pad)
            drawn = self.s.pin(r.pad).name
            if drawn != r.pin:
                self.add('error', 'pin-shift',
                         f'{mcu}.{r.name}: el esquema dibuja {r.net} en {drawn}, pero el pad '
                         f'{r.pad.pin} es {r.pin} en el componente real.', r.pad)
                if caps['family'] == 'stm32' and not re.fullmatch(r'P[A-G]\d+', r.pin):
                    r.pin = None
                continue
            if caps['family'] == 'stm32':
                self._caps_stm32(r, caps)
            else:
                self._caps_esp32(r, caps)

    def _caps_stm32(self, r, caps):
        if not re.fullmatch(r'P[A-G]\d+', r.pin):
            self.add('error', 'signal-pad',
                     f'stm32.{r.name}: {r.net} cae en el pad {r.pad.pin}, que en el STM32 real es {r.pin}.', r.pad)
            r.pin = None
            return
        if r.pin in caps['reserved']:
            self.add('error', 'reserved-pin', f'stm32.{r.name} usa {r.pin}: {caps["reserved"][r.pin]}.', r.pad)
        if r.pin in caps['notes']:
            self.add('info', 'pin-note', f'stm32.{r.name} en {r.pin}: {caps["notes"][r.pin]}', r.pad)
        avail = caps['pins'].get(r.pin)
        if avail is None:
            self.add('error', 'pin-caps', f'stm32.{r.name}: {r.pin} no está en sim/reference/mcus.json; '
                     'añadir su fila desde la fuente de ST antes de usarlo.', r.pad)
            return
        names = {a.split(':')[0]: a for a in avail}
        f = r.function
        if f in ('gpio_out', 'gpio_in'):
            ok = 'GPIO' in names
        elif f == 'adc':
            chans = sorted(a for a in names if re.fullmatch(r'ADC\d_IN\d+', a))
            ok = bool(chans)
            if ok:
                inst, ch = re.fullmatch(r'ADC(\d)_IN(\d+)', chans[0]).groups()
                r.adc = (int(inst), int(ch))
                r.periph = chans[0]
        else:
            want = r.spec.get('periph')
            ok = want in names
            if ok:
                r.periph = want
                m = re.search(r':AF(\d+)$', names[want])
                if m:
                    r.af = int(m.group(1))
                else:
                    ok = False
                    self.add('error', 'pin-caps', f'stm32.{r.name}: {want} en {r.pin} sin número de AF en la referencia.', r.pad)
                    return
        if not ok:
            self.add('error', 'pin-caps',
                     f'stm32.{r.name}: {r.pin} no ofrece {r.spec.get("periph") or f} '
                     f'(tiene {", ".join(sorted(names))}).', r.pad)

    def _caps_esp32(self, r, caps):
        m = re.fullmatch(r'IO(\d+)', r.pin)
        if not m:
            self.add('error', 'signal-pad', f'esp32.{r.name}: {r.net} cae en {r.pin}, que no es un GPIO.', r.pad)
            r.pin = None
            return
        gpio = int(m.group(1))
        r.pin = f'GPIO{gpio}'
        r.periph = r.function
        if gpio in caps['unavailable']:
            self.add('error', 'reserved-pin', f'esp32.{r.name}: GPIO{gpio} lo usa la flash/PSRAM del N8R8.', r.pad)
        if gpio in caps['strapping']:
            self.add('warning', 'strapping-pin', f'esp32.{r.name} en GPIO{gpio}, pin de arranque.', r.pad)
        fixed = {'usb_dm': caps['fixed']['USB_D-'], 'usb_dp': caps['fixed']['USB_D+']}
        if r.function in fixed and gpio != fixed[r.function]:
            self.add('error', 'pin-caps', f'esp32.{r.name}: USB solo sale por GPIO{fixed[r.function]}.', r.pad)
        if gpio in fixed.values() and r.function not in fixed:
            self.add('warning', 'pin-caps', f'esp32.{r.name} ocupa GPIO{gpio}, que es USB.', r.pad)
        if r.function == 'adc':
            chan = caps['adc'].get(str(gpio))
            if chan is None:
                self.add('error', 'pin-caps', f'esp32.{r.name}: GPIO{gpio} no tiene ADC.', r.pad)
            elif chan.startswith('ADC2'):
                self.add('warning', 'pin-caps', f'esp32.{r.name}: {chan} no se puede leer con Wi-Fi activo.', r.pad)

    def check_coverage(self, mcu):
        spec = self.c['mcus'][mcu]
        board, ref = spec['ref'].split(':')
        claimed = {s['net'] for s in spec['signals']} | set(spec.get('system_nets', []))
        for net in spec.get('system_nets', []):
            if net not in self.s.boards[board].nets:
                self.add('warning', 'contract', f'{mcu}: la red de sistema {net} no existe.')
        for node in self.s.mcu_pins(spec):
            net = self.s.pin(node).net
            if net and net not in claimed:
                self.add('warning', 'unclaimed-net',
                         f'{mcu}: {ref}.{node.pin} ({self.s.physical_name(node)}) está en {net}, '
                         'que el contrato de firmware no usa.', node)

    # -- connectivity ---------------------------------------------------------
    def _target_net(self, text):
        mcu, _, name = text.partition(':')
        if mcu in self.c['mcus']:
            other = self.signals.get((mcu, name))
            if other is None:
                raise KeyError(f'{text} no es una señal del contrato')
            return other, self.s.gnet(self.c['mcus'][mcu]['ref'].split(':')[0], other.net)
        return None, self.s.net_of(self.s.endpoint(text))

    def check_paths(self, r):
        if r.pad is None:
            return
        g = self.s.net_of(r.pad)
        for key, reverse in (('reaches', False), ('from', True)):
            if key not in r.spec:
                continue
            try:
                other, target = self._target_net(r.spec[key])
            except KeyError as e:
                self.add('error', 'contract', f'{r.mcu}.{r.name}: {e}')
                continue
            seen = self.s.trace(g, reverse=reverse)
            if target not in seen:
                verb = 'no llega a' if not reverse else 'no recibe desde'
                self.add('error', 'signal-path', f'{r.mcu}.{r.name} ({r.pin}) {verb} {r.spec[key]}.', r.pad)
                continue
            hops = self.s.path(seen, target)
            r.path = [f'{a.board}:{a.ref}' for _, a, _, _ in hops]
            if other is not None:
                pair = {'uart_tx': 'uart_rx', 'uart_rx': 'uart_tx'}.get(r.function)
                if other.function != pair:
                    self.add('error', 'uart-pair',
                             f'{r.mcu}.{r.name} ({r.function}) enlaza con {r.spec[key]} ({other.function}).', r.pad)
            if key == 'reaches' and r.spec.get('interlocked'):
                self._check_interlock(r, hops)

    def _check_interlock(self, r, hops):
        want = self.s.find(self.c['interlock_net'])
        gates = []
        for _, a, b, _ in hops:
            comp = self.s.comp(a.board, a.ref)
            gate = parts.AND_GATES.get(comp.part, {}).get(self.s.physical_name(b))
            if gate:
                mine = self.s.physical_name(a)
                other = next(p for p in gate if p != mine)
                gates.append((a, self.s.net_of(self.s.node_by_name(a.board, a.ref, other))))
        if not any(net in self._buffered(want) for _, net in gates):
            found = ', '.join(f'{a.ref} con {net}' for a, net in gates) or 'ninguna puerta'
            self.add('error', 'interlock',
                     f'{r.mcu}.{r.name}: el camino a {r.spec["reaches"]} no pasa por una AND con '
                     f'{self.c["interlock_net"]} ({found}).', r.pad)

    def _buffered(self, net):
        """The net and every net that carries it through non-inverting buffers."""
        out, todo = {net}, [net]
        while todo:
            g = todo.pop()
            for node in self.s.members.get(g, []):
                comp = self.s.comp(node.board, node.ref)
                for y, a in parts.BUFFERS.get(comp.part, {}).items():
                    if self.s.physical_name(node) == a:
                        nxt = self.s.net_of(self.s.node_by_name(node.board, node.ref, y))
                        if nxt and nxt not in out:
                            out.add(nxt)
                            todo.append(nxt)
        return out

    # -- levels ---------------------------------------------------------------
    def _vdd(self, r):
        return self.s.voltages[self.s.find(self.c['mcus'][r.mcu]['vdd'])]

    def _internal_pull(self, r):
        spec = self.c['mcus'][r.mcu]
        caps = self.mcu_ref[self.s.comp(*spec['ref'].split(':')).mpn]
        pull = caps['reset_pulls'].get(self.s.physical_name(r.pad))
        if not pull:
            return []
        rail = self.s.find(spec['vdd']) if pull == 'up' else self._ground()
        return [(self.s.net_of(r.pad), rail, caps['reset_pull_ohms'])]

    def _ground(self):
        return next(g for g, v in self.s.voltages.items() if v == 0)

    def _level(self, v, vdd):
        if v < 0.3 * vdd:
            return 'low'
        if v > 0.7 * vdd:
            return 'high'
        return 'undefined'

    def check_reset(self, r):
        want = r.spec.get('reset')
        if want is None or r.pad is None:
            return
        g = self.s.net_of(r.pad)
        cluster = sorted(self.s.series_cluster(g))
        try:
            v = dc.solve(self.s, cluster, extra=self._internal_pull(r))
            levels = {n: self._level(v[n], self._vdd(r)) for n in cluster}
            got = 'undefined' if len(set(levels.values())) > 1 else next(iter(levels.values()))
            detail = ', '.join(f'{n.split(":")[1]}={v[n]:.2f} V' for n in cluster)
        except dc.Floating:
            got, detail = 'floating', 'sin resistencia a ningún rail'
        except dc.UnknownRail as e:
            got, detail = 'unknown', f'depende de {e}'
        r.reset_level = got
        if got != want:
            inputs = [str(n) for n in self.s.members.get(g, []) if n != r.pad]
            self.add('error', 'reset-level',
                     f'{r.mcu}.{r.name} ({r.pin}) con el MCU en reset queda {got}, se requiere {want} '
                     f'({detail}). Entradas en la red: {", ".join(inputs)}.', r.pad)

    def check_pull(self, r):
        want = r.spec.get('pull')
        if want is None or r.pad is None:
            return
        g = self.s.net_of(r.pad)
        cluster = self.s.series_cluster(g)
        found = []
        for ref, a, b, ohms in self.s.resistors():
            for x, y in ((a, b), (b, a)):
                if x in cluster and y in self.s.voltages:
                    found.append((ref, y, self.s.voltages[y]))
        ok = [f for f in found if (f[2] > 0) == (want == 'up')]
        if not ok:
            self.add('error', 'pull', f'{r.mcu}.{r.name} ({r.pin}): falta la resistencia de pull-{want}.', r.pad)

    # -- analog ---------------------------------------------------------------
    def check_analog(self, r):
        a = r.spec.get('analog')
        if not a or r.pad is None:
            return
        g = self.s.net_of(r.pad)
        vref = self.c['mcus'][r.mcu]['vref']
        lsb = vref / 2 ** self.c['mcus'][r.mcu]['adc_bits']
        try:
            getattr(self, f'_analog_{a["kind"]}')(r, a, g, vref, lsb)
        except (dc.Floating, dc.UnknownRail) as e:
            self.add('error', 'analog', f'{r.mcu}.{r.name}: no se puede resolver la red ({e}).', r.pad)

    def _analog_divider(self, r, a, g, vref, lsb):
        src = self.s.find(a['source_net'])
        lo, hi = a['range_v']
        v_hi = dc.solve(self.s, [g], fixed={src: hi})[g]
        gain = v_hi / hi
        self.analog.append((r.name, f'{hi:g} V → {v_hi:.3f} V; fondo de escala {vref / gain:.1f} V; '
                                    f'{lsb / gain * 1000:.1f} mV/LSB'))
        if v_hi > 0.98 * vref:
            self.add('error', 'analog', f'{r.mcu}.{r.name}: {hi} V dan {v_hi:.2f} V en {r.pin}, por encima del ADC.', r.pad)

    def _analog_ntc(self, r, a, g, vref, lsb):
        n1, n2 = (self.s.net_of(self.s.endpoint(x)) for x in a['between'])

        def volts(t):
            ohms = a['r25'] * math.exp(a['beta'] * (1 / (t + 273.15) - 1 / 298.15))
            return dc.solve(self.s, [g], extra=[(n1, n2, ohms)])[g]

        lo_w, hi_w = a['window']
        for t in a['range_c']:
            v = volts(t)
            if not lo_w * vref <= v <= hi_w * vref:
                self.add('error', 'analog',
                         f'{r.mcu}.{r.name}: a {t} °C el ADC ve {v:.3f} V, fuera de la ventana '
                         f'{lo_w:.0%}–{hi_w:.0%} que separa la medida de abierto/corto.', r.pad)
        rows = []
        for t in a['check_c']:
            slope = abs(volts(t + 0.5) - volts(t - 0.5))
            res = lsb / slope
            rows.append(f'{t} °C: {volts(t):.3f} V, {res:.3f} °C/LSB')
            if res > a['max_c_per_lsb']:
                self.add('error', 'analog', f'{r.mcu}.{r.name}: {res:.2f} °C/LSB a {t} °C.', r.pad)
        ends = ', '.join(f'{t} °C → {volts(t):.3f} V' for t in a['range_c'])
        self.analog.append((r.name, f'{ends}; ' + '; '.join(rows)))

    def _analog_ipropi(self, r, a, g, vref, lsb):
        vr = self.s.find(a['vref_net'])
        v_vref = dc.solve(self.s, [vr])[vr]
        per_amp = dc.solve(self.s, [g], inject={g: a['gain_a_per_a']})[g]
        itrip = v_vref / per_amp
        self.analog.append((r.name, f'VREF {v_vref:.3f} V; regulación a {itrip:.2f} A; '
                                    f'{per_amp:.3f} V/A; {lsb / per_amp * 1000:.2f} mA/LSB'))
        if v_vref > 3.6:
            self.add('error', 'analog', f'{r.mcu}.{r.name}: VREF del DRV8876 a {v_vref:.2f} V (> 3,6 V).', r.pad)
        if v_vref > vref:
            self.add('warning', 'analog', f'{r.mcu}.{r.name}: el ADC satura antes del límite de corriente.', r.pad)

    # -- front panel ----------------------------------------------------------
    def check_keypad(self):
        k = self.c.get('keypad')
        if not k:
            return
        board, ref = k['device'].split(':')
        addr = 0x20
        for bit, name in enumerate(('A0', 'A1', 'A2')):
            g = self.s.net_of(self.s.node_by_name(board, ref, name))
            v = self.s.voltages.get(g)
            if v is None:
                self.add('error', 'keypad', f'{ref}.{name} no está fijado a masa ni a 3,3 V ({g}).')
            elif v > 0:
                addr |= 1 << bit
        if addr != int(k['address'], 16):
            self.add('error', 'keypad', f'{ref} responde en 0x{addr:02X}, el firmware espera {k["address"]}.')
        for text, pin in zip(k['bus'], ('SCL', 'SDA')):
            mcu, name = text.split(':')
            sig = self.signals.get((mcu, name))
            dev = self.s.net_of(self.s.node_by_name(board, ref, pin))
            if sig is None or sig.pad is None or dev not in self.s.trace(self.s.net_of(sig.pad)):
                self.add('error', 'keypad', f'{ref}.{pin} no está en el bus de {text}.')
        for port, sw in k['keys'].items():
            g = self.s.net_of(self.s.node_by_name(board, ref, port))
            nets = self.s.series_cluster(g)
            sw_nets = {self.s.net_of(Node(board, sw, n)) for n in self.s.comp(board, sw).pins}
            if not nets & sw_nets:
                self.add('error', 'keypad', f'{ref}.{port} no llega a {sw}.')
            elif self._ground() not in sw_nets:
                self.add('error', 'keypad', f'{sw} no cierra a masa: la tecla no sería activa a 0.')
            pulled = any((x in nets and self.s.voltages.get(y, 0) > 0) or (y in nets and self.s.voltages.get(x, 0) > 0)
                         for _, x, y, _ in self.s.resistors())
            if not pulled:
                self.add('error', 'keypad', f'{ref}.{port} ({sw}) sin pull-up.')
        for port, led in k['leds'].items():
            g = self.s.net_of(self.s.node_by_name(board, ref, port))
            k_net = self.s.net_of(self.s.node_by_name(board, led, 'K'))
            if g != k_net:
                self.add('error', 'keypad', f'{ref}.{port} no gobierna el cátodo de {led}.')

    def check_backfeed(self):
        """An external supply must not reach a converter's switch node.

        Followed through inductors and fuses, the low-impedance series parts,
        and not across another rail: a diode or a divider does not back-feed.
        A synchronous buck's switch node cannot sit above its input (the
        high-side body diode back-feeds it), so a bench supply on its output
        node drives the converter outside its absolute ratings.
        """
        sw = {}
        for board, b in self.s.boards.items():
            for ref, comp in b.components.items():
                name = parts.SWITCH_NODES.get(comp.part)
                if name:
                    sw[self.s.net_of(self.s.node_by_name(board, ref, name))] = f'{ref}.{name}'
        for pin in self.c.get('external_supplies', {}).get('pins', []):
            start = self.s.net_of(self.s.endpoint(pin))
            seen, todo = {start}, [start]
            while todo:
                g = todo.pop()
                if g in sw:
                    self.add('error', 'back-feed',
                             f'{pin} llega a {sw[g]} por bobinas o fusibles: con el convertidor sin '
                             'entrada, la fuente externa pone su nodo de conmutación por encima de VIN.')
                    break
                if g in self.s.rails and g != start:
                    continue
                for node in self.s.members.get(g, []):
                    comp = self.s.comp(node.board, node.ref)
                    if comp.part in ('L', 'FUSE') and len(comp.pins) == 2:
                        other = self.s.net_of(Node(node.board, node.ref, next(n for n in comp.pins if n != node.pin)))
                        if other and other not in seen:
                            seen.add(other)
                            todo.append(other)

    def check_ui_domain(self):
        """Logic pull-ups on another rail than the MCU's: back-feed when it is off."""
        by_rail = {}
        for (mcu, name), r in sorted(self.signals.items()):
            if r.pad is None:
                continue
            vdd = self.s.find(self.c['mcus'][mcu]['vdd'])
            cluster = self.s.series_cluster(self.s.net_of(r.pad))
            for ref, a, b, _ in self.s.resistors():
                for x, y in ((a, b), (b, a)):
                    v = self.s.voltages.get(y)
                    if x in cluster and y != vdd and v and v <= self.s.voltages[vdd]:
                        by_rail.setdefault((y, vdd), []).append(f'{mcu}.{name} ({ref.split(":")[1]})')
        for (rail, vdd), users in by_rail.items():
            self.add('info', 'power-domain',
                     f'{", ".join(users)} tienen pull-up a {rail}, no a {vdd}: con {rail} apagado '
                     'los GPIO en alto lo alimentan a través de esas líneas.')
