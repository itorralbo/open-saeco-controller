"""Native ERC + independent netlist comparison. Requires KiCad 10.

Reports and native SVGs go under each board's validation/ directory. A clean
result applies only to the partial schematic, not its suitability for manufacture.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BOARDS = [('controller', 'controller-core-reva'), ('front-panel', 'front-panel-reva')]


def cli_path():
    candidate = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
    if not candidate:
        candidate = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    if not Path(candidate).is_file():
        raise SystemExit('KiCad CLI not found; set KICAD_CLI.')
    return candidate


def verify_netlist(base, root):
    expected = {c['reference']: c for c in json.loads((base/'design-nets.json').read_text())['components']}
    actual_components = {c.attrib['ref']: c for c in root.findall('components/comp')}
    assert set(actual_components) == set(expected), 'Native netlist component mismatch'
    actual = {ref: {} for ref in expected}
    for net in root.findall('nets/net'):
        for node in net.findall('node'):
            ref, pin = node.attrib['ref'], node.attrib['pin']
            if ref.startswith('#'):
                continue
            assert pin not in actual[ref], f'Duplicate native node {ref}.{pin}'
            nc = 'no_connect' in node.attrib.get('pintype', '').split('+')
            actual[ref][pin] = None if nc else net.attrib['name'].removeprefix('/')
    for ref, component in expected.items():
        assert actual[ref] == component['pins'], f'Native connectivity mismatch: {ref}'
        assert (actual_components[ref].findtext('footprint') or '') == component['footprint']
    return len(expected), sum(len(c['pins']) for c in expected.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-svg', action='store_true')
    args = parser.parse_args()
    cli = cli_path()
    version = subprocess.check_output([cli, 'version'], text=True).strip()
    for directory, name in BOARDS:
        base = ROOT/'hardware'/directory
        out = base/'validation'
        out.mkdir(exist_ok=True)
        sch = base/'kicad'/f'{name}.kicad_sch'
        for command in [
            ['sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations', '-o', str(out/'erc.json'), str(sch)],
            ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out/'netlist.xml'), str(sch)],
        ]:
            subprocess.run([cli]+command, check=True)
        report = json.loads((out/'erc.json').read_text())
        # KiCad 10 disables these optional checks in a new default project.
        # No project-specific suppression or violation exclusions are allowed.
        default_ignored = {'single_global_label', 'four_way_junction',
                           'simulation_model_issue', 'footprint_filter'}
        ignored = {c['key'] for c in report.get('ignored_checks', [])}
        assert ignored <= default_ignored, f'Additional ERC checks suppressed: {ignored}'
        assert not any(s['violations'] for s in report['sheets']), 'ERC violations present'
        count, pins = verify_netlist(base, ET.parse(out/'netlist.xml').getroot())
        if not args.no_svg:
            subprocess.run([cli, 'sch', 'export', 'svg', '--exclude-drawing-sheet', '-o', str(out)+'/', str(sch)], check=True)
            # KiCad emits trailing spaces in SVG markup. Normalize generated
            # artifacts so repository whitespace checks remain meaningful.
            svg_path = out/f'{name}.svg'
            svg_path.write_text('\n'.join(line.rstrip() for line in
                                           svg_path.read_text(encoding='utf-8').splitlines())+'\n',
                                encoding='utf-8')
        scope = ('La principal incluye el núcleo lógico, entrada protegida de 12 V aislados, '
                 'buck de 3,3 V, corte del frontal y acondicionamiento de NTC, caudalímetro '
                 'nivel de agua y tres contactos. No valida la fuente AC/DC ni las cargas.'
                 if directory == 'controller' else
                 'El frontal declara alimentación externa por J1; no valida la fuente ni la mecánica.')
        remaining = ('Los GPIO sin asignar llevan NC. J105–J109 usan huellas candidatas '
                     'XH/PH cotejadas con fotos; las dos vías de motor de JP16 permanecen '
                     'NC hasta incorporar el puente H. La salida de JP22 requiere ensayo.'
                     if directory == 'controller' else
                     'J1 ya tiene huella IDC; J2 y SW1–SW8 siguen pendientes de mecánica.')
        (out/'README.md').write_text(
            f'# Validación nativa — {name}\n\n'
            f'KiCad {version}. ERC: 0 errores y 0 avisos, sin exclusiones.\n'
            f'Netlist nativa cotejada: {count} componentes, {pins} pines.\n\n'
            'Configuración estándar de KiCad: no se ejecutan los controles opcionales\n'
            + ', '.join(sorted(ignored)) + '. No se han añadido supresiones.\n\n'
            f'Alcance: esquema parcial. {scope}\n'
            'No valida mecánica completa, selección eléctrica completa ni fabricación.\n'
            f'{remaining}\n'
            'Regenerar con `python3 tools/validate_kicad.py` desde la raíz.\n', encoding='utf-8')
        print(f'{name}: native ERC PASS; {count} components / {pins} pins match.')


if __name__ == '__main__':
    main()
