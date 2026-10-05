"""Both firmwares built for the host and loaded with ctypes (F1, F2).

Each library holds the real sources (STM32: controller, BSP, main loop;
ESP32: front panel, display and link core; both: protocol v0) on top of a
host HAL in sim/hal. The compiler is $CC (default cc), with $SDKROOT as
sysroot when set, the same flags as CMake. Each object loads its own copy
of the library, so two boards never share globals.
"""
import atexit
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORTS, PINS, ADCS, CHANNELS, UART_BUF = 6, 16, 2, 20, 512
ESP_GPIOS = 49
MODES = ('analog', 'input', 'output', 'af')
STATES = ('BOOT', 'SAFE_IDLE', 'FAULT')

TARGETS = {
    'stm32': {
        'lib': 'libosc_fw',
        'sources': ['firmware/stm32/src/controller.c', 'firmware/stm32/src/bsp.c',
                    'firmware/stm32/src/app.c', 'firmware/common/proto.c', 'sim/hal/hal_sim.c'],
        'include': ['firmware/stm32/include', 'firmware/common', 'sim/hal'],
    },
    'esp32': {
        'lib': 'libosc_esp',
        'sources': ['firmware/esp32/core/frontpanel.c', 'firmware/esp32/core/display.c',
                    'firmware/esp32/core/esp_app.c', 'firmware/common/proto.c', 'sim/hal/hal_esp_sim.c'],
        'include': ['firmware/esp32/core', 'firmware/esp32/main', 'firmware/common', 'sim/hal'],
    },
}


class SimIO(ctypes.Structure):
    """Mirror of sim/hal/sim_io.h."""
    _fields_ = [('millis', ctypes.c_uint32),
                ('mode', (ctypes.c_uint8 * PINS) * PORTS),
                ('af', (ctypes.c_uint8 * PINS) * PORTS),
                ('odr', (ctypes.c_uint8 * PINS) * PORTS),
                ('idr', (ctypes.c_uint8 * PINS) * PORTS),
                ('idr_valid', (ctypes.c_uint8 * PINS) * PORTS),
                ('pwm', (ctypes.c_uint16 * PINS) * PORTS),
                ('edges', (ctypes.c_uint32 * PINS) * PORTS),
                ('adc', (ctypes.c_uint16 * CHANNELS) * ADCS),
                ('dead_battery', ctypes.c_uint8),
                ('vrefint_cal', ctypes.c_uint16),
                ('undefined_reads', ctypes.c_uint32),
                ('analog_reads', ctypes.c_uint32),
                ('bad_calls', ctypes.c_uint32),
                ('uart_tx', ctypes.c_uint8 * UART_BUF),
                ('uart_tx_len', ctypes.c_uint16),
                ('uart_rx', ctypes.c_uint8 * UART_BUF),
                ('uart_rx_head', ctypes.c_uint16),
                ('uart_rx_len', ctypes.c_uint16)]


I2C_FN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_uint8, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint,
                          ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint)
SPI_FN = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint)
ESP_PIN = ('off', 'input', 'output', 'i2c', 'spi_clk', 'spi_mosi', 'spi_cs', 'uart_tx', 'uart_rx', 'ledc')


class EspIO(ctypes.Structure):
    """Mirror of sim/hal/sim_esp_io.h."""
    _fields_ = [('millis', ctypes.c_uint32),
                ('mode', ctypes.c_uint8 * ESP_GPIOS),
                ('level', ctypes.c_uint8 * ESP_GPIOS),
                ('in_', ctypes.c_uint8 * ESP_GPIOS),
                ('in_valid', ctypes.c_uint8 * ESP_GPIOS),
                ('duty', ctypes.c_uint16 * ESP_GPIOS),
                ('i2c_hz', ctypes.c_uint32), ('spi_hz', ctypes.c_uint32), ('uart_baud', ctypes.c_uint32),
                ('undefined_reads', ctypes.c_uint32), ('bad_calls', ctypes.c_uint32),
                ('spi_bytes', ctypes.c_uint32), ('i2c_xfers', ctypes.c_uint32),
                ('i2c', I2C_FN), ('spi', SPI_FN),
                ('uart_tx', ctypes.c_uint8 * UART_BUF),
                ('uart_tx_len', ctypes.c_uint16),
                ('uart_rx', ctypes.c_uint8 * UART_BUF),
                ('uart_rx_head', ctypes.c_uint16),
                ('uart_rx_len', ctypes.c_uint16)]


