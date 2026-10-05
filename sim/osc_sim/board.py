"""The STM32 firmware running on the virtual board, in 1 ms steps (F1).

Each step the pins the firmware drives (sim/hal/hal_sim.c) become Thevenin
sources on the netlists, sim/osc_sim/circuit.py solves the boards with the
plant attached, U601 (TPS3828) watches WDI and holds STM_NRST, and the
resulting levels, ADC codes and timer edges go back to the firmware. U601's
timings are a parameter so a test can take the end of each range that makes
it fail: the shortest watchdog time-out and the longest reset delay.
"""
import re
from dataclasses import dataclass, field

from .circuit import X
from .drive import Bench
from .model import Node
from .plant import Plant

DEAD_BATTERY_OHMS = 5100.0  # UCPD Rd, USB Type-C 5.1 kOhm


@dataclass
class Event:
    t: float
    kind: str
    detail: str = ''


@dataclass
class Supervisor:
    """TPS3828 watchdog and reset delay (sim/reference/devices.json)."""
    watchdog_s: float
    delay_s: float
    reset_until: float = 0.0
    last_edge: float = 0.0
    wdi: object = None
    latched: bool = False

    def asserting(self, t):
        return self.latched or t < self.reset_until


class VirtualBoard:
    def __init__(self, checker, firmware=None, plant=None, corner=None, watchdog='min', delay='max'):
        self.k = checker
        self.s = checker.s
        self.bench = Bench(checker)
        self.circuit = self.bench.circuit
        self.fw = firmware
        self.plant = plant or Plant()
        self.corner = corner
        self.rails = self.bench.rails(corner)
        self.vdd = self.rails[self.bench.vdd_net]
        u601 = next(d for d in self.circuit.devices if d.kind == 'supervisor')
        self.u601 = u601
        p = u601.params
        pick = {'min': 0, 'typ': 1, 'max': 2}
        self.sup = Supervisor(p['watchdog_s'][pick[watchdog]], p['reset_delay_s'][pick[delay]])
        # Power-up: RESET held for td, then the watchdog starts timing.
        self.sup.reset_until = self.sup.last_edge = self.sup.delay_s
        self.wdi_net = u601.pins['WDI']
        self.nrst = self.bench.nrst
        self.mcu = self.circuit.mcus['stm32']
        self.t = 0.0
        self.ms = 0
        self.events = []
        self.nrst_high = False
        # STM32 pads by (port, pin).
        board, ref = self.bench.mcu_board, self.bench.mcu_ref
        self.pads = {}
        for num in self.s.comp(board, ref).pins:
            node = Node(board, ref, num)
            m = re.fullmatch(r'P([A-F])(\d+)', self.s.physical_name(node))
            net = self.s.net_of(node)
            if m and net:
                self.pads[(ord(m.group(1)) - ord('A'), int(m.group(2)))] = (net, m.group(0))
        self.adc_pins = {}
        for (mcu, name), r in checker.signals.items():
            if mcu == 'stm32' and r.adc and r.pad is not None:
                self.adc_pins[name] = (self.s.net_of(r.pad), r.adc)
        self.dead_battery = [p for p, (_, n) in self.pads.items() if n in ('PB4', 'PB6')]
        self.flow_key = None
        r = checker.signals.get(('stm32', 'FLOW'))
        if r and r.pin:
            self.flow_key = (ord(r.pin[1]) - ord('A'), int(r.pin[2:]))
        self._flow_level = True
        self.uart_tx = {r.pin for (mcu, _), r in checker.signals.items()
                        if mcu == 'stm32' and r.function == 'uart_tx' and r.pin}
        self.out = None
        self.loads_state = {}
        self._cache = {}

    # -- one step ---------------------------------------------------------------
    def drives(self):
        vdd = self.vdd
        d = [(self.nrst, vdd, self.mcu['nrst_pullup_ohms'][1])]
        running = self.fw is not None and self.fw.running
        if not running:
            d += self.bench.reset_pulls(vdd)
        io = self.fw.io if self.fw is not None else None
        if io is None or io.dead_battery:
            d += [(self.pads[p][0], 0.0, DEAD_BATTERY_OHMS) for p in self.dead_battery]
        if running:
            for (port, pin), (net, name) in self.pads.items():
                mode = io.mode[port][pin]
                if mode == 2:
                    d.append(self.circuit.mcu_drive('stm32', net, bool(io.odr[port][pin]), vdd, name))
                elif mode == 3 and (port, pin) != self.flow_key:
                    # Timer outputs at their duty (0 or full); UART TX idles high.
                    duty = io.pwm[port][pin]
                    high = duty >= 500 if duty else name in self.uart_tx
                    d.append(self.circuit.mcu_drive('stm32', net, high, vdd, name))
        return d

    def plant_loads(self):
        out = []
        for el in self.plant.elements():
            if el[0] == 'src':
                out.append(('src', self.s.net_of(self.s.endpoint(el[1])), el[2], el[3]))
            else:
                a, b = (self.s.net_of(self.s.endpoint(e)) for e in el[1:3])
                out.append((el[0], a, b, *el[3:]))
        return out

    def solve(self):
        """Operating point for the present pins and plant, cached on its inputs.

        Plant values are rounded to four digits (NTC, EMF, motor current) so the
        cache holds while they drift.
        """
        drives = tuple(self.drives())
        loads = tuple(tuple(_round(x) for x in el) for el in self.plant_loads())
        asserting = self.sup.asserting(self.t)
        amps = _round(self.plant.motor_amps)
        key = (drives, loads, asserting, amps)
        out = self._cache.get(key)
        if out is None:
            out = self.circuit.evaluate(self.rails, drives, loads, supervisor_reset=asserting,
                                        bridge_amps={'controller:U501': amps})
            if len(self._cache) > 4096:
                self._cache.clear()
            self._cache[key] = out
        return out

    def step(self, dt=0.001):
        sup = self.sup
        out = self.solve()
        self.out = out
        run = out.lo
        for ref, why in out.undefined():
            self._event('undefined', f'{ref}: {why}')
        # U601 watches WDI.
        lv = self._level(run.volts.get(self.wdi_net), self.u601.params['wdi_vih_frac'], self.u601.params['wdi_vil_frac'])
        if lv is X:
            self._event('wdi-undefined', f'WDI a {run.volts.get(self.wdi_net)}')
        elif sup.wdi is True and lv is False:
            if sup.asserting(self.t):
                # TPS382x (not A): WDI edges while RESET is low latch it low.
                sup.latched = True
                self._event('reset-latched', 'flanco en WDI con RESET activo (TPS3828 sin sufijo A)')
            sup.last_edge = self.t
        if lv is not X:
            sup.wdi = lv
        if not sup.asserting(self.t) and self.t - sup.last_edge >= sup.watchdog_s:
            sup.reset_until = self.t + sup.delay_s
            sup.last_edge = sup.reset_until
            self._event('watchdog', f'sin flanco en WDI durante {sup.watchdog_s:g} s')
        # STM_NRST decides whether the core runs.
        nrst = self._level(run.volts.get(self.nrst), self.mcu['vih_frac'], self.mcu['vil_frac'])
        if self.fw is not None:
            if nrst is False and self.fw.running:
                self.fw.reset()
                self._event('reset', 'STM_NRST bajo')
            elif nrst is True and not self.fw.running:
                self.fw.start(self.ms)
                self._event('boot', 'STM_NRST liberado')
        self.nrst_high = nrst is True
        self._inputs(run)
        # Loads and the plant.
        live = lambda e: out.classify(self.s.net_of(self.s.endpoint(e)), 'live')  # noqa: E731
        v1, v2 = run.volts.get(self.s.net_of(self.s.endpoint('controller:J108.2'))), \
            run.volts.get(self.s.net_of(self.s.endpoint('controller:J108.1')))
        motor = (v1 - v2) if v1 is not None and v2 is not None else 0.0
        vv = [run.volts.get(self.s.net_of(self.s.endpoint(e))) for e in ('controller:J113.1', 'controller:J113.2')]
        valve = vv[0] - vv[1] if None not in vv else 0.0
        self.loads_state = {'heater': live('controller:J116.1'), 'pump': live('controller:J117.1'),
                            'grinder': live('controller:J115.1'), 'mains': live('controller:Q703.A2'),
                            'valve_v': valve, 'motor_v': motor,
                            'ui': self.s.find('controller:3V3_UI') and
                            (run.volts.get(self.s.find('controller:3V3_UI')) or 0.0) > 0.9 * self.vdd}
        self.plant.step(dt, self.loads_state['heater'] is True, self.loads_state['pump'] is True, motor)
        self.t += dt
        self.ms += round(dt * 1000)
        if self.fw is not None:
            self.fw.poll(self.ms)

    def run(self, seconds, dt=0.001, until=None, each=None):
        for _ in range(round(seconds / dt)):
            if each:
                each(self)
            self.step(dt)
            if until and until(self):
                return True
        return False

    def force(self, name, active):
        """Drive an STM32 order directly, as a stuck or runaway core would."""
        r = self.k.signals[('stm32', name)]
        port, pin = ord(r.pin[1]) - ord('A'), int(r.pin[2:])
        high = bool(active) == (r.spec.get('active', 'high') == 'high')
        io = self.fw.io
        io.odr[port][pin] = 1 if high else 0
        io.mode[port][pin] = 2
        io.pwm[port][pin] = 0

    def pin_level(self, name):
        """Input level the STM32 sees on a contract signal: True, False or None."""
        r = self.k.signals[('stm32', name)]
        port, pin = ord(r.pin[1]) - ord('A'), int(r.pin[2:])
        io = self.fw.io
        return bool(io.idr[port][pin]) if io.idr_valid[port][pin] else None

    def adc_code(self, name):
        net, (adc, ch) = self.adc_pins[name]
        return self.fw.io.adc[adc - 1][ch]

    # -- helpers ------------------------------------------------------------------
    def _level(self, v, vih_frac, vil_frac):
        if v is None:
            return X
        if v >= vih_frac * self.vdd:
            return True
        if v <= vil_frac * self.vdd:
            return False
        return X

    def _inputs(self, run):
        if self.fw is None:
            return
        io = self.fw.io
        p = self.mcu
        for (port, pin), (net, name) in self.pads.items():
            lv = self._level(run.volts.get(net), p['vih_frac'], p['vil_frac'])
            io.idr[port][pin] = 1 if lv is True else 0
            io.idr_valid[port][pin] = 0 if lv is X else 1
            if (port, pin) == self.flow_key and lv is not X:
                if self._flow_level and not lv:
                    io.edges[port][pin] += 1
                self._flow_level = lv
        vdda = self.vdd
        for name, (net, (adc, ch)) in self.adc_pins.items():
            v = run.volts.get(net) or 0.0
            io.adc[adc - 1][ch] = max(0, min(4095, round(v / vdda * 4095)))

    def _event(self, kind, detail=''):
        last = self.events[-1] if self.events else None
        if last and last.kind == kind and last.detail == detail:
            return
        self.events.append(Event(round(self.t, 4), kind, detail))

    def kinds(self, kind):
        return [e for e in self.events if e.kind == kind]


def _round(x):
    if isinstance(x, float) and x:
        return float(f'{x:.4g}')
    return x
