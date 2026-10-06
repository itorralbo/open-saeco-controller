"""F4: set-up tests driven from the menus of the interface.

Each test is chosen on the front panel (MENU > Puesta a punto), confirmed,
run by the STM32 (firmware/stm32/src/service.c) against the plant and
reported back to the screen. The loads checked here are the ones the
netlist energises, not the orders of the firmware.
Run: python -m unittest discover -s tests/sim
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sim'))
sys.path.insert(0, str(ROOT / 'tests' / 'sim'))

from osc_sim import firmware  # noqa: E402
from osc_sim.plant import Plant  # noqa: E402
from test_f2 import HAVE_CC, lines, machine, tap, up  # noqa: E402

UP, DOWN, BACK, OK, MENU, STOP = 'SW1', 'SW2', 'SW3', 'SW5', 'SW6', 'SW7'
INPUTS, BREW_UNIT, VALVE, RELAY, PUMP, HEATER, GRINDER, DOSE = range(1, 9)
DONE, ABORTED, REFUSED = 2, 3, 4
R_OK, R_DOOR, R_STOP, R_LINK, R_NO_FLOW = 0, 1, 5, 6, 10
R_NO_BEANS, R_JAM, R_NO_DOSE = 13, 14, 15
QUIET = {'boot', 'esp-boot'}
SERVICE = 3  # OSC_CORE_SERVICE in STATUS


def page(b):
    return firmware.PAGES[b.esp.view.ui.page]


def report(b):
    return b.esp.view.report


def booted(plant=None):
    b = machine(plant=plant)
    assert up(b, 2.0), b.events
    return b


def choose(b, test):
    """MENU > Puesta a punto > test, leaving the confirmation page shown."""
    tap(b, MENU)
    tap(b, DOWN)
    tap(b, OK)
    for _ in range(test - 1):
        tap(b, DOWN)
    tap(b, OK)


def start(b, test):
    choose(b, test)
    tap(b, OK)


def finished(b, test, seconds):
    return b.run(seconds, until=lambda x: x.esp.view.have_report and report(x).id == test
                 and report(x).phase in (DONE, ABORTED, REFUSED))


def loads_off(b):
    s = b.loads_state
    return not any(s[k] is True for k in ('heater', 'pump', 'grinder', 'mains')) \
        and abs(s['valve_v']) < 1.0 and abs(s['motor_v']) < 1.0


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Menus(unittest.TestCase):
    def test_the_set_up_list_and_its_confirmation(self):
        b = booted()
        tap(b, MENU)
        self.assertEqual(page(b), 'MENU')
        tap(b, DOWN)
        tap(b, OK)
        self.assertEqual(page(b), 'SETUP')
        shown = ' '.join(lines(b)).lower()
        for word in ('entradas', 'grupo', 'valvula', 'rele', 'bomba', 'calentador', 'molinillo', 'dosis'):
            self.assertIn(word, shown)
        for _ in range(PUMP - 1):
            tap(b, DOWN)
        tap(b, OK)
        self.assertEqual((page(b), b.esp.view.ui.test, b.esp.view.ui.param), ('CONFIRM', PUMP, 100))
        tap(b, UP)
        self.assertGreater(b.esp.view.ui.param, 100)
        tap(b, BACK)
        tap(b, BACK)
        tap(b, BACK)
        self.assertEqual(page(b), 'HOME')
        self.assertTrue(loads_off(b))
        self.assertEqual(b.fw.controller[0], 'SAFE_IDLE')


class Texts(unittest.TestCase):
    def test_every_reason_fits_after_motivo(self):
        import re
        ui = (ROOT / 'firmware/esp32/core/ui.c').read_text(encoding='utf-8')
        block = ui[ui.index('reasons[] = {'):]
        block = block[:block.index('};')]
        names = re.findall(r'"([^"]*)"', block)
        self.assertEqual(len(names), 16)
        for name in names:
            self.assertLessEqual(len('Motivo: ' + name), 26, name)


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Tests(unittest.TestCase):
    def test_inputs_reads_every_sensor_without_a_load(self):
        p = Plant()
        b = booted(p)
        start(b, INPUTS)
        self.assertTrue(b.run(1.0, until=lambda x: x.esp.view.have_report and report(x).id == INPUTS))
        self.assertTrue(loads_off(b))
        self.assertTrue(finished(b, INPUTS, 4.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (DONE, R_OK))
        door, unit, work, water, boiler, rail = r.value
        self.assertEqual((door, unit, work), (1, 1, 0))
        self.assertGreater(water, 1500)              # tank full: ~2 V on JP22
        self.assertLess(abs(boiler - 200), 15)       # 20 degC, 0.1 degC units
        self.assertLess(abs(rail - 1000 * b.rails['controller:24V_ACT_RAW']), 300)  # x21 divider, VDDA via VREFINT
        self.assertEqual(b.fw.controller[0], 'SAFE_IDLE')  # no load test: no SERVICE state
        self.assertEqual({e.kind for e in b.events} - QUIET, set())

    def test_brew_unit_goes_to_work_and_back(self):
        p = Plant()
        b = booted(p)
        start(b, BREW_UNIT)
        self.assertTrue(b.run(1.0, until=lambda x: x.esp.view.status.state == SERVICE))
        self.assertTrue(b.run(5.0, until=lambda x: p.unit_pos >= 0.95))
        self.assertTrue(finished(b, BREW_UNIT, 10.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (DONE, R_OK), r)
        to_work, i0, peak, stop, back, faults = r.value
        self.assertTrue(2000 < to_work < 6000, to_work)  # ASSUMED travel, slowest at the min corner
        self.assertTrue(100 <= i0 <= 300, i0)        # docs/verification.md: I0 100-300 mA
        self.assertGreaterEqual(peak, i0)
        self.assertEqual(faults, 0)
        self.assertLess(p.unit_pos, 0.1)
        b.run(0.2)
        self.assertTrue(loads_off(b))
        self.assertEqual(b.fw.controller[0], 'SAFE_IDLE')

    def test_valve_relay_and_grinder_energise_only_their_load(self):
        for test, load, seconds in ((VALVE, 'valve', 2.0), (RELAY, 'mains', 1.0), (GRINDER, 'grinder', 3.0)):
            with self.subTest(load=load):
                p = Plant()
                b = booted(p)
                seen = set()

                def watch(x):
                    s = x.loads_state
                    for k in ('heater', 'pump', 'grinder', 'mains'):
                        if s[k] is True:
                            seen.add(k)
                    if abs(s['valve_v']) > 12.0:
                        seen.add('valve')
                    if abs(s['motor_v']) > 1.0:
                        seen.add('motor')
                start(b, test)
                self.assertTrue(b.run(seconds + 3.0, each=watch,
                                      until=lambda x: x.esp.view.have_report and report(x).id == test
                                      and report(x).phase == DONE), report(b))
                # The mains relay arms the triac loads and stays off for the valve.
                want = {load} | ({'mains'} if load == 'grinder' else set())
                self.assertEqual(seen, want)
                on_ms = report(b).value[0 if load == 'grinder' else 2]
                self.assertTrue(abs(on_ms - seconds * 1000) < 150, report(b))
                if load == 'grinder':
                    self.assertAlmostEqual(p.ground_g, 1.2 * 3.0, delta=0.3)
                b.run(0.2)
                self.assertTrue(loads_off(b))

    def test_pump_measures_flow_and_calibrates_the_meter(self):
        p = Plant()
        b = booted(p)
        start(b, PUMP)
        self.assertTrue(finished(b, PUMP, 30.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (DONE, R_OK), r)
        on_ms, pulses, ml10 = r.value[:3]
        self.assertAlmostEqual(p.flow_ml, 100.0, delta=2.0)
        self.assertAlmostEqual(pulses, 192, delta=3)
        self.assertAlmostEqual(ml10, 1000, delta=20)
        self.assertAlmostEqual(on_ms, 20000, delta=500)  # 5 ml/s, ASSUMED in the plant
        b.run(0.3)
        tap(b, OK)
        self.assertEqual(page(b), 'ENTRY')
        self.assertEqual(b.esp.view.ui.entry_ml, 100)
        for _ in range(4):
            tap(b, DOWN)                             # the scale read 96 ml
        tap(b, OK)
        self.assertEqual(b.esp.view.ui.flow_ppl, pulses * 1000 // 96)
        self.assertTrue(loads_off(b))

    def test_pump_without_water_stops_for_no_flow(self):
        p = Plant(tank_ml=0.0)
        b = booted(p)
        start(b, PUMP)
        self.assertTrue(finished(b, PUMP, 5.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (ABORTED, R_NO_FLOW), r)
        self.assertLess(r.elapsed_ms, 3500)
        b.run(0.2)
        self.assertTrue(loads_off(b))

    def test_heater_reaches_the_target_and_reports_the_overshoot(self):
        p = Plant()
        b = booted(p)
        start(b, HEATER)
        self.assertTrue(finished(b, HEATER, 70.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (DONE, R_OK), r)
        t0, t_end, heat_ms, rate, peak, overshoot = r.value
        self.assertLess(abs(t0 - 200), 15)
        self.assertGreaterEqual(t_end, 900)
        self.assertTrue(2.0 < rate / 100 < 8.0, rate)
        self.assertEqual(overshoot, peak - 900)
        self.assertLess(p.boiler_c, 120)
        self.assertTrue(loads_off(b))


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class GrinderCurrent(unittest.TestCase):
    """U704 on JP8's + line: empty hopper, jammed burrs and the dose check."""

    def test_the_grinder_test_reads_its_current(self):
        p = Plant()
        b = booted(p)
        start(b, GRINDER)
        seen = []
        self.assertTrue(b.run(1.0, until=lambda x: x.plant.grinder_on))
        b.run(1.0, each=lambda x: seen.append((x.esp.view.status.grinder_ma, p.grinder_mean_amps)))
        # STATUS follows the mean of the full-wave current: the 1 ms samples
        # average whole 100 Hz periods instead of aliasing them.
        stm, real = seen[-1]
        self.assertAlmostEqual(stm / 1000, real, delta=0.08)
        self.assertTrue(finished(b, GRINDER, 4.0))
        r = report(b)
        on_ms, peak, loaded, last, zero, rail = r.value
        self.assertEqual((r.phase, r.reason), (DONE, R_OK), r)
        self.assertLess(abs(zero), 30)
        self.assertGreater(peak, 2000)              # stalled rotor at switch-on
        self.assertAlmostEqual(last, 900, delta=60)  # ASSUMED loaded current
        self.assertGreater(loaded, last)
        b.run(0.2)
        self.assertTrue(loads_off(b))

    def test_an_empty_hopper_stops_the_grinder(self):
        p = Plant(beans_g=2.0)
        b = booted(p)
        start(b, GRINDER)
        self.assertTrue(finished(b, GRINDER, 6.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (ABORTED, R_NO_BEANS), r)
        self.assertLess(r.elapsed_ms, 2500)          # 2 g last 1.7 s at 1.2 g/s
        self.assertEqual(p.beans_g, 0.0)
        b.run(0.2)
        self.assertTrue(loads_off(b))
        self.assertIn('Motivo: sin cafe en tolva', ' '.join(lines(b)))

    def test_no_beans_from_the_start(self):
        p = Plant(beans_g=0.0)
        b = booted(p)
        start(b, GRINDER)
        self.assertTrue(finished(b, GRINDER, 3.0))
        self.assertEqual((report(b).phase, report(b).reason), (ABORTED, R_NO_BEANS))
        self.assertLess(report(b).elapsed_ms, 1200)

    def test_jammed_burrs(self):
        p = Plant(grinder_jammed=True)
        b = booted(p)
        start(b, GRINDER)
        self.assertTrue(finished(b, GRINDER, 3.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (ABORTED, R_JAM), r)
        self.assertLess(r.elapsed_ms, 800)
        b.run(0.2)
        self.assertTrue(loads_off(b))

    def test_the_dose_is_pressed(self):
        p = Plant()
        b = booted(p)
        start(b, DOSE)
        self.assertTrue(finished(b, DOSE, 25.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason), (DONE, R_OK), r)
        grind_ms, grinder, verdict, i0, rise, dose = r.value
        self.assertEqual((grind_ms, verdict, dose), (6000, 0, 1))
        self.assertTrue(100 <= i0 <= 300, i0)
        self.assertGreater(rise, 2 * 40)
        self.assertEqual(p.chamber_g, 0.0)           # dropped back at rest
        self.assertLess(p.unit_pos, 0.05)

    def test_a_blocked_chute_leaves_the_chamber_empty(self):
        p = Plant(chute_blocked=True)
        b = booted(p)
        start(b, DOSE)
        self.assertTrue(finished(b, DOSE, 25.0))
        r = report(b)
        self.assertEqual((r.phase, r.reason, r.value[5]), (DONE, R_NO_DOSE, 0), r)
        self.assertLess(r.value[4], 40)
        self.assertIn('camara sin cafe', ' '.join(lines(b)))


@unittest.skipUnless(HAVE_CC, 'needs a C compiler (CC)')
class Safety(unittest.TestCase):
    def test_load_tests_are_refused_with_the_door_open(self):
        p = Plant(door_closed=False)
        b = machine(plant=p)
        b.run(1.5)
        self.assertEqual(b.fw.controller[0], 'FAULT')  # door open at boot
        for test in (BREW_UNIT, PUMP, HEATER, GRINDER, DOSE):
            with self.subTest(test=test):
                start(b, test)
                b.run(0.3)
                r = report(b)
                self.assertEqual((r.id, r.phase), (test, REFUSED), r)
                self.assertTrue(loads_off(b))
                tap(b, BACK)
                tap(b, BACK)
                tap(b, BACK)
        start(b, INPUTS)                               # the inputs test checks the door switch
        self.assertTrue(finished(b, INPUTS, 4.0))
        self.assertEqual((report(b).phase, report(b).value[0]), (DONE, 0))

    def test_stop_aborts_and_drops_every_load(self):
        b = booted()
        start(b, PUMP)
        self.assertTrue(b.run(1.0, until=lambda x: x.loads_state['pump'] is True))
        tap(b, STOP)
        self.assertTrue(b.run(0.2, until=loads_off))
        self.assertTrue(finished(b, PUMP, 0.5))
        self.assertEqual((report(b).phase, report(b).reason), (ABORTED, R_STOP))

    def test_back_while_running_also_stops(self):
        b = booted()
        start(b, HEATER)
        self.assertTrue(b.run(1.0, until=lambda x: x.loads_state['heater'] is True))
        tap(b, BACK)
        self.assertTrue(b.run(0.2, until=loads_off))
        self.assertEqual((report(b).phase, report(b).reason), (ABORTED, R_STOP))
        self.assertEqual(page(b), 'TEST')

    def test_opening_the_door_mid_test_aborts(self):
        p = Plant()
        b = booted(p)
        start(b, BREW_UNIT)
        self.assertTrue(b.run(2.0, until=lambda x: abs(x.loads_state['motor_v']) > 1.0))
        p.door_closed = False
        self.assertTrue(b.run(0.2, until=loads_off))
        self.assertTrue(b.run(0.3, until=lambda x: report(x).phase != 1))
        self.assertIn(report(b).reason, (R_DOOR,), report(b))
        self.assertEqual(b.fw.controller[0], 'FAULT')

    def test_a_hung_interface_stops_the_test(self):
        b = booted()
        start(b, HEATER)
        self.assertTrue(b.run(1.0, until=lambda x: x.loads_state['heater'] is True))
        b.esp.hung = True
        self.assertTrue(b.run(1.0, until=loads_off))
        self.assertEqual(b.fw.controller[0], 'FAULT')
        self.assertFalse(b.fw.link_ok)


if __name__ == '__main__':
    unittest.main()
