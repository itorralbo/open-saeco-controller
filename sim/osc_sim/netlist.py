"""Read a KiCad 'export version E' netlist (hardware/*/validation/netlist.xml)."""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class Pin:
    number: str
    name: str
    type: str
    net: str | None = None


@dataclass
class Component:
    ref: str
    value: str
    part: str
    fields: dict
    pins: dict = field(default_factory=dict)

    @property
    def mpn(self):
        return self.fields.get('mpn', '')

    def pin_by_name(self, name):
        hits = [p for p in self.pins.values() if p.name == name]
        assert len(hits) == 1, f'{self.ref}: pin {name!r} matches {len(hits)}'
        return hits[0]


@dataclass
class Board:
    name: str
    source: str
    components: dict
    nets: dict  # net name -> list of (ref, pin number)

    def pin(self, ref, number):
        return self.components[ref].pins[number]


def _net_name(raw):
    if raw.startswith('unconnected-'):
        return None
    return raw.lstrip('/')


def load(path, name):
    root = ET.parse(path).getroot()
    libparts = {}
    for lp in root.find('libparts'):
        pins = lp.find('pins')
        libparts[lp.get('part')] = {} if pins is None else {
            p.get('num'): (p.get('name') or '', p.get('type')) for p in pins}
    comps = {}
    # Footprints reserved but not fitted (KiCad DNP) are not in the circuit.
    unfitted = {c.get('ref') for c in root.find('components')
                if any(p.get('name') == 'dnp' for p in c.findall('property'))}
    for c in root.find('components'):
        if c.get('ref') in unfitted:
            continue
        part = c.find('libsource').get('part')
        fields = {f.get('name'): (f.text or '') for f in c.iter('field')}
        comp = Component(c.get('ref'), c.findtext('value'), part, fields)
        for num, (pname, ptype) in libparts[part].items():
            comp.pins[num] = Pin(num, pname, ptype)
        comps[comp.ref] = comp
    nets = {}
    for n in root.find('nets'):
        net = _net_name(n.get('name'))
        nodes = [(x.get('ref'), x.get('pin')) for x in n if x.get('ref') not in unfitted]
        for ref, num in nodes:
            comps[ref].pins[num].net = net
        if net is not None:
            assert net not in nets, f'{name}: duplicate net {net}'
            nets[net] = nodes
    return Board(name, root.find('design').findtext('source') or '', comps, nets)


_SI = {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3, '': 1.0,
       'k': 1e3, 'K': 1e3, 'M': 1e6, 'R': 1.0}


def resistance(value):
    """Ohms from a value field such as '10k / pull-up', '4.7k', '33', '2k4'."""
    head = value.split('/')[0].strip().replace(',', '.')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([pnuµmkKMR]?)(\d*)\s*(?:Ω|ohm)?', head)
    if not m:
        return None
    base, unit, tail = m.groups()
    if tail:  # 2k4 notation
        base = f'{base}.{tail}'
    return float(base) * _SI[unit]


def capacitance(value):
    """Farads from a value field such as '100nF / local', '4.7uF', '56pF'."""
    head = value.split('/')[0].strip().replace(',', '.')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([pnuµm]?)F?', head)
    return float(m.group(1)) * _SI[m.group(2)] if m else None
