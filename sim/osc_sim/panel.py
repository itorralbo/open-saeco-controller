"""Local web panel of the virtual machine (F3).

  python tools/sim_panel.py [--port 8765] [--speed 1]

A thread runs both firmwares on the virtual board in real time (or faster);
the page in sim/panel/ shows the front panel and its display, the state of
both cores, loads and plant, plots, an event log, fault injection, and a VCD
of the digital signals. Standard library only; it listens on 127.0.0.1.
"""
import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import firmware
from .board import VirtualBoard
from .checks import Checker
from .model import ROOT, System, load_contract
from .plant import Plant
from .vcd import Recorder

PAGE = ROOT / 'sim/panel/index.html'
HISTORY_MS = 50
KEYS = [f'SW{i}' for i in range(1, 8)]


class Session:
    def __init__(self, speed=1.0, corner=None, checker=None):
        if checker is None:
            checker = Checker(System(load_contract(ROOT), ROOT))
            checker.run()
        self.checker = checker
        self.lock = threading.RLock()
        self.speed = speed
        self.paused = False
        self.corner = corner
        self._build()
        self._stop = threading.Event()
        self.thread = None

    def _build(self):
        self.plant = Plant()
        self.board = VirtualBoard(self.checker, firmware.Firmware(), self.plant, corner=self.corner,
                                  esp=firmware.EspFirmware())
        self.history = deque(maxlen=1200)
        b = self.board
        orders = sorted(n for (m, n), r in self.checker.signals.items()
                        if m == 'stm32' and r.function in ('gpio_out', 'pwm'))
        self.orders = orders
        self._orders_names = orders
        names = (['STM_NRST', 'WDI', 'STM_LINK', 'ESP_LINK', 'UI_POWER', 'LCD_BL', 'STBY_LED']
                 + [f'PB_{n}' for n in orders]
                 + ['HEATER', 'PUMP', 'GRINDER', 'MAINS', 'VALVE', 'BREW_FWD', 'BREW_REV']
                 + KEYS + ['CORE_STATE', 'ESP_PAGE', 'TEST_ID', 'TEST_PHASE'])
        self.vcd = Recorder(names, widths={'CORE_STATE': 2, 'ESP_PAGE': 3, 'TEST_ID': 3, 'TEST_PHASE': 3})
        self._wdi = b.u601.pins['WDI']

    # -- running ----------------------------------------------------------------
    def start(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=2)

    def _loop(self):
        last = time.monotonic()
        owed = 0.0
        while not self._stop.is_set():
            now = time.monotonic()
            with self.lock:
                if not self.paused:
                    owed = min(owed + (now - last) * 1000 * self.speed, 250)
                    steps = int(owed)
                    owed -= steps
                    self.advance(steps)
                else:
                    owed = 0.0
            last = now
            time.sleep(0.005)

    def advance(self, ms):
        b = self.board
        for _ in range(ms):
            b.step()
            self.vcd.sample(b.t * 1e6, self._digital())
            if b.ms % HISTORY_MS == 0:
                self.history.append(self._analog())

    def _digital(self):
        b, fw, esp = self.board, self.board.fw, self.board.esp
        run = b.out.lo if b.out else None
        v = (lambda net: run.volts.get(net)) if run else (lambda net: None)  # noqa: E731
        wdi = v(self._wdi)
        out = {'STM_NRST': b.nrst_high, 'WDI': None if wdi is None else wdi > 0.5 * b.vdd,
               'STM_LINK': fw.link_ok, 'ESP_LINK': bool(esp.view.link_ok) if esp.running else False,
               'UI_POWER': b.ui_volts > 2.0, 'LCD_BL': b.front.lcd.backlight,
               'STBY_LED': self.led_on()}
        for n in self.orders:
            r = self.checker.signals[('stm32', n)]
            port, pin = ord(r.pin[1]) - ord('A'), int(r.pin[2:])
            mode = fw.io.mode[port][pin] if fw.running else 0
            if mode == 2:
                out[f'PB_{n}'] = bool(fw.io.odr[port][pin])
            elif mode == 3:
                out[f'PB_{n}'] = fw.io.pwm[port][pin] >= 500
            else:
                out[f'PB_{n}'] = None
        ls = b.loads_state
        out.update({'HEATER': ls.get('heater'), 'PUMP': ls.get('pump'), 'GRINDER': ls.get('grinder'),
                    'MAINS': ls.get('mains'), 'VALVE': (ls.get('valve_v') or 0) > 12,
                    'BREW_FWD': (ls.get('motor_v') or 0) > 6, 'BREW_REV': (ls.get('motor_v') or 0) < -6})
        for k in KEYS:
            out[k] = k in b.front.pressed
        out['CORE_STATE'] = firmware.STATES.index(fw.controller[0]) if fw.running else None
        out['ESP_PAGE'] = esp.view.ui.page if esp.running else None
        rep = esp.view.report if esp.running and esp.view.have_report else None
        out['TEST_ID'] = rep.id if rep else None
        out['TEST_PHASE'] = rep.phase if rep else None
        return out

    def order_levels(self):
        """Level each STM32 order pin asks for: True active, False inactive, None released."""
        fw, out = self.board.fw, {}
        for n in self._orders_names:
            r = self.checker.signals[('stm32', n)]
            port, pin = ord(r.pin[1]) - ord('A'), int(r.pin[2:])
            mode = fw.io.mode[port][pin] if fw.running else 0
            if mode == 2:
                high = bool(fw.io.odr[port][pin])
            elif mode == 3:
                high = fw.io.pwm[port][pin] >= 500
            else:
                out[n] = None
                continue
            out[n] = high == (r.spec.get('active', 'high') == 'high')
        return out



    def _analog(self):
        b = self.board
        v = b.esp.view if b.esp.running else None
        s = v.status if v is not None and v.have_status else None
        return {'t': round(b.t, 3), 'boiler_c': round(self.plant.boiler_c, 2),
                'ntc_code': b.adc_code('NTC') if b.fw.running else None,
                'rail_12v': s.rail_12v_mv / 1000 if s else None,
                'rail_24v': s.rail_24v_mv / 1000 if s else None,
                'brew_ma': s.brew_ma if s else None,
                'motor_a': round(self.plant.motor_amps, 3), 'ui_v': round(b.ui_volts, 2),
                'grinder_a': round(self.plant.grinder_mean_amps, 3),
                'grinder_stm_a': s.grinder_ma / 1000 if s else None}

    def led_on(self):
        net = self.board.tca_pins[7]
        run = self.board.out.lo if self.board.out else None
        v = run.volts.get(net) if run else None
        return v is not None and self.board.ui_volts > 2 and v < 0.3 * self.board.ui_volts

    # -- views ------------------------------------------------------------------
    def state(self):
        with self.lock:
            b, fw, esp, p = self.board, self.board.fw, self.board.esp, self.plant
            st, outs = fw.controller if fw.running else ('RESET', {})
            v = esp.view if esp.running else None
            s = v.status if v is not None and v.have_status else None
            lcd = b.front.lcd
            return {
                't': round(b.t, 3), 'speed': self.speed, 'paused': self.paused,
                'stm': {'running': fw.running, 'state': st, 'link': fw.link_ok, 'outputs': outs,
                        'hung': fw.hung},
                'esp': {'running': esp.running, 'hung': esp.hung,
                        'page': firmware.PAGES[v.ui.page] if v else None,
                        'title': v.display.want.title_text if v else '',
                        'lines': v.display.want.lines() if v else [],
                        'front': firmware.FRONT[v.front] if v else None,
                        'link': bool(v.link_ok) if v else False, 'standby': bool(v.ui.standby) if v else False,
                        'keypad_valid': bool(v.keypad.valid) if v else False,
                        'requests': v.requests if v else 0, 'replies': v.replies if v else 0,
                        'recoveries': v.recoveries if v else 0,
                        'last_reply': ({'type': v.last_reply_type, 'for': v.last_reply_for,
                                        'code': v.last_reply_code} if v and v.replies else None)},
                'test': ({'id': firmware.TESTS[v.report.id] if v.report.id < len(firmware.TESTS) else v.report.id,
                          'phase': firmware.TEST_PHASES[v.report.phase], 'step': v.report.step,
                          'reason': v.report.reason,
                          'reason_name': firmware.REASONS[v.report.reason] if v.report.reason < len(firmware.REASONS) else '', 'elapsed_ms': v.report.elapsed_ms,
                          'values': list(v.report.value)} if v and v.have_report else None),
                'orders': self.order_levels(),
                'status': ({'state': s.state, 'boiler_dc': s.boiler_dc, 'grinder_ma': s.grinder_ma, 'rail_12v_mv': s.rail_12v_mv, 'rail_24v_mv': s.rail_24v_mv, 'brew_ma': s.brew_ma,
                            'ntc_raw': s.ntc_raw, 'inputs': s.inputs, 'outputs': s.outputs,
                            'uptime_ms': s.uptime_ms} if s else None),
                'board': {'nrst': b.nrst_high, 'ui_volts': round(b.ui_volts, 2),
                          'corner': {None: 'nom', 0: 'min', 1: 'max'}[b.corner],
                          'loads': {k: (round(x, 2) if isinstance(x, float) else x)
                                    for k, x in b.loads_state.items()},
                          'led': self.led_on(), 'backlight': lcd.backlight, 'lcd_on': lcd.visible,
                          'lcd_pixels': lcd.pixels_written, 'uart_dropped': b.uart_dropped},
                'plant': {'boiler_c': round(p.boiler_c, 2), 'flow_ml': round(p.flow_ml, 1),
                          'unit_pos': round(p.unit_pos, 3), 'motor_a': round(p.motor_amps, 3),
                          'door_closed': p.door_closed, 'unit_present': p.unit_present,
                          'ntc_open': p.ntc_open, 'water_volts': p.water_volts,
                          'tank_ml': round(p.tank_ml), 'tank_capacity_ml': p.tank_capacity_ml,
                          'beans_g': round(p.beans_g, 1), 'ground_g': round(p.ground_g, 1),
                          'chamber_g': round(p.chamber_g, 1), 'grinder_a': round(p.grinder_mean_amps, 3),
                          'grinder_jammed': p.grinder_jammed, 'chute_blocked': p.chute_blocked,
                          'heater_on': p.heater_on, 'pump_on': p.pump_on, 'valve_on': p.valve_on,
                          'grinder_on': p.grinder_on, 'pump_ml_s': p.pump_ml_s},
                'faults': {'brew_fault': 'controller:U501' in b.faults, 'keypad_hang': b.front.tca.hung,
                           'uart_noise': b.uart_noise},
                'pressed': sorted(b.front.pressed),
                'events': [{'t': e.t, 'kind': e.kind, 'detail': e.detail} for e in b.events[-40:]],
                'vcd_changes': len(self.vcd.changes),
            }

    def frame(self):
        with self.lock:
            lcd = self.board.front.lcd
            return bytes(lcd.frame), lcd.visible, lcd.pixels_written

    def history_json(self):
        with self.lock:
            return list(self.history)

    # -- commands -----------------------------------------------------------------
    def command(self, c):
        """Apply one command dict; returns an error string or None."""
        with self.lock:
            b, p, name = self.board, self.plant, c.get('cmd')
            if name == 'press':
                if c.get('sw') not in KEYS:
                    return 'unknown key'
                b.press(c['sw'], bool(c.get('down', True)))
            elif name == 'door':
                p.door_closed = bool(c.get('closed'))
            elif name == 'unit_present':
                p.unit_present = bool(c.get('value'))
            elif name == 'ntc_open':
                p.ntc_open = bool(c.get('value'))
            elif name == 'water_volts':
                p.water_volts = None if c.get('value') is None else float(c['value'])
            elif name == 'tank':
                p.tank_ml = max(0.0, min(p.tank_capacity_ml, float(c.get('value', p.tank_capacity_ml))))
            elif name == 'beans':
                p.beans_g = max(0.0, float(c.get('value', 200)))
            elif name == 'grinder_jam':
                p.grinder_jammed = bool(c.get('value'))
            elif name == 'chute_blocked':
                p.chute_blocked = bool(c.get('value'))
            elif name == 'stm_hang':
                b.fw.hung = bool(c.get('value'))
            elif name == 'esp_hang':
                b.esp.hung = bool(c.get('value'))
            elif name == 'keypad_hang':
                b.front.tca.hung = bool(c.get('value'))
            elif name == 'brew_fault':
                (b.faults.add if c.get('value') else b.faults.discard)('controller:U501')
            elif name == 'uart_noise':
                b.uart_noise = max(0.0, min(1.0, float(c.get('value', 0))))
            elif name == 'corner':
                b.set_corner({'min': 0, 'max': 1, 'nom': None}[c.get('value', 'nom')])
            elif name == 'speed':
                self.speed = max(0.05, min(50.0, float(c.get('value', 1))))
            elif name == 'pause':
                self.paused = bool(c.get('value'))
            elif name == 'step':
                self.advance(max(1, min(10000, int(c.get('ms', 1)))))
            elif name == 'reboot':
                self._build()
            elif name == 'clear_vcd':
                self.vcd.changes.clear()
                self.vcd.last.clear()
            else:
                return f'unknown command {name!r}'
            return None


