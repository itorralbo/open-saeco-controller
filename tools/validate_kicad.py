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
    for default in ('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
                    'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'):
        if not candidate and Path(default).is_file():
            candidate = default
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
        scope = ('La principal incluye el núcleo lógico, USB-C de servicio, fuente aislada '
                 'IRM-30-24, selección de 24 V internos/externos, buck AP63200 de 24 V a 12 V, '
                 'buck de 3,3 V, sensores, puente H DRV8876 y etapa low-side de válvula. '
                 'Un relé G5RL normalmente abierto corta la fase de las cargas y solo se arma '
                 'mediante reset válido y orden explícita. Todavía no valida los drivers de '
                 'calentador, bomba o molino.'
                 if directory == 'controller' else
                 'El frontal declara alimentación externa por J1; no valida la fuente ni la mecánica.')
        remaining = ('Los GPIO sin asignar llevan NC. J105–J109 y J112–J113 usan huellas '
                     'candidatas XH/PH cotejadas con fotos. JP16 V1/V2 llegan al puente H y '
                     'JP3.1/JP3.2 a la etapa de válvula. J112 requiere una fuente de 24 V '
                     'aislada limitada; corriente, frenado, térmica, liberación de válvula y '
                     'la salida de JP22 requieren ensayo. El watchdog y sus tiempos también '
                     'requieren firmware y prueba de banco.'
                     if directory == 'controller' else
                     'Todas las posiciones tienen huella: SW1–SW7 HRO K2-1102SP-A4SC-04 '
                     '(OpenSaeco.pretty), J2 JST PH 8 y LED STBY en P7. Contorno y '
                     'taladros Ø8,4 desde mechanical-source.json.')
        extra = (('\nLa colocación alinea J104, J108, J107, J113, J109, J105 y J106 con '
                  'JP21, JP16, JP14, JP3, JP22, JP13 y JP5. JP8, JP19, JP24, JP17, '
                  'JP1 y JP9 son conectores obligatorios y ya tienen huella, con patrón de '
                  'patas provisional en los FASTON. El routing reproducible cubre USB, la alimentación '
                  'y el desacoplo del STM32, la entrada de red hasta PS701, K701 y RV701, la '
                  'salida de 24 V, el puente H del grupo, el supervisor con sus interlocks y el '
                  'mando del relé, la etapa de válvula, el lado de mazo de los sensores, el buck '
                  'de 24 V a 12 V, el buck de 3,3 V con su telemetría y un plano GND_UI en B.Cu: '
                  '589 segmentos y 126 vías. Las fases '
                  'de carga van duplicadas en las dos caras con cobre de 1 oz. '
                  'La barrera de 8 mm red/SELV es una regla DRC y una banda sin cobre; el '
                  'dominio de red es contiguo, reserva el disipador de calentador y bomba, y el '
                  'DRC de esta etapa tiene 0 infracciones y dos avisos intencionales de extremo '
                  'suelto, donde las filas de fallo y de corriente del puente H esperan las '
                  'señales del STM32. '
                  'Quedan 75 conexiones abiertas y tres diferencias de paridad, los taladros '
                  'mecánicos MH1–MH3.\n\n'
                  'La principal usa dos capas y clases explícitas para red, USB, alimentación, '
                  'conmutación y actuadores. La geometría USB sigue pendiente de verificar '
                  'con el stack-up de fabricación.\n')
                 if directory == 'controller' else '')
        (out/'README.md').write_text(
            f'# Validación nativa — {name}\n\n'
            f'KiCad {version}. ERC: 0 errores y 0 avisos, sin exclusiones.\n'
            f'Netlist nativa cotejada: {count} componentes, {pins} pines.\n\n'
            'Configuración estándar de KiCad: no se ejecutan los controles opcionales\n'
            + ', '.join(sorted(ignored)) + '. No se han añadido supresiones.\n\n'
            f'Alcance: esquema parcial. {scope}\n'
            'No valida mecánica completa, selección eléctrica completa ni fabricación.\n'
            f'{remaining}\n'
            f'{extra}'
            'Regenerar con `python3 tools/validate_kicad.py` desde la raíz.\n', encoding='utf-8')
        print(f'{name}: native ERC PASS; {count} components / {pins} pins match.')


if __name__ == '__main__':
    main()
