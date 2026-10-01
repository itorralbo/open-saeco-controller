"""Both boards and the harness as one graph of global nets.

A global net is 'board:NET'; the harness merges the nets on matching pins of
its two connectors. Every pin carries two names: the symbol's and the
physical one from sim/reference/pinouts.json, so the model behaves like the
PCB that would be built, not like the drawing.
"""
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from . import netlist, parts

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Node:
    board: str
    ref: str
    pin: str  # pad number

    def __str__(self):
        return f'{self.board}:{self.ref}.{self.pin}'


class System:
    def __init__(self, contract, root=ROOT, boards=None):
        self.contract = contract
        self.root = Path(root)
        self.reference = json.loads((self.root / 'sim/reference/pinouts.json').read_text(encoding='utf-8'))['parts']
        self.boards = boards or {name: netlist.load(self.root / path, name)
                                 for name, path in contract['boards'].items()}
        self._parent = {}
        for name, board in self.boards.items():
            for net in board.nets:
                self._parent[f'{name}:{net}'] = f'{name}:{net}'
        self.harness_pairs = []
        for h in contract.get('harness', []):
            (ba, ra), (bb, rb) = (x.split(':') for x in (h['a'], h['b']))
            assert h['map'] == '1:1'
            for n in range(1, h['pins'] + 1):
                pa = self.boards[ba].components[ra].pins.get(str(n))
                pb = self.boards[bb].components[rb].pins.get(str(n))
                self.harness_pairs.append((h['name'], n, ba, ra, pa, bb, rb, pb))
                if pa and pb and pa.net and pb.net:
                    self._union(f'{ba}:{pa.net}', f'{bb}:{pb.net}')
        self.members = {}
        for name, board in self.boards.items():
            for ref, comp in board.components.items():
                for num, pin in comp.pins.items():
                    if pin.net:
                        self.members.setdefault(self.gnet(name, pin.net), []).append(Node(name, ref, num))
        self.rails = {self.find(r) for r in contract.get('rails', {})}
        for g, nodes in self.members.items():
            if any(self.pin(n).type == 'power_in' for n in nodes):
                self.rails.add(g)
        self.voltages = {self.find(r): v for r, v in contract.get('rails', {}).items() if v is not None}

    # -- nets ---------------------------------------------------------------
    def _union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[max(ra, rb)] = min(ra, rb)

    def find(self, g):
        while self._parent[g] != g:
            self._parent[g] = self._parent[self._parent[g]]
            g = self._parent[g]
        return g

    def gnet(self, board, net):
        return self.find(f'{board}:{net}')

    def aliases(self, g):
        return sorted(k for k in self._parent if self.find(k) == g)

    def net_of(self, node):
        pin = self.pin(node)
        return self.gnet(node.board, pin.net) if pin.net else None

    # -- pins ---------------------------------------------------------------
    def comp(self, board, ref):
        return self.boards[board].components[ref]

    def pin(self, node):
        return self.comp(node.board, node.ref).pins[node.pin]

    def reference_names(self, board, ref):
        ref_part = self.reference.get(self.comp(board, ref).mpn)
        return None if ref_part is None else ref_part['pins']

    def physical_name(self, node):
        names = self.reference_names(node.board, node.ref)
        if names is None:
            return self.pin(node).name
        return names.get(node.pin, '?').split('|')[0]

    def node_by_name(self, board, ref, name):
        """Pad of a part by its physical name (or pad number)."""
        comp = self.comp(board, ref)
        if name in comp.pins:
            return Node(board, ref, name)
        hits = [Node(board, ref, n) for n in comp.pins
                if self.physical_name(Node(board, ref, n)) == name]
        if len(hits) != 1:
            raise KeyError(f'{board}:{ref}.{name} matches {len(hits)} pads')
        return hits[0]

    def endpoint(self, text):
        """'board:REF.PIN' -> Node (PIN is a pad number or physical name)."""
        board, rest = text.split(':', 1)
        ref, name = rest.split('.', 1)
        return self.node_by_name(board, ref, name)

    # -- traversal ----------------------------------------------------------
    def _steps(self, g, reverse):
        """Nets one part away from g, following SERIES parts and ARCS."""
        for node in self.members.get(g, []):
            comp = self.comp(node.board, node.ref)
            name = self.physical_name(node)
            if comp.part in parts.SERIES and len(comp.pins) == 2:
                other = next(n for n in comp.pins if n != node.pin)
                yield node, Node(node.board, node.ref, other)
                continue
            for a, b in parts.THROUGH.get(comp.part, ()):
                if node.pin in (a, b):
                    yield node, Node(node.board, node.ref, b if node.pin == a else a)
            for out, ins in parts.ARCS.get(comp.part, {}).items():
                if not reverse and name in ins:
                    yield node, self.node_by_name(node.board, node.ref, out)
                elif reverse and name == out:
                    for i in ins:
                        yield node, self.node_by_name(node.board, node.ref, i)

    def trace(self, start, reverse=False):
        """Breadth-first walk from net 'start'. Rails are reached, not crossed.

        Returns {net: (previous net, input node, output node)}.
        """
        seen = {start: None}
        queue = deque([start])
        while queue:
            g = queue.popleft()
            if g in self.rails and g != start:
                continue
            for a, b in self._steps(g, reverse):
                nxt = self.net_of(b)
                if nxt is not None and nxt not in seen:
                    seen[nxt] = (g, a, b)
                    queue.append(nxt)
        return seen

    def path(self, seen, target):
        hops = []
        while seen.get(target):
            prev, a, b = seen[target]
            hops.append((prev, a, b, target))
            target = prev
        return hops[::-1]

    def series_cluster(self, start):
        """Nets joined to 'start' through resistors only, without crossing rails."""
        seen, queue = {start}, deque([start])
        while queue:
            g = queue.popleft()
            for node in self.members.get(g, []):
                comp = self.comp(node.board, node.ref)
                if comp.part != 'R':
                    continue
                other = self.net_of(Node(node.board, node.ref, next(n for n in comp.pins if n != node.pin)))
                if other and other not in seen and other not in self.rails:
                    seen.add(other)
                    queue.append(other)
        return seen

    def resistors(self):
        for name, board in self.boards.items():
            for ref, comp in board.components.items():
                if comp.part == 'R':
                    a, b = (self.net_of(Node(name, ref, n)) for n in sorted(comp.pins))
                    if a and b:
                        yield f'{name}:{ref}', a, b, netlist.resistance(comp.value)

    def mcu_pins(self, mcu):
        board, ref = mcu['ref'].split(':')
        return [Node(board, ref, n) for n in self.comp(board, ref).pins]