def handler(session):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code, body, ctype='application/json', extra=()):
            data = body if isinstance(body, bytes) else body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            for k, v in extra:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split('?')[0]
            if path in ('/', '/index.html'):
                self._send(200, PAGE.read_bytes(), 'text/html; charset=utf-8')
            elif path == '/api/state':
                self._send(200, json.dumps(session.state()))
            elif path == '/api/history':
                self._send(200, json.dumps(session.history_json()))
            elif path == '/api/frame':
                data, visible, n = session.frame()
                self._send(200, data, 'application/octet-stream',
                           [('X-Visible', '1' if visible else '0'), ('X-Pixels', str(n))])
            elif path == '/api/vcd':
                with session.lock:
                    text = session.vcd.text()
                self._send(200, text, 'text/plain; charset=utf-8',
                           [('Content-Disposition', 'attachment; filename="open-saeco.vcd"')])
            else:
                self._send(404, json.dumps({'error': 'not found'}))

        def do_POST(self):
            if self.path != '/api/cmd':
                self._send(404, json.dumps({'error': 'not found'}))
                return
            n = int(self.headers.get('Content-Length', 0))
            try:
                cmd = json.loads(self.rfile.read(n) or b'{}')
                err = session.command(cmd)
            except (ValueError, TypeError, KeyError) as e:
                err = str(e)
            self._send(400 if err else 200, json.dumps({'error': err} if err else {'ok': True}))
    return Handler


def serve(port=8765, speed=1.0, corner=None):
    session = Session(speed=speed, corner=corner)
    server = ThreadingHTTPServer(('127.0.0.1', port), handler(session))
    session.start()
    return server, session


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Local web panel of the virtual machine (F3).')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--speed', type=float, default=1.0, help='simulated seconds per real second')
    ap.add_argument('--corner', choices=('min', 'nom', 'max'), default='nom')
    a = ap.parse_args(argv)
    server, session = serve(a.port, a.speed, {'min': 0, 'max': 1, 'nom': None}[a.corner])
    print(f'Panel en http://127.0.0.1:{server.server_address[1]}/ (Ctrl+C para salir)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        session.stop()
        server.server_close()
