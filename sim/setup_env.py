"""Prepare the simulator on this machine (macOS, Windows or Linux).

    python sim/setup_env.py           (Windows: py sim\\setup_env.py)

Creates .venv at the repository root, installs sim/requirements.txt in it
(zig cc as the C compiler), creates sim/.env from sim/.env.example if there is
none, and builds both firmware libraries to check the toolchain. Standard
library only; run it again after changing the requirements.
"""
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / '.venv'
PY = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
CHECK = '''
import sys
sys.path.insert(0, 'sim')
from osc_sim import firmware
print('compilador:', ' '.join(firmware.compiler() or ['ninguno']))
for target in ('stm32', 'esp32'):
    print('  ', target, '->', firmware.build(target).relative_to(firmware.ROOT))
'''


def run(*cmd, label=None):
    print('$', label or ' '.join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), cwd=ROOT, check=True)


def main():
    if sys.version_info < (3, 10):
        sys.exit(f'Hace falta Python 3.10 o posterior; este es {sys.version.split()[0]}.')
    if not PY.exists():
        print(f'Creando {VENV.relative_to(ROOT)}')
        venv.EnvBuilder(with_pip=True).create(VENV)
    run(PY, '-m', 'pip', 'install', '--disable-pip-version-check', '-q', '-r', ROOT / 'sim/requirements.txt')
    env = ROOT / 'sim/.env'
    if not env.exists():
        shutil.copy(ROOT / 'sim/.env.example', env)
        print('Creado sim/.env (todo comentado: ajústalo solo si hace falta)')
    run(PY, '-c', CHECK, label='compilando los dos firmwares')
    act = r'.venv\Scripts\Activate.ps1' if os.name == 'nt' else 'source .venv/bin/activate'
    print(f'''
Listo. Para usarlo:
  {act}
  python -m unittest discover -s tests/sim
  python tools/sim_panel.py          (http://127.0.0.1:8765/)''')


if __name__ == '__main__':
    main()
