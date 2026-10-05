"""The STM32 firmware built for the host and loaded with ctypes (F1).

The library holds the real firmware/stm32 sources (controller, BSP, main
loop) on top of sim/hal/hal_sim.c. The compiler is $CC (default cc), with
$SDKROOT as sysroot when set, the same flags as CMake. Each Firmware object
loads its own copy of the library, so two boards never share globals.
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
SOURCES = ['firmware/stm32/src/controller.c', 'firmware/stm32/src/bsp.c',
           'firmware/stm32/src/app.c', 'sim/hal/hal_sim.c']
PORTS, PINS, ADCS, CHANNELS = 6, 16, 2, 20
MODES = ('analog', 'input', 'output', 'af')
STATES = ('BOOT', 'SAFE_IDLE', 'FAULT')


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
                ('undefined_reads', ctypes.c_uint32),
                ('analog_reads', ctypes.c_uint32),
                ('bad_calls', ctypes.c_uint32)]


class Outputs(ctypes.Structure):
    _fields_ = [(n, ctypes.c_bool) for n in ('heater', 'pump', 'valve', 'grinder', 'brew_motor')]


class Controller(ctypes.Structure):
    _fields_ = [('state', ctypes.c_int), ('outputs', Outputs)]


def compiler():
    cc = os.environ.get('CC') or shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')
    return cc


def build(out_dir=None):
    """Compile the firmware library; returns its path."""
    cc = compiler()
    if not cc:
        raise RuntimeError('no C compiler: set CC')
    out_dir = Path(out_dir or ROOT / 'build/sim')
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = '.dylib' if sys.platform == 'darwin' else ('.dll' if os.name == 'nt' else '.so')
    lib = out_dir / f'libosc_fw{ext}'
    srcs = [ROOT / s for s in SOURCES]
    headers = list((ROOT / 'firmware/stm32/include').glob('*.h')) + list((ROOT / 'sim/hal').glob('*.h'))
    if lib.exists() and all(lib.stat().st_mtime >= p.stat().st_mtime for p in srcs + headers):
        return lib
    cmd = [cc, '-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic', '-O1', '-fPIC', '-shared',
           f'-I{ROOT / "firmware/stm32/include"}', f'-I{ROOT / "sim/hal"}', *map(str, srcs), '-o', str(lib)]
    if os.environ.get('SDKROOT'):
        cmd[1:1] = ['-isysroot', os.environ['SDKROOT']]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return lib


class Firmware:
    """One STM32 running the firmware; the board drives its clock and reset."""

    def __init__(self, lib_path=None):
        src = Path(lib_path or build())
        # A private copy, so each instance has its own globals.
        tmp = tempfile.mkdtemp(prefix='osc_fw_')
        atexit.register(shutil.rmtree, tmp, True)
        path = Path(tmp) / src.name
        shutil.copy(src, path)
        self.lib = ctypes.CDLL(str(path))
        self.io = SimIO.in_dll(self.lib, 'osc_sim_io')
        self.lib.osc_app_controller.restype = ctypes.POINTER(Controller)
        self.running = False
        self.hung = False
        self.lib.osc_sim_reset()

    def reset(self):
        """NRST low: every pin back to its reset state, the core stops."""
        self.lib.osc_sim_reset()
        self.running = False

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

    def mode(self, port, pin):
        return MODES[self.io.mode[port][pin]]