class Outputs(ctypes.Structure):
    _fields_ = [(n, ctypes.c_bool) for n in ('heater', 'pump', 'valve', 'grinder', 'brew_motor')]


class Controller(ctypes.Structure):
    _fields_ = [('state', ctypes.c_int), ('outputs', Outputs)]


class Status(ctypes.Structure):
    _fields_ = [('state', ctypes.c_uint8), ('inputs', ctypes.c_uint8), ('outputs', ctypes.c_uint16),
                ('rail_12v_mv', ctypes.c_uint16), ('rail_24v_mv', ctypes.c_uint16),
                ('brew_ma', ctypes.c_uint16), ('ntc_raw', ctypes.c_uint16), ('uptime_ms', ctypes.c_uint32)]


class Keypad(ctypes.Structure):
    _fields_ = [('valid', ctypes.c_bool), ('armed', ctypes.c_bool), ('led', ctypes.c_bool),
                ('keys', ctypes.c_uint8), ('candidate', ctypes.c_uint8), ('presses', ctypes.c_uint8),
                ('since', ctypes.c_uint32), ('last_sample', ctypes.c_uint32), ('last_try', ctypes.c_uint32),
                ('nacks', ctypes.c_uint32)]


class Display(ctypes.Structure):
    _fields_ = [('phase', ctypes.c_int), ('t', ctypes.c_uint32),
                ('bg', ctypes.c_uint16), ('bar', ctypes.c_uint16),
                ('shown_bg', ctypes.c_uint16), ('shown_bar', ctypes.c_uint16),
                ('painted', ctypes.c_bool), ('backlight', ctypes.c_bool), ('frames', ctypes.c_uint32)]


class EspView(ctypes.Structure):
    """Mirror of osc_esp_view (firmware/esp32/core/esp_app.h)."""
    _fields_ = [('link_ok', ctypes.c_bool), ('have_status', ctypes.c_bool), ('standby', ctypes.c_bool),
                ('status', Status), ('screen', ctypes.c_int), ('front', ctypes.c_int),
                ('last_reply_type', ctypes.c_uint8), ('last_reply_code', ctypes.c_uint8),
                ('last_reply_for', ctypes.c_uint8),
                ('requests', ctypes.c_uint32), ('replies', ctypes.c_uint32), ('recoveries', ctypes.c_uint32),
                ('keypad', Keypad), ('display', Display)]


SCREENS = ('BOOT', 'LINK_LOST', 'STARTING', 'IDLE', 'FAULT', 'STANDBY')
FRONT = ('WAIT', 'ON', 'POWER_OFF', 'POWER_ON')


def compiler():
    return os.environ.get('CC') or shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')


def build(target='stm32', out_dir=None):
    """Compile one firmware library; returns its path."""
    spec = TARGETS[target]
    cc = compiler()
    if not cc:
        raise RuntimeError('no C compiler: set CC')
    out_dir = Path(out_dir or ROOT / 'build/sim')
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = '.dylib' if sys.platform == 'darwin' else ('.dll' if os.name == 'nt' else '.so')
    lib = out_dir / f'{spec["lib"]}{ext}'
    srcs = [ROOT / s for s in spec['sources']]
    headers = [h for d in spec['include'] for h in (ROOT / d).glob('*.h')]
    if lib.exists() and all(lib.stat().st_mtime >= p.stat().st_mtime for p in srcs + headers):
        return lib
    cmd = [cc, '-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic', '-O1', '-fPIC', '-shared',
           *(f'-I{ROOT / d}' for d in spec['include']), *map(str, srcs), '-o', str(lib)]
    if os.environ.get('SDKROOT'):
        cmd[1:1] = ['-isysroot', os.environ['SDKROOT']]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return lib