def fixed_symbols(contract, root=ROOT):
    """The boards as if every symbol followed sim/reference/pinouts.json.

    Each net moves from the symbol's pad to the real pad of the same name, so
    the remaining checks show what is still wrong once the symbols are fixed.
    """
    root = Path(root)
    reference = json.loads((root / 'sim/reference/pinouts.json').read_text(encoding='utf-8'))['parts']
    boards = {name: netlist.load(root / path, name) for name, path in contract['boards'].items()}
    for board in boards.values():
        for comp in board.components.values():
            pads = reference.get(comp.mpn, {}).get('pins')
            if not pads:
                continue
            new = {}
            # Unique names first, then repeated ones (VSS, GND) in pad order.
            for num, pin in sorted(comp.pins.items(), key=lambda kv: (len(kv[1].name) == 0, int(kv[0]))):
                free = sorted((n for n, alts in pads.items()
                               if pin.name in alts.split('|') and n not in new), key=int)
                if not free:
                    raise ValueError(f'{comp.ref}: no reference pad left for {pin.name}')
                exact = [n for n in free if n == num]
                target = exact[0] if exact else free[0]
                new[target] = netlist.Pin(target, pin.name, pin.type, pin.net)
            comp.pins = new
        board.nets = {}
        for ref, comp in board.components.items():
            for num, pin in comp.pins.items():
                if pin.net:
                    board.nets.setdefault(pin.net, []).append((ref, num))
    return boards


def load_contract(root=ROOT):
    return json.loads((Path(root) / 'firmware/common/signals.json').read_text(encoding='utf-8'))
