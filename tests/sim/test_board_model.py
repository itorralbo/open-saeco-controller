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

    def test_bench_24v_without_polarity_diode(self):
        b = baseline()  # J112 straight onto 24V_ACT_RAW, as before 2026-10-07
        set_net(b['controller'], 'J112', '1', '24V_ACT_RAW')
        self.expect(b, 'reverse-polarity', 'U303.VIN')

    def test_bench_polarity_diode_reversed(self):
        b = baseline()  # D308 fitted the wrong way round blocks nothing
        set_net(b['controller'], 'D308', '1', '24V_BENCH_FUSED')
        set_net(b['controller'], 'D308', '2', '24V_ACT_RAW')
        self.expect(b, 'reverse-polarity', 'D308.K')

    def test_probe_header_rail_next_to_rail(self):
        b = baseline()  # the 3.3 V probe moved next to the 12 V one
        set_net(b['controller'], 'J114', '3', 'PROBE_3V3')
        set_net(b['controller'], 'J114', '2', 'GND_UI')
        self.expect(b, 'probe-header', 'J114.3 (PROBE_3V3) y J114.4 (PROBE_12V) son contiguos')

    def test_probe_header_pin_straight_on_a_rail(self):
        b = baseline()  # J114.4 on 12V_PROTECTED, as before 2026-10-07
        set_net(b['controller'], 'J114', '4', '12V_PROTECTED')
        self.expect(b, 'probe-header', 'J114.4 (12V_PROTECTED) llega a')

    def test_probe_header_pin_on_an_adc_node(self):
        b = baseline()  # the 24 V telemetry node back on J114.6
        set_net(b['controller'], 'J114', '6', 'RAIL_24V_ADC')
        self.expect(b, 'probe-header', 'U101.PC1')

    def test_flow_sensor_fed_straight_from_the_rail(self):
        b = baseline()  # J106.3 on 12V_PROTECTED, as before 2026-10-07
        set_net(b['controller'], 'J106', '3', '12V_PROTECTED')
        self.expect(b, 'offboard-supply', 'controller:J106.3 (12V_PROTECTED)')

    def test_water_sensor_fed_straight_from_the_plane(self):
        b = baseline()  # J109.1 on 3V3_CORE, as before 2026-10-07
        set_net(b['controller'], 'J109', '1', '3V3_CORE')
        self.expect(b, 'offboard-supply', 'controller:J109.1 (3V3_CORE)')

    def test_front_panel_switch_without_current_limit(self):
        b = baseline()  # the TPS22918 that was U302 has no current limit
        b['controller'].components['U302'].fields['mpn'] = 'TPS22918DBVR'
        self.expect(b, 'offboard-supply', 'controller:J104.1 (3V3_UI)')

    def test_tvs_breaks_down_above_what_it_protects(self):
        b = baseline()  # the SMAJ18A starts at 20-22.1 V, over U502's 20 V VDD
        b['controller'].components['D302'].fields['mpn'] = 'SMAJ18A'
        self.expect(b, 'tvs', 'U502.VDD')

    def test_mains_fuse_below_the_fault_current(self):
        b = baseline()  # the JFC2410 that was F703 breaks 50 A, not 1500 A
        b['controller'].components['F703'].fields['mpn'] = 'JFC2410-1400TS'
        self.expect(b, 'fuse-breaking', 'F703 (JFC2410-1400TS) corta 50 A')

    def test_mains_fuse_without_a_breaking_rating(self):
        b = baseline()  # F701 had no part, so no rating, until 2026-10-06
        b['controller'].components['F701'].fields['mpn'] = ''
        self.expect(b, 'fuse-breaking', 'F701 (sin MPN)')

    def test_resistor_over_its_rating(self):
        b = baseline()  # the catalogue's 100 mW 1k back in the 12 V LED feed
        b['controller'].components['R709'].fields['lcsc'] = 'C21190'
        self.expect(b, 'resistor-power', 'R709')

    def test_wdi_left_to_follow_pb4_through_reset(self):
        b = baseline()  # U601 WDI back on the kick, without U606 between them
        set_net(b['controller'], 'U601', '4', 'WATCHDOG_KICK')
        self.expect(b, 'wdi-reset', 'U601.WDI')

    def test_grinder_sensor_without_supply(self):
        b = baseline()  # U704's VS pads left off the 3.3 V rail
        for pad in ('9', '10'):
            set_net(b['controller'], 'U704', pad, 'U704_VS')
        self.expect(b, 'analog', 'GRINDER_CURRENT')

    def test_grinder_current_bypassing_the_sensor(self):
        b = baseline()  # JP8's + back on the bridge, U704's input shorted
        set_net(b['controller'], 'J115', '1', 'GRINDER_DC_PLUS')
        set_net(b['controller'], 'U704', '2', 'GRINDER_DC_PLUS')
        self.expect(b, 'analog', 'U704')

    def test_unclaimed_mcu_net(self):
        b = baseline()
        set_net(b['controller'], 'U101', '42', 'SPARE')
        found = [f for f in run(b).findings if f.code == 'unclaimed-net']
        self.assertTrue(any('SPARE' in f.message for f in found))


if __name__ == '__main__':
    unittest.main()
