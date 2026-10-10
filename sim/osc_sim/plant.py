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
    # Pressing the dose: base plus a share per gram in the chamber, ASSUMED
    # until BU-05 (manual: I0 + 55 to 200 mA with coffee; 7 g -> ~0.1 A).
    motor_compression_a: float = 0.02
    motor_compression_a_per_g: float = 0.012
    motor_tau_s: float = 0.03          # ASSUMED: mechanical time constant, sets the start peak
    unit_present: bool = True
    unit_pos: float = 0.0              # 0 = rest, 1 = work end stop
    # Valve: OLAB 6000BH/B0DN, 56.7 ohm measured.
    valve_ohms: float = 56.7
    door_closed: bool = True
    # Water tank and JP22 sensor: ASSUMED digital-like output until WL-01.
    tank_ml: float = 1500.0
    tank_capacity_ml: float = 1800.0
    water_low_ml: float = 150.0
    water_present_v: float = 2.0
    water_absent_v: float = 0.3
    water_override: float = None       # volts forced from the panel, None = follow the tank
    # Grinder: ASSUMED 1.2 g/s until GR-07. V3.2 motor on rectified mains
    # through U704; mean currents ASSUMED until GR-02/03/08, the stall from
    # the 68 Ohm winding: 230 V x 0.9 / 68 = 3.0 A mean.
    beans_g: float = 200.0
    grind_g_per_s: float = 1.2
    ground_g: float = 0.0
    chamber_g: float = 0.0             # ground coffee waiting in the brew chamber
    grinder_loaded_a: float = 0.9      # ASSUMED, grinding
    grinder_free_a: float = 0.45       # ASSUMED, running light (hopper empty)
    grinder_stall_a: float = 230.0 * 0.9 / 68.0
    grinder_tau_s: float = 0.15        # ASSUMED, inrush decay
    mains_hz: float = 50.0
    grinder_jammed: bool = False       # fault: burrs blocked
    chute_blocked: bool = False        # fault: ground coffee does not reach the chamber
    grinder_on: bool = False
    valve_on: bool = False
    pump_on: bool = False
    heater_on: bool = False
    # State
    t: float = 0.0
    flow_ml: float = 0.0
    log: list = field(default_factory=list)
    _motor_a: float = 0.0
    _emf: float = 0.0
    _grind_a: float = 0.0
    _pressed: bool = False

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
        out = [('r', 'controller:J105.2', 'controller:J105.1', self.ntc_ohms()),
               ('r', 'controller:J113.5', 'controller:J113.4', self.valve_ohms),
               # Back-EMF from J108.8 (BREW_OUT1) to J108.7 while the unit moves.
               ('vr', 'controller:J108.8', 'controller:J108.7', self._emf, self.motor_ohms),
               ('src', 'controller:J109.2', self.water_volts, 1000.0)]
        if self.door_closed:
            out.append(('r', 'controller:J107.2', 'controller:J107.1', 0.05))
        if self.unit_present:
            out.append(('r', 'controller:J108.4', 'controller:J108.3', 0.05))
        if self.unit_present and self.unit_pos >= 0.95:
            out.append(('r', 'controller:J108.2', 'controller:J108.1', 0.05))
        if self.flow_low():
            out.append(('r', 'controller:J106.1', 'controller:J106.2', 20.0))
        return out

    @property
    def water_volts(self):
        if self.water_override is not None:
            return self.water_override
        return self.water_present_v if self.tank_ml > self.water_low_ml else self.water_absent_v

    @water_volts.setter
    def water_volts(self, v):
        self.water_override = v

    @property
    def motor_amps(self):
        return self._motor_a

    @property
    def grinder_mean_amps(self):
        return self._grind_a if self.grinder_on else 0.0

    @property
    def grinder_amps(self):
        """Current in JP8's + line now: full-wave rectified, mean grinder_mean_amps."""
        return self.grinder_mean_amps * math.pi / 2 * abs(math.sin(2 * math.pi * self.mains_hz * self.t))

    # -- dynamics ---------------------------------------------------------------
    def step(self, dt, heater_on, pump_on, motor_volts, valve_on=False, grinder_on=False):
        """Advance dt seconds. motor_volts: J108.8 minus J108.7 (forward > 0)."""
        self.t += dt
        was_grinding = self.grinder_on
        self.heater_on, self.pump_on, self.valve_on = heater_on, pump_on, valve_on
        p = MAINS_V ** 2 / self.heater_ohms if heater_on else 0.0
        # The pump only moves water while the tank has some.
        flow = self.pump_ml_s if pump_on and self.tank_ml > 0 else 0.0
        self.tank_ml = max(0.0, self.tank_ml - flow * dt)
        self.flow_ml += flow * dt
        if grinder_on:
            if self.grinder_jammed:
                target = self.grinder_stall_a
            else:
                target = self.grinder_loaded_a if self.beans_g > 0 else self.grinder_free_a
                g = min(self.beans_g, self.grind_g_per_s * dt)
                self.beans_g -= g
                self.ground_g += g
                if not self.chute_blocked:
                    self.chamber_g += g
            if not was_grinding:
                self._grind_a = self.grinder_stall_a  # starts as a stalled rotor
            self._grind_a += (target - self._grind_a) * min(1.0, dt / self.grinder_tau_s)
        else:
            self._grind_a = 0.0
        self.grinder_on = grinder_on
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
            # The back-EMF rises toward its running value with motor_tau_s:
            # the start draws close to V/R, then falls to the load current.
            press = self.motor_compression_a + self.motor_compression_a_per_g * self.chamber_g
            load = self.motor_friction_a + (press if self.unit_pos > 0.7 else 0.0)
            run = max(0.0, abs(v) - load * self.motor_ohms)
            emf = min(abs(self._emf), run) if self._emf * direction > 0 else 0.0
            emf += (run - emf) * min(1.0, dt / self.motor_tau_s)
            self._motor_a, self._emf = (abs(v) - emf) / self.motor_ohms, direction * emf
            self.unit_pos = min(1.0, max(0.0, self.unit_pos + direction * emf / self.motor_v_per_unit_s * dt))
        # Back at rest after pressing, the unit drops the spent dose.
        if self.unit_pos >= 0.95:
            self._pressed = True
        elif self.unit_pos <= 0.02 and self._pressed:
            self._pressed = False
            self.chamber_g = 0.0
