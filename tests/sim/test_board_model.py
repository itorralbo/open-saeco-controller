"""Each board check must catch the fault it exists for.

The baseline is the real netlists, read through fixed_symbols() so it stays
valid if a symbol drifts from its reference pinout again; every test then
breaks one thing in memory and expects exactly that finding.
Run: python -m unittest discover -s tests/sim
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sim'))

from osc_sim import netlist  # noqa: E402
from osc_sim.checks import Checker  # noqa: E402
from osc_sim.model import System, fixed_symbols, load_contract  # noqa: E402

CONTRACT = load_contract(ROOT)


def set_net(board, ref, pad, net):
    board.components[ref].pins[pad].net = net


def baseline():
    return fixed_symbols(CONTRACT, ROOT)


def run(boards):
    for b in boards.values():  # rebuild the net index after edits
        b.nets = {}
        for ref, comp in b.components.items():
            for num, pin in comp.pins.items():
                if pin.net:
                    b.nets.setdefault(pin.net, []).append((ref, num))
    checker = Checker(System(CONTRACT, ROOT, boards=boards))
    checker.run()
    return checker


def errors(checker):
    return [(f.code, f.message) for f in checker.findings if f.severity == 'error']


class Baseline(unittest.TestCase):
    def test_fixed_design_is_clean(self):
        self.assertEqual(errors(run(baseline())), [])

    def test_real_netlists_parse_and_join(self):
        s = System(CONTRACT, ROOT)
        self.assertEqual(s.gnet('front', 'KEY_SDA'), s.gnet('controller', 'KEY_SDA'))
        self.assertIn(s.find('controller:3V3_UI'), s.rails)


class Mutations(unittest.TestCase):
    def expect(self, boards, code, text):
        found = errors(run(boards))
        self.assertTrue(any(c == code and text in m for c, m in found), found)

    def test_symbol_pinout(self):
        b = baseline()
        pins = b['controller'].components['U502'].pins
        pins['3'].name, pins['4'].name = pins['4'].name, pins['3'].name
        self.expect(b, 'symbol-pinout', 'U502')

    def test_harness_swap(self):
        b = baseline()
        set_net(b['front'], 'J1', '11', 'KEY_SDA')
        set_net(b['front'], 'J1', '12', 'KEY_SCL')
        self.expect(b, 'harness', 'pin 11')

    def test_missing_load_pull_down(self):
        b = baseline()
        del b['controller'].components['R711']
        self.expect(b, 'reset-level', 'HEATER_EN')

    def test_missing_relay_arm_pull_down(self):
        b = baseline()
        del b['controller'].components['R722']
        self.expect(b, 'reset-level', 'MAINS_ARM')

    def test_real_boards_are_clean(self):
        self.assertEqual(errors(run({n: netlist.load(ROOT / p, n)
                                     for n, p in CONTRACT['boards'].items()})), [])

    def test_missing_display_cs_pull_up(self):
        b = baseline()
        del b['front'].components['R4']
        self.expect(b, 'reset-level', 'LCD_CS_N')

    def test_interlock_bypassed(self):
        b = baseline()
        set_net(b['controller'], 'U604', '2', '3V3_CORE')
        self.expect(b, 'interlock', 'PUMP_EN')

    def test_load_unreachable(self):
        b = baseline()
        set_net(b['controller'], 'Q704', '3', None)
        self.expect(b, 'signal-path', 'PUMP_EN')

    def test_keypad_address(self):
        b = baseline()
        set_net(b['front'], 'U1', '1', '3V3_UI')
        self.expect(b, 'keypad', '0x21')

    def test_i2c_pull_up(self):
        b = baseline()
        del b['front'].components['R1']
        self.expect(b, 'pull', 'KEY_SCL')

    def test_timer_on_wrong_pin(self):
        b = baseline()  # BREW_PWM (TIM1_CH3N) and UI_PWR_EN trade pads
        set_net(b['controller'], 'U101', '5', 'UI_PWR_EN')
        set_net(b['controller'], 'U101', '34', 'BREW_PWM_RAW')
        self.expect(b, 'pin-caps', 'BREW_PWM')

    def test_adc_channel_follows_pin(self):
        b = baseline()  # NTC moves to PA0, which also has an ADC
        set_net(b['controller'], 'U101', '12', 'NTC_ADC')
        set_net(b['controller'], 'U101', '17', 'BU_WORK_N')
        r = run(b).signals[('stm32', 'NTC')]
        self.assertEqual((r.pin, r.adc), ('PA0', (1, 1)))

    def test_uart_tx_to_tx(self):
        b = baseline()
        set_net(b['controller'], 'R211', '2', 'ESP_TX_RAW')
        self.expect(b, 'signal-path', 'stm32.UART_TX')

    def test_esp32_uart_swap_is_legal(self):
        b = baseline()  # the GPIO matrix routes UART to any free pad
        set_net(b['controller'], 'U201', '35', 'STM_TO_ESP')
        set_net(b['controller'], 'U201', '38', 'ESP_TX_RAW')
        self.assertEqual(errors(run(b)), [])

    def test_divider_over_range(self):
        b = baseline()
        b['controller'].components['R703'].value = '100k'
        self.expect(b, 'analog', 'RAIL_12V')

    def test_ntc_window(self):
        b = baseline()
        b['controller'].components['R401'].value = '100'
        self.expect(b, 'analog', 'NTC')

    def test_supply_pad(self):
        b = baseline()
        set_net(b['controller'], 'U101', '29', None)  # VDDA
        self.expect(b, 'supply-pad', 'U101.29')

    def test_mosfet_not_specified_at_3v3(self):
        b = baseline()  # the SI2308A is only specified from VGS = 4.5 V
        b['controller'].components['Q705'].fields['mpn'] = 'SI2308A'
        self.expect(b, 'drive', 'HEATER_EN')

    def test_opto_led_below_ift(self):
        b = baseline()
        b['controller'].components['R709'].value = '3.3k'
        self.expect(b, 'drive', 'U701: IF')

    def test_relay_coil_below_must_operate(self):
        b = baseline()
        set_net(b['controller'], 'K701', '1', '12V_PROTECTED')
        self.expect(b, 'drive', 'K701: bobina')

    def test_gate_output_overloaded(self):
        b = baseline()
        b['controller'].components['R512'].value = '100'
        self.expect(b, 'drive-current', 'U602.2Y')

    def test_gate_reset_input_on_the_slow_rc(self):
        b = baseline()  # U602 1B back on STM_NRST, bypassing the Schmitt buffer
        set_net(b['controller'], 'U602', '2', 'STM_NRST')
        self.expect(b, 'slow-edge', 'U602.1B')

    def test_interlock_through_buffer_must_reach_nrst(self):
        b = baseline()  # U605 fed from 3.3 V: the gates no longer see the reset
        set_net(b['controller'], 'U605', '2', '3V3_CORE')
        self.expect(b, 'interlock', 'HEATER_EN')

    def test_vbus_sense_without_lower_divider(self):
        b = baseline()
        del b['controller'].components['R226']
        self.expect(b, 'pin-voltage', 'IO15')

    def test_door_pull_up_too_strong(self):
        b = baseline()  # a closed contact can no longer pull the line under VIL
        b['controller'].components['R405'].value = '100'
        self.expect(b, 'input-level', 'DOOR_CLOSED_N')

    def test_bench_supply_on_the_buck_output(self):
        b = baseline()  # J101 back on U303's output node, as before 2026-10-05
        set_net(b['controller'], 'J101', '1', '12V_ISO_RAW')
        self.expect(b, 'back-feed', 'U303.SW')

    def test_unclaimed_mcu_net(self):
        b = baseline()
        set_net(b['controller'], 'U101', '42', 'SPARE')
        found = [f for f in run(b).findings if f.code == 'unclaimed-net']
        self.assertTrue(any('SPARE' in f.message for f in found))


if __name__ == '__main__':
    unittest.main()