def _load(path):
    # A private copy, so each instance has its own globals.
    tmp = tempfile.mkdtemp(prefix='osc_fw_')
    atexit.register(shutil.rmtree, tmp, True)
    copy = Path(tmp) / Path(path).name
    shutil.copy(path, copy)
    return ctypes.CDLL(str(copy))


class Firmware:
    """The STM32 running the firmware; the board drives its clock and reset."""

    def __init__(self, lib_path=None):
        self.lib = _load(lib_path or build('stm32'))
        self.io = SimIO.in_dll(self.lib, 'osc_sim_io')
        self.lib.osc_app_controller.restype = ctypes.POINTER(Controller)
        self.lib.osc_app_link_ok.restype = ctypes.c_bool
        assert self.lib.osc_sim_size() == ctypes.sizeof(SimIO), 'SimIO out of step with sim_io.h'
        self.running = False
        self.hung = False
        self.lib.osc_sim_reset()

    def reset(self):
        """NRST low: every pin back to its reset state, the core stops."""
        self.lib.osc_sim_reset()
        self.running = False
        self.hung = False  # a reset is what gets a hung core going again

    def start(self, millis):
        """NRST released: the firmware runs from main()."""
        self.io.millis = millis
        self.lib.osc_app_init()
        self.running = True

    def poll(self, millis):
        self.io.millis = millis
        if self.running and not self.hung:
            self.lib.osc_app_poll()

    @property
    def controller(self):
        c = self.lib.osc_app_controller().contents
        return STATES[c.state], {n: getattr(c.outputs, n) for n, _ in Outputs._fields_}

    @property
    def link_ok(self):
        return bool(self.lib.osc_app_link_ok()) if self.running else False

    def mode(self, port, pin):
        return MODES[self.io.mode[port][pin]]


class EspFirmware:
    """The ESP32-S3 interface core; i2c and spi answer through the board."""

    def __init__(self, lib_path=None):
        self.lib = _load(lib_path or build('esp32'))
        self.io = EspIO.in_dll(self.lib, 'osc_esp_io')
        self.lib.esp_app_view.restype = ctypes.POINTER(EspView)
        self.hung = False
        assert self.lib.osc_esp_sim_size(0) == ctypes.sizeof(EspIO), 'EspIO out of step with sim_esp_io.h'
        assert self.lib.osc_esp_sim_size(1) == ctypes.sizeof(EspView), 'EspView out of step with esp_app.h'
        self.running = False
        self._cb = []
        self.lib.osc_esp_sim_reset()

    def attach(self, i2c, spi):
        """i2c(addr, bytes written, n to read) -> bytes or None (NACK); spi(bytes)."""
        def i2c_c(addr, w, wn, r, rn):
            got = i2c(addr, bytes(w[i] for i in range(wn)), rn)
            if got is None:
                return 0
            for i in range(rn):
                r[i] = got[i]
            return 1

        def spi_c(data, n):
            spi(ctypes.string_at(data, n))
        self._cb = [I2C_FN(i2c_c), SPI_FN(spi_c)]  # keep references alive
        self.io.i2c, self.io.spi = self._cb

    def reset(self):
        self.lib.osc_esp_sim_reset()
        self.running = False

    def start(self, millis):
        self.io.millis = millis
        self.lib.esp_app_init()
        self.running = True

    def poll(self, millis):
        self.io.millis = millis
        if self.running and not self.hung:
            self.lib.esp_app_poll()

    @property
    def view(self):
        return self.lib.esp_app_view().contents

    def pin_mode(self, gpio):
        return ESP_PIN[self.io.mode[gpio]]
