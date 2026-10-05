"""Join both netlists, check them against the firmware contract and generate
board_pins.h for each MCU, sim/board-model.json and sim/board-report.md.

  python tools/build_board_model.py           regenerate the outputs
  python tools/build_board_model.py --check   fail on design errors or stale outputs
  python tools/build_board_model.py --as-if-fixed   errors left once the symbols
                                    follow sim/reference/pinouts.json (prints only)

Reads hardware/*/validation/netlist.xml: run tools/validate_kicad.py first
after editing a schematic. Not a substitute for KiCad ERC/DRC.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sim'))

from osc_sim import codegen  # noqa: E402
from osc_sim.checks import Checker  # noqa: E402
from osc_sim.model import System, fixed_symbols, load_contract  # noqa: E402

SEVERITY = {'error': 'Error', 'warning': 'Aviso', 'info': 'Nota'}


def report(checker):
    errors = [f for f in checker.findings if f.severity == 'error']
    warnings = [f for f in checker.findings if f.severity == 'warning']
    out = ['# Informe del modelo de placa', '',
           'Generado por `tools/build_board_model.py` a partir de los netlists de las dos placas y del',
           '[contrato de firmware](../firmware/common/signals.json). No sustituye a ERC/DRC.',
           'Qué comprueba cada regla: [README del simulador](README.md).', '',
           f'**{len(errors)} errores, {len(warnings)} avisos.**', '',
           '## Hallazgos', '']
    if not checker.findings:
        out.append('Ninguno.')
    for f in checker.findings:
        out.append(f'- **{SEVERITY[f.severity]}** `{f.code}`: {f.message}')
    out += ['', '## Señales', '',
            '| MCU | Señal | Red | Pad | Pin real | Periférico | Reset | Camino |',
            '|---|---|---|---|---|---|---|---|']
    for (mcu, name), r in sorted(checker.signals.items()):
        periph = r.periph or ''
        if r.af is not None:
            periph += f' AF{r.af}'
        path = ' → '.join(dict.fromkeys(p.split(':')[1] for p in r.path))
        pad = r.pad.pin if r.pad else '—'
        out.append(f'| {mcu} | {name} | `{r.net}` | {pad} | {r.pin or "—"} | {periph} | '
                   f'{r.reset_level or ""} | {path} |')
    out += ['', '## Entradas analógicas', '', '| Señal | Resultado |', '|---|---|']
    out += [f'| {name} | {text} |' for name, text in checker.analog]
    out += ['', '## Excitación en el peor caso', '',
            'Cada orden activa con los rails al mínimo (sim/osc_sim/drive.py): lo que cambia de estado y su margen '
            'frente al punto que garantiza el fabricante (sim/reference/devices.json).', '',
            '| Señal | Carga | Cadena |', '|---|---|---|']
    out += [f'| {name} | {load.split(":")[1]} | {text} |' for name, load, text in sorted(checker.drive_rows)]
    return '\n'.join(out) + '\n'


def outputs(checker):
    c = checker.c
    files = {c['mcus'][m]['header']: codegen.header(checker, m, c['mcus'][m]['header']) for m in c['mcus']}
    files['sim/board-model.json'] = json.dumps(codegen.model(checker), indent=1, ensure_ascii=False) + '\n'
    files['sim/board-report.md'] = report(checker)
    return files


def main(argv):
    check = '--check' in argv
    contract = load_contract(ROOT)
    if '--as-if-fixed' in argv:
        # What would still fail once every symbol matches its reference pinout.
        findings = Checker(System(contract, ROOT, boards=fixed_symbols(contract, ROOT))).run()
        for f in findings:
            print(f'{f.severity.upper()} {f.code}: {f.message}')
        return 1 if any(f.severity == 'error' for f in findings) else 0
    checker = Checker(System(contract, ROOT))
    findings = checker.run()
    stale = []
    for rel, text in outputs(checker).items():
        path = ROOT / rel
        if check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
    for f in findings:
        if f.severity != 'info':
            print(f'{f.severity.upper()} {f.code}: {f.message}')
    errors = sum(f.severity == 'error' for f in findings)
    print(f'{errors} errores, {sum(f.severity == "warning" for f in findings)} avisos; '
          'detalle en sim/board-report.md')
    if stale:
        print('Salidas desactualizadas, regenerar con python tools/build_board_model.py: ' + ', '.join(stale))
    return 1 if errors or stale else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
