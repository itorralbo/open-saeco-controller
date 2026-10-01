"""DC operating point of the resistor networks around a set of nets.

Nodal analysis over the board resistors plus extra elements (an external
sensor, an MCU internal pull). Rails with a known voltage are fixed nodes.
"""
from collections import deque


class Floating(Exception):
    """A net has no resistive path to any fixed voltage."""


class UnknownRail(Exception):
    """The network ends on a rail whose voltage the contract leaves open."""


def solve(system, nets, extra=(), inject=None, fixed=None):
    inject = dict(inject or {})
    fixed = {**system.voltages, **(fixed or {})}
    edges = {}
    for _, a, b, ohms in list(system.resistors()) + [(None, a, b, r) for a, b, r in extra]:
        if a != b and ohms:
            edges.setdefault(a, []).append((b, ohms))
            edges.setdefault(b, []).append((a, ohms))
    # Nets reachable through resistors, stopping at rails.
    unknown, boundary = set(), set()
    queue = deque(nets)
    while queue:
        g = queue.popleft()
        if g in fixed:
            boundary.add(g)
            continue
        if g in system.rails:
            raise UnknownRail(g)
        if g in unknown:
            continue
        unknown.add(g)
        queue.extend(n for n, _ in edges.get(g, []))
    if not boundary and not any(inject.get(g) for g in unknown):
        raise Floating(sorted(unknown))
    order = sorted(unknown)
    index = {g: i for i, g in enumerate(order)}
    n = len(order)
    m = [[0.0] * (n + 1) for _ in range(n)]
    for g in order:
        i = index[g]
        m[i][n] += inject.get(g, 0.0)
        for other, ohms in edges.get(g, []):
            m[i][i] += 1 / ohms
            if other in index:
                m[i][index[other]] -= 1 / ohms
            else:
                m[i][n] += fixed[other] / ohms
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-15:
            raise Floating([order[col]])
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col and m[r][col]:
                f = m[r][col] / m[col][col]
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    result = {g: m[index[g]][n] / m[index[g]][index[g]] for g in order}
    result.update({g: fixed[g] for g in boundary})
    return result
