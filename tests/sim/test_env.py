"""sim/.env: local settings of the simulator (sim/.env.example).
Run: python -m unittest discover -s tests/sim
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'sim'))

from osc_sim import firmware  # noqa: E402


class Env(unittest.TestCase):
    def load(self, text, **shell):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, shell, clear=True):
            path = Path(d) / '.env'
            path.write_text(text, encoding='utf-8')
            firmware.load_env(path)
            return dict(os.environ)

    def test_values_comments_and_quotes(self):
        env = self.load('# comment\n\nCC = "C:\\Program Files\\gcc.exe"\nSDKROOT=/sdk\n# OFF=1\nEMPTY=\n')
        self.assertEqual(env, {'CC': 'C:\\Program Files\\gcc.exe', 'SDKROOT': '/sdk'})

    def test_the_shell_wins(self):
        self.assertEqual(self.load('CC=clang\n', CC='gcc')['CC'], 'gcc')

    def test_the_compiler_is_a_command(self):
        with mock.patch.dict(os.environ, {'CC': 'zig cc'}):
            self.assertEqual(firmware.compiler(), ['zig', 'cc'])
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / 'my gcc.exe'
            exe.write_bytes(b'')
            with mock.patch.dict(os.environ, {'CC': str(exe)}):
                self.assertEqual(firmware.compiler(), [str(exe)])  # a path with spaces stays whole


if __name__ == '__main__':
    unittest.main()
