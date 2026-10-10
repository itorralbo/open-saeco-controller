"""Both firmwares running on the virtual board, in 1 ms steps (F1, F2).

Each step the pins the firmware drives (sim/hal/hal_sim.c) become Thevenin
sources on the netlists, sim/osc_sim/circuit.py solves the boards with the
plant attached, U601 (TPS3828) watches WDI and holds STM_NRST, and the
resulting levels, ADC codes and timer edges go back to the firmware. U601's
timings are a parameter so a test can take the end of each range that makes
it fail: the shortest watchdog time-out and the longest reset delay.

With an ESP32 attached (F2) its pins join the circuit too, the front panel
(sim/osc_sim/front.py) answers its I2C and SPI from the voltages on the far
side of the harness, and the UART carries bytes between the two firmwares
only while both pins are configured and the line idles high at the
receiver. An ESP32 pin driven high into the front panel while 3V3_UI is off
is recorded as a 'backfeed' event.
"""
from collections import deque
import random
import re
from dataclasses import dataclass, field

from .circuit import X
from .drive import Bench
from .firmware import ESP_PIN
from .front import LCD_VCC_MIN, TCA_VCC_MIN, TCA_VIH, TCA_VIL, FrontPanel
from .model import Node
from .plant import Plant

DEAD_BATTERY_OHMS = 5100.0  # UCPD Rd, USB Type-C 5.1 kOhm
VREFINT_V = 1.212           # DS12589: 1.182 / 1.212 / 1.232 V; the part's own value is calibrated
UART_BYTES_PER_MS = 11      # 115200 baud, 8N1
ESP_BOOT_S = 0.35           # ASSUMED: EN RC (R201/C201) plus ROM and bootloader
OPEN_DRAIN_OHMS = 50.0


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
    def __init__(self, checker, firmware=None, plant=None, corner=None, watchdog='min', delay='max',
                 esp=None, front=None, esp_boot_s=ESP_BOOT_S):
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
        # Alternate functions that drive their pin; timer and UART inputs do not.
        self.af_outputs = {r.pin for (mcu, _), r in checker.signals.items()
                           if mcu == 'stm32' and r.function in ('pwm', 'uart_tx') and r.pin}
        self.out = None
        self.loads_state = {}
        self._cache = {}
        self.faults = set()        # refs whose open-drain fault output is pulled low
        self.uart_noise = 0.0      # probability that a UART byte arrives with a bit flipped
        self._rng = random.Random(1)
        self.vrefint_v = VREFINT_V
        if firmware is not None:
            firmware.io.vrefint_cal = round(self.vrefint_v / 3.0 * 4095)
        self._init_esp(esp, front, esp_boot_s)

    def _init_esp(self, esp, front, boot_s):
        s, k = self.s, self.k
        self.esp = esp
        self.front = front or FrontPanel()
        self.ui_volts = 0.0
        self.esp_boot_s = boot_s
        self.esp_mcu = self.circuit.mcus['esp32']
        board, ref = k.c['mcus']['esp32']['ref'].split(':')
        self.esp_pads = {}
        for num in s.comp(board, ref).pins:
            node = Node(board, ref, num)
            m = re.fullmatch(r'IO(\d+)', s.physical_name(node))
            net = s.net_of(node)
            if m and net:
                self.esp_pads[int(m.group(1))] = net
        front_nets = {g for g, nodes in s.members.items() if any(n.board == 'front' for n in nodes)}
        self.esp_front = {gpio for gpio, net in self.esp_pads.items()
                          if net not in s.rails and s.series_cluster(net) & front_nets}
        self.ui_net = s.find('controller:3V3_UI')
        u1 = lambda name: s.net_of(s.node_by_name('front', 'U1', name))  # noqa: E731
        self.tca_pins = [u1(f'P{i}') for i in range(8)]
        self.tca_int, self.tca_sda, self.tca_scl = u1('~{INT}'), u1('SDA'), u1('SCL')
        sig = lambda m, n: k.signals[(m, n)]  # noqa: E731
        gpio = lambda n: int(sig('esp32', n).pin[4:])  # noqa: E731
        self.lcd_bl = s.net_of(s.endpoint(sig('esp32', 'LCD_BL').spec['reaches']))
        self.lcd_rst = s.net_of(s.endpoint(sig('esp32', 'LCD_RST_N').spec['reaches']))
        self.esp_dc, self.esp_rst = gpio('LCD_DC'), gpio('LCD_RST_N')
        self.esp_tx, self.esp_rx = gpio('UART_TX'), gpio('UART_RX')
        pad = lambda n: (ord(sig('stm32', n).pin[1]) - ord('A'), int(sig('stm32', n).pin[2:]))  # noqa: E731
        self.stm_tx, self.stm_rx = pad('UART_TX'), pad('UART_RX')
        self.to_esp, self.to_stm = deque(), deque()
        self.uart_dropped = 0
        if esp is not None:
            esp.attach(self._i2c, self._spi)

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
                elif mode == 3 and name in self.af_outputs:
                    # Timer outputs at their duty (0 or full); UART TX idles high.
                    duty = io.pwm[port][pin]
                    high = duty >= 500 if duty else name in self.uart_tx
                    d.append(self.circuit.mcu_drive('stm32', net, high, vdd, name))
        d += self._esp_drives(vdd)
        tca = self.front.tca
        if tca.int_low:
            d.append((self.tca_int, 0.0, OPEN_DRAIN_OHMS))
        if tca.powered and not tca.config & 0x80:
            # P7 push-pull output: the standby LED's cathode.
            d.append((self.tca_pins[7], self.ui_volts if tca.output & 0x80 else 0.0, 25.0))
        return d

    def _esp_drives(self, vdd):
        esp = self.esp
        if esp is None or not esp.running:
            return []
        io, d = esp.io, []
        for gpio, net in sorted(self.esp_pads.items()):
            high = self._esp_high(gpio)
            if high is not None:
                d.append(self.circuit.mcu_drive('esp32', net, high, vdd, f'GPIO{gpio}'))
        return d

    def _esp_high(self, gpio):
        """Level an ESP32 pin drives (True/False) or None when it does not drive."""
        io = self.esp.io
        mode = ESP_PIN[io.mode[gpio]]
        if mode == 'output':
            return bool(io.level[gpio])
        if mode in ('spi_clk', 'spi_mosi'):
            return False
        if mode in ('spi_cs', 'uart_tx'):
            return True  # idle levels
        if mode == 'ledc':
            return io.duty[gpio] > 0
        return None

    def plant_loads(self):
        out = []
        for el in self.plant.elements() + self.front.elements():
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
        self.ui_volts = (self.out.lo.volts.get(self.ui_net) or 0.0) if self.out else 0.0
        drives = tuple(self.drives())
        loads = tuple(tuple(_round(x) for x in el) for el in self.plant_loads())
        asserting = self.sup.asserting(self.t)
        amps = _round(self.plant.motor_amps)
        # U704 sees the grinder's full-wave current; 10 mA steps keep the cache useful.
        grind = round(self.plant.grinder_amps, 2)
        faults = tuple(sorted(self.faults))
        key = (drives, loads, asserting, amps, grind, faults)
        out = self._cache.get(key)
        if out is None:
            out = self.circuit.evaluate(self.rails, drives, loads, supervisor_reset=asserting,
                                        bridge_amps={'controller:U501': amps},
                                        sense_amps={'controller:U704': grind}, faults=faults)
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
        self._front(run)
        # Loads and the plant.
        live = lambda e: out.classify(self.s.net_of(self.s.endpoint(e)), 'live')  # noqa: E731
        v1, v2 = run.volts.get(self.s.net_of(self.s.endpoint('controller:J108.7'))), \
            run.volts.get(self.s.net_of(self.s.endpoint('controller:J108.8')))
        motor = (v1 - v2) if v1 is not None and v2 is not None else 0.0
        vv = [run.volts.get(self.s.net_of(self.s.endpoint(e))) for e in ('controller:J113.1', 'controller:J113.2')]
        valve = vv[0] - vv[1] if None not in vv else 0.0
        self.loads_state = {'heater': live('controller:J116.1'), 'pump': live('controller:J117.1'),
                            'grinder': live('controller:J115.1'), 'mains': live('controller:Q703.A2'),
                            'valve_v': valve, 'motor_v': motor,
                            'ui': self.s.find('controller:3V3_UI') and
                            (run.volts.get(self.s.find('controller:3V3_UI')) or 0.0) > 0.9 * self.vdd}
        self.plant.step(dt, self.loads_state['heater'] is True, self.loads_state['pump'] is True, motor,
                        valve_on=valve > 12.0, grinder_on=self.loads_state['grinder'] is True)
        self.t += dt
        self.ms += round(dt * 1000)
        if self.fw is not None:
            self.fw.poll(self.ms)
        if self.esp is not None:
            if not self.esp.running and self.t >= self.esp_boot_s:
                self.esp.start(self.ms)
                self._event('esp-boot')
            self.esp.poll(self.ms)
            self._uart(run)

    # -- F2: ESP32, front panel and UART ------------------------------------------
    def _front(self, run):
        ui = run.volts.get(self.ui_net) or 0.0
        self.ui_volts = ui
        tca, lcd = self.front.tca, self.front.lcd
        tca.power(ui >= TCA_VCC_MIN)
        lcd.power(ui >= LCD_VCC_MIN)
        pins = 0
        for i, net in enumerate(self.tca_pins):
            v = run.volts.get(net)
            if v is None or v >= TCA_VIH * ui:
                pins |= 1 << i
            elif v > TCA_VIL * ui:
                pins |= 1 << i
                tca.undefined += 1
        tca.pins = pins
        rst = run.volts.get(self.lcd_rst)
        if lcd.powered and rst is not None and rst <= 0.3 * ui:
            lcd.reset()
        bl = run.volts.get(self.lcd_bl)
        lcd.backlight = bl is not None and ui > 0 and bl >= 0.7 * ui
        if self.esp is None or not self.esp.running:
            return
        io, p = self.esp.io, self.esp_mcu
        for gpio, net in self.esp_pads.items():
            if ESP_PIN[io.mode[gpio]] in ('input', 'i2c', 'uart_rx'):
                lv = self._level(run.volts.get(net), p['vih_frac'], p['vil_frac'])
                io.in_[gpio] = 1 if lv is True else 0
                io.in_valid[gpio] = 0 if lv is X else 1
            if ui < 1.0 and gpio in self.esp_front and self._esp_high(gpio):
                self._event('backfeed', f'GPIO{gpio} en alto con 3V3_UI a {ui:.2f} V')

    def _i2c(self, addr, w, rn):
        run = self.out.lo if self.out else None
        if run is None:
            return None
        vdd = self.vdd
        for net in (self.tca_sda, self.tca_scl):
            v = run.volts.get(net)
            if v is None or v < self.esp_mcu['vih_frac'] * vdd:
                return None  # no pull-up: the bus never releases high
        if addr != self.front.tca.address:
            return None
        return self.front.tca.xfer(w, rn)

    def _spi(self, data):
        io, ui = self.esp.io, self.ui_volts
        dc = bool(io.level[self.esp_dc]) if ESP_PIN[io.mode[self.esp_dc]] == 'output' else False
        rst_mode = ESP_PIN[io.mode[self.esp_rst]]
        rst_high = bool(io.level[self.esp_rst]) if rst_mode == 'output' else ui > 2.0  # R5 pull-up
        self.front.lcd.spi(data, dc, rst_high)

    def _uart(self, run):
        fw, esp = self.fw, self.esp
        p = self.esp_mcu
        stm_tx = fw is not None and fw.running and fw.io.mode[self.stm_tx[0]][self.stm_tx[1]] == 3 \
            and fw.io.af[self.stm_tx[0]][self.stm_tx[1]] == 7
        stm_rx = fw is not None and fw.running and fw.io.mode[self.stm_rx[0]][self.stm_rx[1]] == 3 \
            and fw.io.af[self.stm_rx[0]][self.stm_rx[1]] == 7
        esp_tx = esp.running and ESP_PIN[esp.io.mode[self.esp_tx]] == 'uart_tx'
        esp_rx = esp.running and ESP_PIN[esp.io.mode[self.esp_rx]] == 'uart_rx'
        if fw is not None:
            if stm_tx:
                self.to_esp.extend(fw.io.uart_tx[:fw.io.uart_tx_len])
            fw.io.uart_tx_len = 0
        if esp_tx:
            self.to_stm.extend(esp.io.uart_tx[:esp.io.uart_tx_len])
        esp.io.uart_tx_len = 0
        # Bytes only arrive where the line idles high at the receiving pad. A
        # receiver that is listening keeps them queued while the line is not
        # idle yet (the transmitter was enabled this very step); one that is
        # not listening loses them.
        idle = lambda net, vdd, frac: (run.volts.get(net) or 0.0) >= frac * vdd  # noqa: E731
        self._deliver(self.to_esp, esp.io if esp_rx else None,
                      idle(self.esp_pads[self.esp_rx], self.vdd, p['vih_frac']))
        self._deliver(self.to_stm, fw.io if (fw is not None and stm_rx) else None,
                      idle(self.pads[self.stm_rx][0], self.vdd, self.mcu['vih_frac']))

    def set_corner(self, corner):
        """Supplies at their minimum (0), maximum (1) or nominal (None)."""
        self.corner = corner
        self.rails = self.bench.rails(corner)
        self.vdd = self.rails[self.bench.vdd_net]
        self._cache.clear()

    def _deliver(self, queue, io, line_idle):
        if io is not None and not line_idle:
            while len(queue) > 4 * UART_BYTES_PER_MS:
                queue.popleft()
                self.uart_dropped += 1
            return
        for _ in range(min(UART_BYTES_PER_MS, len(queue))):
            byte = queue.popleft()
            if self.uart_noise and self._rng.random() < self.uart_noise:
                byte ^= 1 << self._rng.randrange(8)
            if io is None:
                self.uart_dropped += 1
                continue
            if io.uart_rx_head >= io.uart_rx_len:
                io.uart_rx_head = io.uart_rx_len = 0
            if io.uart_rx_len < len(io.uart_rx):
                io.uart_rx[io.uart_rx_len] = byte
                io.uart_rx_len += 1
            else:
                self.uart_dropped += 1

    def press(self, sw, down=True):
        """Press or release a front-panel key by its switch (SW1-SW7)."""
        (self.front.pressed.add if down else self.front.pressed.discard)(sw)

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
        io.adc[0][18] = round(self.vrefint_v / vdda * 4095)  # ADC1_IN18, VREFINT

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
