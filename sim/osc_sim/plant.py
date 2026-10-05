"""The machine around the board (F1): boiler, NTC, pump and flow meter, brew
unit, door, valve and water sensor, at the connector pins of the contract.

Measured or documented values carry their source; the rest are placeholders
marked ASSUMED until the machine is characterised
(docs/HD8911/characterization-plan.md). The plant only has to be plausible
enough to exercise the board and the firmware, not to tune a controller.
"""
import math
from dataclasses import dataclass, field

MAINS_V = 230.0
WATER_J_PER_ML_K = 4.18


@dataclass
class Plant:
    # Heater: 27.5 ohm measured, 1900 W nominal (hardware/power/power-architecture.md).
    heater_ohms: float = 27.5
    boiler_j_per_k: float = 400.0      # ASSUMED: ~0.45 kg of aluminium thermoblock
    boiler_loss_w_per_k: float = 1.5   # ASSUMED
    ambient_c: float = 20.0
    inlet_c: float = 20.0
    boiler_c: float = 20.0
    # NTC fit R25 49.9 kOhm, B 4037 K (docs/HD8911/components.md, as the contract).
    ntc_r25: float = 49900.0
    ntc_beta: float = 4037.0
    ntc_open: bool = False
    # Pump and Digmesa FHKSC 932-9521-B, ~1925 pulses/L (docs/verification.md).
    pump_ml_s: float = 5.0             # ASSUMED, against the brew pressure
    flow_pulses_per_l: float = 1925.0
    # Brew unit: 54.7 ohm measured; I0 100-300 mA and +55..200 mA under
    # compression (docs/verification.md). Travel time ASSUMED.
    motor_ohms: float = 54.7
    motor_v_per_unit_s: float = 39.0   # ASSUMED: ~3 s per full travel at 24 V
    motor_friction_a: float = 0.2
    motor_compression_a: float = 0.1
    unit_present: bool = True
    unit_pos: float = 0.0              # 0 = rest, 1 = work end stop
    # Valve: OLAB 6000BH/B0DN, 56.7 ohm measured.
    valve_ohms: float = 56.7
    door_closed: bool = True
    water_volts: float = 2.0           # ASSUMED: JP22 output not measured
    # State
    t: float = 0.0
    flow_ml: float = 0.0
    log: list = field(default_factory=list)
    _motor_a: float = 0.0
    _emf: float = 0.0

    # -- electrical view ------------------------------------------------------
    def ntc_ohms(self):
        if self.ntc_open:
            return 1e9
        t = self.boiler_c + 273.15
        return self.ntc_r25 * math.exp(self.ntc_beta * (1 / t - 1 / 298.15))

    def flow_low(self):
        """Open-collector output state: low for half of each pulse period."""
        pulses = self.flow_ml / 1000.0 * self.flow_pulses_per_l
        return (pulses % 1.0) >= 0.5

    def elements(self):
        """Plant parts at the connector pins: ('r', a, b, ohms), ('vr', a, b, volts, ohms), ('src', a, volts, ohms)."""
        out = [('r', 'controller:J105.1', 'controller:J105.2', self.ntc_ohms()),
               ('r', 'controller:J113.1', 'controller:J113.2', self.valve_ohms),
               # Back-EMF from J108.2 (BREW_OUT1) to J108.1 while the unit moves.
               ('vr', 'controller:J108.2', 'controller:J108.1', self._emf, self.motor_ohms),
               ('src', 'controller:J109.2', self.water_volts, 1000.0)]
        if self.door_closed:
            out.append(('r', 'controller:J107.1', 'controller:J107.2', 0.05))
        if self.unit_present:
            out.append(('r', 'controller:J108.6', 'controller:J108.5', 0.05))
        if self.unit_present and self.unit_pos >= 0.95:
            out.append(('r', 'controller:J108.8', 'controller:J108.7', 0.05))
        if self.flow_low():
            out.append(('r', 'controller:J106.1', 'controller:J106.2', 20.0))
        return out

    @property
    def motor_amps(self):
        return self._motor_a

    # -- dynamics ---------------------------------------------------------------
    def step(self, dt, heater_on, pump_on, motor_volts):
        """Advance dt seconds. motor_volts: J108.2 minus J108.1 (forward > 0)."""
        self.t += dt
        p = MAINS_V ** 2 / self.heater_ohms if heater_on else 0.0
        flow = self.pump_ml_s if pump_on else 0.0
        self.flow_ml += flow * dt
        loss = self.boiler_loss_w_per_k * (self.boiler_c - self.ambient_c)
        water = flow * WATER_J_PER_ML_K * (self.boiler_c - self.inlet_c)
        self.boiler_c += (p - loss - water) * dt / self.boiler_j_per_k
        # Brew unit: quasi-static motor, current set by friction and load.
        v = motor_volts or 0.0
        direction = (v > 0) - (v < 0)
        stalled = (direction > 0 and self.unit_pos >= 1.0) or (direction < 0 and self.unit_pos <= 0.0) \
            or not self.unit_present
        if direction == 0 or abs(v) < 1e-3:
            self._motor_a, self._emf = 0.0, 0.0
        elif stalled:
            self._motor_a, self._emf = abs(v) / self.motor_ohms, 0.0
        else:
            load = self.motor_friction_a + (self.motor_compression_a if self.unit_pos > 0.7 else 0.0)
            i = min(load, abs(v) / self.motor_ohms)
            emf = abs(v) - i * self.motor_ohms
            self._motor_a, self._emf = i, direction * emf
            self.unit_pos = min(1.0, max(0.0, self.unit_pos + direction * emf / self.motor_v_per_unit_s * dt))
