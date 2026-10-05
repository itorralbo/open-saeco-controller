"""F3: the local web panel and the VCD of the virtual machine.

The session runs both firmwares; the HTTP API is exercised on an ephemeral
port. Run: python -m unittest discover -s tests/sim
"""
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sim'))

from osc_sim import firmware  # noqa: E402
from osc_sim.vcd import Recorder  # noqa: E402

HAVE_CC = firmware.compiler() is not None


class Vcd(unittest.TestCase):
    def test_only_changes_are_written(self):
        r = Recorder(['A', 'BUS'], widths={'BUS': 3})
        for t, a, bus in ((0, False, 0), (1, False, 0), (2, True, 5), (3, None, 5)):
            r.sample(t, {'A': a, 'BUS': bus})
        text = r.text()
        self.assertIn('$timescale 1us $end', text)
        self.assertIn('$var reg 3', text)
        body = text.split('$enddefinitions $end\n')[1].split('\n')
        self.assertEqual(body[:3], ['#0', '0!', 'b0 "'])
        self.assertIn('#2', body)
        self.assertIn('b101 "', body)
        self.assertIn('x!', body)
        self.assertNotIn('#1', body)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Panel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from osc_sim.panel import Session, ThreadingHTTPServer, handler
        cls.session = Session(speed=1.0)
        cls.session.paused = True  # the test advances time itself
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler(cls.session))
        cls.url = f'http://127.0.0.1:{cls.server.server_address[1]}'
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.url + path, timeout=10) as r:
            return r.read(), dict(r.headers)

    def cmd(self, **c):
        req = urllib.request.Request(self.url + '/api/cmd', json.dumps(c).encode(),
                                     {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def state(self):
        return json.loads(self.get('/api/state')[0])

    def test_a_page_and_boot(self):
        page, headers = self.get('/')
        self.assertIn(b'<canvas id="lcd"', page)
        self.cmd(cmd='step', ms=1000)
        s = self.state()
        self.assertEqual((s['stm']['state'], s['esp']['page'], s['board']['lcd_on']), ('SAFE_IDLE', 'HOME', True))
        frame, headers = self.get('/api/frame')
        self.assertEqual(len(frame), 320 * 240 * 2)
        self.assertEqual(frame[2 * (2 * 320 + 160):][:2], b'\x07\xe0')  # green title bar, big endian RGB565

    def test_b_key_and_fault_injection(self):
        self.cmd(cmd='press', sw='SW5', down=True)
        self.cmd(cmd='step', ms=60)
        self.cmd(cmd='press', sw='SW5', down=False)
        self.cmd(cmd='step', ms=60)
        self.assertEqual(self.state()['esp']['last_reply'], {'type': 0x7F, 'for': 0x22, 'code': 3})
        self.cmd(cmd='door', closed=False)
        self.cmd(cmd='step', ms=200)
        s = self.state()
        self.assertEqual((s['stm']['state'], s['esp']['page']), ('FAULT', 'HOME'))
        self.cmd(cmd='door', closed=True)
        self.cmd(cmd='press', sw='SW5', down=True)
        self.cmd(cmd='step', ms=60)
        self.cmd(cmd='press', sw='SW5', down=False)
        self.cmd(cmd='step', ms=100)
        self.assertEqual(self.state()['stm']['state'], 'SAFE_IDLE')

    def test_c_uart_noise_drops_the_link_and_nothing_resumes_alone(self):
        self.cmd(cmd='uart_noise', value=0.05)  # 5 % of bytes with a flipped bit
        self.cmd(cmd='step', ms=2000)
        self.cmd(cmd='uart_noise', value=0)
        self.cmd(cmd='step', ms=500)
        s = self.state()
        self.assertTrue(s['stm']['link'] and s['esp']['link'], s)
        if s['stm']['state'] == 'FAULT':  # the link dropped: CLEAR_FAULT is needed
            self.cmd(cmd='press', sw='SW5', down=True)
            self.cmd(cmd='step', ms=60)
            self.cmd(cmd='press', sw='SW5', down=False)
            self.cmd(cmd='step', ms=100)
        self.assertEqual((self.state()['stm']['state'], self.state()['esp']['page']), ('SAFE_IDLE', 'HOME'))

    def test_d_vcd_and_history(self):
        text = self.get('/api/vcd')[0].decode()
        self.assertIn('$var wire 1', text)
        self.assertIn('PB_WDT_KICK', text)
        self.assertGreater(text.count('\n#'), 10)
        hist = json.loads(self.get('/api/history')[0])
        self.assertTrue(hist and {'t', 'boiler_c', 'rail_12v'} <= set(hist[-1]))

    def test_e_bad_command_is_refused(self):
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.cmd(cmd='launch_missiles')
        self.assertEqual(e.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
