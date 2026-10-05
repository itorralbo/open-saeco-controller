"""Local web panel of the virtual machine (sim/README.md, F3).

  python tools/sim_panel.py [--port 8765] [--speed 1] [--corner nom|min|max]

Builds both firmwares for the host (needs a C compiler, $CC) and serves the
panel on http://127.0.0.1:8765/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sim'))

from osc_sim.panel import main  # noqa: E402

if __name__ == '__main__':
    main(sys.argv[1:])
