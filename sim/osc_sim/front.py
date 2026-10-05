"""The front panel on the far end of the harness (F2): seven keys, the
TCA9534 and the ST7789 display, as the ESP32 sees them.

The devices only work from what the board gives them: they answer when
3V3_UI is up, the TCA9534 reads each key from the voltage on its pin (the
switch, R1x pull-up and R2x series resistor are in the netlist), its INT is
an open-drain pull-down on the circuit, and the display listens only out of
reset. Register behaviour from TI SCPS197D (TCA9534) and the ST7789V
command set (CASET/RASET/RAMWR, COLMOD, MADCTL, SLPOUT, DISPON).
"""
from dataclasses import dataclass, field

TCA_VCC_MIN = 1.65   # TCA9534 supply range 1.65-5.5 V
TCA_VIH, TCA_VIL = 0.7, 0.3
LCD_VCC_MIN = 2.4    # ST7789V VDDI/VDD minimum, rounded


@dataclass
class Tca9534:
    address: int = 0x20
    output: int = 0xFF
    polarity: int = 0x00
    config: int = 0xFF
    pointer: int = 0
    last_read: int = 0xFF
    pins: int = 0xFF
    powered: bool = False
    undefined: int = 0
    hung: bool = False  # a latched-up bus interface; only a power cycle clears it

    def power(self, on):
        if on and not self.powered:
            undefined = self.undefined
            self.__init__(self.address)  # power-on reset: all inputs, INT released
            self.powered = True
            self.undefined = undefined
            self.last_read = self.pins
        elif not on:
            self.powered = False

    def input(self):
        # Outputs read back their own level; inputs the pins.
        value = (self.pins & self.config) | (self.output & ~self.config & 0xFF)
        return value ^ self.polarity

    @property
    def int_low(self):
        return self.powered and ((self.input() ^ self.last_read) & self.config) != 0

    def xfer(self, w, rn):
        if not self.powered or self.hung:
            return None
        if w:
            self.pointer = w[0] & 0x03
            for b in w[1:]:
                if self.pointer == 1:
                    self.output = b
                elif self.pointer == 2:
                    self.polarity = b
                elif self.pointer == 3:
                    self.config = b
        out = []
        for _ in range(rn):
            if self.pointer == 0:
                v = self.input()
                self.last_read = v  # reading the input port clears INT
            else:
                v = (0, self.output, self.polarity, self.config)[self.pointer]
            out.append(v)
        return bytes(out)


@dataclass
class St7789:
    width: int = 320   # landscape after MADCTL MV
    height: int = 240
    powered: bool = False
    awake: bool = False
    on: bool = False
    colmod: int = 0
    madctl: int = 0
    window: tuple = (0, 0, 319, 239)
    cursor: int = 0
    command: int = 0
    args: bytearray = field(default_factory=bytearray)
    frame: bytearray = field(default_factory=lambda: bytearray(320 * 240 * 2))
    pixels_written: int = 0
    ignored: int = 0
    backlight: bool = False

    def power(self, on):
        if not on:
            self.powered = self.awake = self.on = False
        elif not self.powered:
            self.powered = True
            self.reset()

    def reset(self):
        self.awake = self.on = False
        self.colmod = self.madctl = 0
        self.command = 0
        self.args = bytearray()

    def spi(self, data, dc, rst_high):
        if not self.powered or not rst_high:
            self.ignored += len(data)
            return
        if not dc:
            for c in data:
                self._command(c)
            return
        if self.command == 0x2C:
            self._pixels(data)
        else:
            self.args += data
            self._apply()

    def _command(self, c):
        self.command = c
        self.args = bytearray()
        if c == 0x01:
            self.reset()
            self.command = 0x01
        elif c == 0x11:
            self.awake = True
        elif c == 0x29:
            self.on = True
        elif c == 0x28:
            self.on = False
        elif c == 0x2C:
            self.cursor = 0

    def _apply(self):
        a = self.args
        if self.command == 0x3A and len(a) >= 1:
            self.colmod = a[0]
        elif self.command == 0x36 and len(a) >= 1:
            self.madctl = a[0]
        elif self.command in (0x2A, 0x2B) and len(a) >= 4:
            lo, hi = (a[0] << 8) | a[1], (a[2] << 8) | a[3]
            x0, y0, x1, y1 = self.window
            self.window = (lo, y0, hi, y1) if self.command == 0x2A else (x0, lo, x1, hi)

    def _pixels(self, data):
        if not self.awake or self.colmod != 0x55:
            self.ignored += len(data)
            return
        x0, y0, x1, y1 = self.window
        w = x1 - x0 + 1
        n = len(data) // 2
        if x0 == 0 and w == self.width:
            # Full-width window: the frame is contiguous.
            start = (y0 * self.width + self.cursor) * 2
            end = min(start + n * 2, (y1 + 1) * self.width * 2, len(self.frame))
            if end > start:
                self.frame[start:end] = data[:end - start]
        else:
            for i in range(n):
                c = self.cursor + i
                x, y = x0 + c % w, y0 + c // w
                if y <= y1 and x < self.width and y < self.height:
                    o = (y * self.width + x) * 2
                    self.frame[o:o + 2] = data[2 * i:2 * i + 2]
        self.cursor += n
        self.pixels_written += n

    def pixel(self, x, y):
        o = (y * self.width + x) * 2
        return (self.frame[o] << 8) | self.frame[o + 1]

    @property
    def visible(self):
        return self.powered and self.awake and self.on and self.backlight


@dataclass
class FrontPanel:
    """Keys by switch reference (SW1-SW7); pressed ones close to ground."""
    pressed: set = field(default_factory=set)
    tca: Tca9534 = field(default_factory=Tca9534)
    lcd: St7789 = field(default_factory=St7789)

    def elements(self):
        return [('r', f'front:{sw}.1', f'front:{sw}.2', 0.05) for sw in sorted(self.pressed)]
