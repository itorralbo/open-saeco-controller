"""Manufacturing regressions: handedness, numbered pads and stale audit guards."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_jlc_placements import fit
from jlc_placement_corrections import board_digest, corrected_placements, transform


class PlacementTests(unittest.TestCase):
    def test_rotated_connector_center(self):
        # PH8: origin at pin 1, seven 2 mm intervals, placed at 180 degrees.
        x, y, a = transform({'x': 99, 'y': -6.6, 'angle': 180, 'side': 'top'},
                            {'offset_x': 7, 'offset_y': 0, 'rotation': 180})
        self.assertAlmostEqual(x, 92)
        self.assertAlmostEqual(y, -6.6)
        self.assertEqual(a, 0)

    def test_source_center_rotated_into_board_axes(self):
        # IRM-30 pins sit off the body center; local +Y becomes board -X at 90.
        x, y, a = transform({'x': 50, 'y': -80, 'angle': 90, 'side': 'top'},
                            {'offset_x': 0, 'offset_y': 10.5, 'rotation': 0})
        self.assertEqual((round(x, 6), round(y, 6), a), (39.5, -80, 90))

    def test_bottom_rotation_and_offset_handedness(self):
        # Bouni's bottom convention: mirror on Y, then add the part correction.
        x, y, a = transform({'x': 10, 'y': -20, 'angle': 90, 'side': 'bottom'},
                            {'offset_x': 1, 'offset_y': 2, 'rotation': 270})
        self.assertEqual((round(x, 6), round(y, 6), a), (12, -19, 0))

    def test_reject_nonfinite_coordinates(self):
        with self.assertRaises(ValueError):
            transform({'x': math.nan, 'y': 0, 'angle': 0, 'side': 'top'},
                      {'offset_x': 0, 'offset_y': 0, 'rotation': 0})

    def test_pin_numbers_resolve_square_package(self):
        native = [dict(pin=str(i+1), x=x, y=y) for i, (x, y) in
                  enumerate([(-1, 1), (-1, -1), (1, -1), (1, 1)])]
        model = [{**p, 'x': -p['y'], 'y': p['x']} for p in native]
        result = fit(native, model)
        self.assertEqual(result['rotation'], 270)
        self.assertEqual(result['status'], 'geometry_match')
        self.assertEqual(result['max_error_mm'], 0)

    def test_incompatible_relay_cannot_be_fixed_by_rotation(self):
        native = [dict(pin=str(i), x=x, y=y) for i, x, y in
                  [(1, 10, 3.75), (3, -5, 3.75), (4, -10, 3.75),
                   (8, 10, -3.75), (6, -5, -3.75), (5, -10, -3.75)]]
        model = [dict(pin=str(i), x=x, y=y) for i, x, y in
                 [(1, -12.5, -3.75), (3, 7.5, -3.75), (4, 12.5, -3.75),
                  (8, -12.5, 3.75), (6, 7.5, 3.75), (5, 12.5, 3.75)]]
        result = fit(native, model)
        self.assertEqual(result['status'], 'review_geometry')
        self.assertEqual(result['max_error_mm'], 2.5)

    def test_duplicate_tails_checked_not_only_group_centroids(self):
        native = [{'pin': '1', 'x': -1, 'y': 0}, {'pin': '1', 'x': 1, 'y': 0},
                  {'pin': '2', 'x': -1, 'y': 3}, {'pin': '2', 'x': 1, 'y': 3}]
        model = [{**p, 'x': p['x']*2} for p in native]
        self.assertEqual(fit(native, model)['status'], 'review_geometry')

    def test_pending_never_silently_applies_best_fit(self):
        records = {'K701': {'native': {'x': 1, 'y': -2, 'angle': 0, 'side': 'top'},
                           'fit': {'status': 'review_geometry', 'rotation': 180}}}
        placements = [{'Ref': 'K701', 'PosX': 1, 'PosY': -2, 'Rot': 0, 'Side': 'top'}]
        with patch('jlc_placement_corrections.load_audit', return_value=records):
            with self.assertRaisesRegex(ValueError, 'Unresolved.*K701'):
                corrected_placements(Path('board'), placements)
            self.assertEqual(corrected_placements(Path('board'), placements, allow_unverified=True), placements)

    def test_stale_placement_rejected_even_with_review_flag(self):
        records = {'J2': {'native': {'x': 1, 'y': -2, 'angle': 0, 'side': 'top'},
                         'fit': {'status': 'geometry_match', 'rotation': 180,
                                 'offset_x': 7, 'offset_y': 0}}}
        with patch('jlc_placement_corrections.load_audit', return_value=records):
            with self.assertRaisesRegex(ValueError, 'does not match'):
                corrected_placements(Path('board'), [{'Ref': 'J2', 'PosX': 2, 'PosY': -2,
                                                      'Rot': 0, 'Side': 'top'}], allow_unverified=True)

    def test_digest_is_portable_but_detects_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory)/'a', Path(directory)/'b'
            a.write_bytes(b'(board\n  (pad 1)\n)\n')
            b.write_bytes(b'(board\r\n  (pad 1)\r\n)\r\n')
            self.assertEqual(board_digest(a), board_digest(b))
            b.write_bytes(b'(board\n  (pad 2)\n)\n')
            self.assertNotEqual(board_digest(a), board_digest(b))

    def test_committed_part_specific_rotations(self):
        report = json.loads((Path(__file__).resolve().parents[1]/
                             'hardware/assembly/placement-audit.json').read_text(encoding='utf-8'))
        rows = {r['reference']: r for r in report['rows'] if r['board'] == 'controller'}
        self.assertEqual(rows['U301']['fit']['rotation'], 270)
        self.assertEqual(rows['U303']['fit']['rotation'], 180)
        self.assertEqual(rows['U302']['fit']['rotation'], 180)
        self.assertEqual(rows['U203']['fit']['rotation'], 270)
        self.assertEqual(rows['U201']['fit']['rotation'], 0)
        self.assertEqual(rows['U201']['fit']['offset_y'], -.62)
        self.assertEqual(rows['L302']['fit']['status'], 'datasheet_checked')
        self.assertEqual(rows['L302']['fit']['rotation'], 180)

    def test_unexplained_pad_count_change_is_not_approved(self):
        native = [{'pin': '1', 'x': -2, 'y': 0}, {'pin': '1', 'x': -2, 'y': 2},
                  {'pin': '2', 'x': 2, 'y': 1}]
        model = [{'pin': '1', 'x': -2, 'y': 1}, {'pin': '2', 'x': 2, 'y': 1}]
        result = fit(native, model)
        self.assertEqual(result['status'], 'review_geometry')
        self.assertEqual(result['pad_count_mismatch'], ['1'])


if __name__ == '__main__':
    unittest.main()
