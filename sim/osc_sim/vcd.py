"""Value Change Dump (IEEE 1364) of the virtual board's digital signals (F3).

Each sample is a dict name -> bool/int/None (None is written as x). Only
changes are stored, so an hour of mostly quiet signals stays small. The file
opens in GTKWave, PulseView or Surfer.
"""
from datetime import date

# Printable ASCII without '$', which starts every VCD keyword.
_ID_CHARS = ''.join(chr(c) for c in range(33, 127) if c != 36)


def _ident(n):
    s = ''
    while True:
        s = _ID_CHARS[n % len(_ID_CHARS)] + s
        n //= len(_ID_CHARS)
        if n == 0:
            return s
        n -= 1


class Recorder:
    def __init__(self, names, widths=None, limit=200000):
        """names: signal names in order; widths: {name: bits} for vectors."""
        self.names = list(names)
        self.widths = dict(widths or {})
        self.ids = {n: _ident(i) for i, n in enumerate(self.names)}
        self.changes = []   # (time in us, name, value)
        self.last = {}
        self.limit = limit
        self.dropped = 0

    def sample(self, t_us, values):
        for name in self.names:
            v = values.get(name)
            if name in self.last and self.last[name] == v:
                continue
            self.last[name] = v
            if len(self.changes) >= self.limit:
                self.dropped += 1
                continue
            self.changes.append((int(t_us), name, v))

    def _value(self, name, v):
        width = self.widths.get(name, 1)
        if width == 1:
            return ('x' if v is None else '1' if v else '0') + self.ids[name]
        bits = 'x' if v is None else format(int(v) & ((1 << width) - 1), 'b')
        return f'b{bits} {self.ids[name]}'

    def text(self, scope='osc'):
        out = [f'$date {date.today().isoformat()} $end',
               '$version open-saeco-controller virtual board $end',
               '$timescale 1us $end',
               f'$scope module {scope} $end']
        for name in self.names:
            kind = 'wire' if self.widths.get(name, 1) == 1 else 'reg'
            out.append(f'$var {kind} {self.widths.get(name, 1)} {self.ids[name]} {name} $end')
        out += ['$upscope $end', '$enddefinitions $end']
        current = None
        for t, name, v in self.changes:
            if t != current:
                out.append(f'#{t}')
                current = t
            out.append(self._value(name, v))
        return '\n'.join(out) + '\n'
