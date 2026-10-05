"""F1: the STM32 firmware on the virtual board.

The firmware is the real firmware/stm32 code built for the host
(sim/osc_sim/firmware.py); the board, U601 and the plant come from the
netlists (sim/osc_sim/board.py). U601 runs at the end of each timing range
that makes the test harder: 0.9 s watchdog time-out, 300 ms reset delay.
Needs a C compiler ($CC, $SDKROOT on macOS). Run: python -m unittest discover -s tests/sim
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sim'))

from osc_sim import firmware  # noqa: E402
from osc_sim.board import VirtualBoard  # noqa: E402
from osc_sim.checks import Checker  # noqa: E402
from osc_sim.model import System, load_contract  # noqa: E402
from osc_sim.plant import Plant  # noqa: E402

CHECKER = Checker(System(load_contract(ROOT), ROOT))
CHECKER.run()
HAVE_CC = firmware.compiler() is not None


def board(corner=0, plant=None, **kw):
    return VirtualBoard(CHECKER, firmware.Firmware(), plant or Plant(), corner=corner, **kw)


def kicker(period=0.1):
    """WDI toggles every 'period' s, as osc_app_poll() does, for forced runs."""
    state = {'next': 0.0, 'level': False}

    def each(b):
        if b.t >= state['next']:
            state['next'] = b.t + period
            state['level'] = not state['level']
            b.force('WDT_KICK', state['level'])
    return each


def booted(b):
    b.run(1.0, until=lambda x: x.fw.running)
    return b


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Boot(unittest.TestCase):
    def test_power_up_holds_reset_then_boots(self):
        for corner in (0, 1):
            b = board(corner)
            b.run(0.29)
            self.assertFalse(b.fw.running)
            self.assertFalse(any(v for k, v in b.loads_state.items() if k in ('heater', 'pump', 'grinder', 'mains')))
            b.run(0.02)
            self.assertTrue(b.fw.running, b.events)
            self.assertEqual([e.kind for e in b.events], ['boot'])

    def test_firmware_keeps_the_watchdog_quiet(self):
        b = board(0)
        b.run(5.0)
        self.assertEqual(b.kinds('watchdog'), [])
        self.assertEqual(len(b.kinds('boot')), 1)
        self.assertEqual(b.kinds('undefined'), [])
        self.assertEqual((b.fw.io.undefined_reads, b.fw.io.analog_reads, b.fw.io.bad_calls), (0, 0, 0))

    def test_without_link_the_core_waits_then_faults_with_loads_off(self):
        b = booted(board(1))
        b.run(0.5)
        state, outs = b.fw.controller
        self.assertEqual(state, 'BOOT')  # waiting for the ESP32 (OSC_LINK_BOOT_GRACE_MS)
        b.run(1.6)
        state, outs = b.fw.controller
        self.assertEqual(state, 'FAULT')
        self.assertFalse(any(outs.values()))
        self.assertTrue(b.loads_state['ui'])
        self.assertTrue(b.pin_level('DOOR_CLOSED_N') is False)  # closed door pulls the line low


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Watchdog(unittest.TestCase):
    def test_hung_core_is_reset_within_the_longest_time_out(self):
        b = booted(board(0, watchdog='max', delay='min'))
        b.run(1.0)
        b.fw.hung = True
        hung_at = b.t
        b.run(3.0, until=lambda x: bool(x.kinds('watchdog')))
        self.assertTrue(b.kinds('watchdog'))
        self.assertLessEqual(b.t - hung_at, 2.5 + 0.21)  # time-out after the last edge
        b.fw.hung = False
        b.run(0.2, until=lambda x: len(x.kinds('boot')) == 2)
        self.assertEqual(len(b.kinds('boot')), 2)

    def test_hung_core_recovers_whatever_pb4_was(self):
        # TPS3828 latches RESET if WDI pulses during reset; U606 keeps it high.
        for level in (True, False):
            b = booted(board(0))
            b.run(0.3)
            b.fw.hung = True
            b.force('WDT_KICK', level)
            self.assertTrue(b.run(1.5, until=lambda x: bool(x.kinds('watchdog'))))
            self.assertTrue(b.run(0.5, until=lambda x: len(x.kinds('boot')) == 2), b.events)
            self.assertEqual(b.kinds('reset-latched'), [])

    def test_runaway_orders_are_cut_by_the_interlock(self):
        b = booted(board(0))
        b.fw.hung = True
        for name in ('MAINS_ARM', 'HEATER_EN', 'PUMP_EN', 'VALVE_EN'):
            b.force(name, True)
        b.run(0.05)
        self.assertTrue(b.loads_state['heater'] and b.loads_state['pump'])
        self.assertGreater(b.loads_state['valve_v'], 20.0)  # coil energised
        b.run(1.0, until=lambda x: x.sup.asserting(x.t))
        # The step that asserts RESET already sees every load off.
        b.run(0.001)
        self.assertFalse(b.loads_state['heater'] or b.loads_state['pump'] or b.loads_state['mains'])
        self.assertLess(b.loads_state['valve_v'], 1.0)

    def test_dead_battery_pull_down_makes_nfault_undefined(self):
        b = booted(board(0))
        b.run(0.1)
        self.assertEqual(b.fw.io.undefined_reads, 0)
        b.fw.io.dead_battery = 1  # as if bsp_init() skipped the UCPD disable
        b.run(0.1)
        self.assertGreater(b.fw.io.undefined_reads, 0)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Loads(unittest.TestCase):
    def test_heater_warms_the_boiler_and_the_ntc_code_falls(self):
        b = booted(board(0, Plant(boiler_c=60.0)))
        b.fw.hung = True
        b.run(0.02, each=kicker())
        cold = b.adc_code('NTC')
        b.force('MAINS_ARM', True)
        b.force('HEATER_EN', True)
        b.run(4.0, each=kicker())
        self.assertEqual(b.kinds('watchdog'), [])
        self.assertTrue(b.loads_state['heater'])
        self.assertGreater(b.plant.boiler_c, 70.0)
        self.assertLess(b.adc_code('NTC'), cold - 200)

    def test_brew_unit_reaches_work_and_ipropi_reads_the_current(self):
        b = booted(board(0))
        b.fw.hung = True
        for name in ('BREW_SLEEP_N', 'BREW_PWM', 'BREW_DIR'):
            b.force(name, True)
        b.run(0.5, each=kicker())
        amps = b.plant.motor_amps
        self.assertGreater(amps, 0.15)
        volts = b.adc_code('BREW_CURRENT') / 4095 * b.vdd
        self.assertAlmostEqual(volts / amps, 2.4, delta=0.05)  # R510 = 2.4k, 1000 uA/A
        self.assertTrue(b.run(6.0, each=kicker(), until=lambda x: x.pin_level('BU_WORK_N') is False))
        self.assertGreaterEqual(b.plant.unit_pos, 0.95)

    def test_flow_meter_edges_reach_the_timer(self):
        b = booted(board(1))
        b.run(0.05)
        b.fw.hung = True
        b.force('MAINS_ARM', True)
        b.force('PUMP_EN', True)
        b.run(2.0, each=kicker())
        port, pin = b.flow_key
        edges = b.fw.io.edges[port][pin]
        expected = b.plant.flow_ml / 1000 * b.plant.flow_pulses_per_l
        self.assertGreater(edges, 10)
        self.assertLessEqual(abs(edges - expected), 1.5)


if __name__ == '__main__':
    unittest.main()
