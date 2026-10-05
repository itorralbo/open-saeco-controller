"""F2: the ESP32 interface core and the STM32 talking over protocol v0.

Both firmwares run on the virtual board (sim/osc_sim/board.py). The front
panel answers from the far end of the harness: keys close real switches in
the netlist, the TCA9534 reads them as voltages and the ST7789 paints a
framebuffer. Run: python -m unittest discover -s tests/sim
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
GREEN, RED, GREY, AMBER = 0x07E0, 0xF800, 0x7BEF, 0xFD20


def machine(corner=0, plant=None):
    return VirtualBoard(CHECKER, firmware.Firmware(), plant or Plant(), corner=corner,
                        esp=firmware.EspFirmware())


def up(b, seconds=1.0):
    ok = b.run(seconds, until=lambda x: x.esp.view.link_ok and x.fw.controller[0] == 'SAFE_IDLE'
               and x.front.lcd.visible)
    return ok


def screen(b):
    return firmware.SCREENS[b.esp.view.screen]


def tap(b, sw, hold=0.06, after=0.06):
    b.press(sw)
    b.run(hold)
    b.press(sw, False)
    b.run(after)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Link(unittest.TestCase):
    def test_both_boot_and_the_core_reaches_safe_idle(self):
        for corner in (0, 1):
            b = machine(corner)
            self.assertTrue(up(b), b.events)
            self.assertEqual(screen(b), 'IDLE')
            lcd = b.front.lcd
            self.assertEqual((lcd.pixel(160, 120), lcd.colmod, lcd.madctl), (GREEN, 0x55, 0x60))
            self.assertEqual(b.kinds('backfeed') + b.kinds('undefined'), [])
            self.assertEqual((b.uart_dropped, b.esp.io.undefined_reads, b.esp.io.bad_calls), (0, 0, 0))
            self.assertEqual(b.front.tca.undefined, 0)

    def test_status_carries_the_board(self):
        b = machine(1)
        up(b)
        b.run(0.3)
        s = b.esp.view.status
        self.assertAlmostEqual(s.rail_12v_mv / 1000, b.rails[b.s.find('controller:12V_PROTECTED')], delta=0.1)
        self.assertAlmostEqual(s.rail_24v_mv / 1000, b.rails[b.s.find('controller:24V_ACT_RAW')], delta=0.2)
        self.assertTrue(s.inputs & 0x01 and s.inputs & 0x10)  # door closed, front panel on

    def test_esp32_hang_faults_the_core(self):
        b = machine()
        up(b)
        b.esp.hung = True  # stops polling: no keepalive
        b.run(0.5)
        self.assertEqual(b.fw.controller[0], 'FAULT')
        self.assertFalse(any(b.fw.controller[1].values()))

    def test_stm32_hang_shows_link_lost_then_recovers_after_the_watchdog(self):
        b = machine()
        up(b)
        b.fw.hung = True
        b.run(0.4)
        self.assertEqual(screen(b), 'LINK_LOST')
        self.assertEqual(b.front.lcd.pixel(160, 120), GREY)
        # U601 resets the hung core; the reset clears the hang.
        self.assertTrue(b.run(3.0, until=lambda x: bool(x.kinds('watchdog'))))
        self.assertTrue(up(b, 2.0), b.events)
        self.assertEqual(len(b.kinds('boot')), 2)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Keys(unittest.TestCase):
    def test_start_is_refused_and_shown_as_a_normal_answer(self):
        b = machine()
        up(b)
        tap(b, 'SW1')
        v = b.esp.view
        self.assertEqual((v.last_reply_type, v.last_reply_for, v.last_reply_code), (0x7F, 0x22, 3))
        self.assertEqual(screen(b), 'IDLE')
        self.assertEqual(b.front.lcd.pixel(160, 5), AMBER)
        self.assertFalse(any(b.fw.controller[1].values()))

    def test_key_held_through_boot_is_ignored_until_released(self):
        b = machine()
        b.press('SW1')
        up(b)
        b.run(0.3)
        self.assertEqual(b.esp.view.last_reply_for, 0x01)  # only the HELLO was answered
        self.assertFalse(b.esp.view.keypad.armed)
        b.press('SW1', False)
        b.run(0.1)
        tap(b, 'SW1')
        self.assertEqual(b.esp.view.last_reply_for, 0x22)

    def test_bounces_shorter_than_the_debounce_do_not_count(self):
        b = machine()
        up(b)
        before = b.esp.view.requests
        for _ in range(5):
            tap(b, 'SW1', hold=0.008, after=0.008)
        b.run(0.1)
        self.assertEqual(b.esp.view.requests, before)

    def test_open_door_faults_and_clear_fault_needs_it_closed(self):
        plant = Plant()
        b = machine(plant=plant)
        up(b)
        plant.door_closed = False
        b.run(0.2)
        self.assertEqual((b.fw.controller[0], screen(b)), ('FAULT', 'FAULT'))
        self.assertEqual(b.front.lcd.pixel(160, 120), RED)
        tap(b, 'SW2')
        self.assertEqual(b.fw.controller[0], 'FAULT')  # refused with the door open
        plant.door_closed = True
        b.run(0.1)
        tap(b, 'SW2')
        self.assertEqual((b.fw.controller[0], screen(b)), ('SAFE_IDLE', 'IDLE'))

    def test_standby_key_turns_the_backlight_off_and_the_led_on(self):
        b = machine()
        up(b)
        tap(b, 'SW4')
        b.run(0.05)
        self.assertFalse(b.front.lcd.visible)
        led = b.out.lo.volts[b.tca_pins[7]]
        self.assertLess(led, 0.5)  # P7 low: the standby LED conducts
        tap(b, 'SW4')
        b.run(0.05)
        self.assertTrue(b.front.lcd.visible)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class FrontSupply(unittest.TestCase):
    def test_a_hung_keypad_gets_its_supply_cycled_without_backfeed(self):
        b = machine()
        up(b)
        b.front.tca.hung = True
        self.assertTrue(b.run(2.0, until=lambda x: x.ui_volts < 0.5), 'UI supply never switched off')
        b.run(0.05)
        self.assertEqual(b.kinds('backfeed'), [])
        modes = {g: b.esp.pin_mode(g) for g in b.esp_front}
        self.assertTrue(all(m in ('off', 'input') for m in modes.values()), modes)
        self.assertTrue(b.run(1.5, until=lambda x: x.esp.view.keypad.valid and x.front.lcd.visible))
        self.assertEqual(b.esp.view.recoveries, 1)
        self.assertEqual(b.kinds('backfeed'), [])

    def test_backfeed_detector_sees_a_pin_left_high(self):
        b = machine()
        up(b)
        b.front.tca.hung = True
        b.run(2.0, until=lambda x: x.ui_volts < 0.5)
        cs = int(CHECKER.signals[('esp32', 'LCD_CS_N')].pin[4:])
        b.esp.hung = True  # freeze the core and force a stray high
        b.esp.io.mode[cs], b.esp.io.level[cs] = 2, 1
        b.step()
        b.step()
        self.assertTrue(b.kinds('backfeed'))


if __name__ == '__main__':
    unittest.main()
