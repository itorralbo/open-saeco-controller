"""Add newly sourced controller footprints and refresh pad nets in-place.

This is intentionally narrower than KiCad's interactive update-from-schematic:
it only operates on the controller board, preserves all placement and mechanics,
and refuses unexpected or changed footprints. New power parts receive provisional
staging coordinates. It never creates tracks, vias, zones or manufacturing data.
Run with KiCad's bundled Python/pcbnew after validate_kicad.py.
"""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as pcb

from check_front_panel import parse, one
from validate_kicad import ROOT, verify_netlist

BASE = ROOT/'hardware/controller'
BOARD_PATH = BASE/'kicad/controller-core-reva.kicad_pcb'
FP_ROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
LOCAL_FP_ROOT = BASE/'kicad/OpenSaeco.pretty'

# Provisional placement, clear of the current ESP antenna area. J104 occupies
# the original front-panel cable corner. J105-J109 are staged away from the
# accepted mounting holes; final edge positions still depend on harness reach.
NEW_POSITIONS = {
    'J101': (92, 6), 'J102': (70, 116), 'J103': (90, 116), 'J104': (5.5, 6),
    'F301': (36, 15), 'D301': (44, 15), 'D302': (52, 15),
    'C301': (60, 15), 'C302': (65, 15), 'U301': (58, 25),
    'C303': (64, 25), 'L301': (50, 25), 'C304': (42, 23),
    'C305': (42, 28), 'C306': (45, 34), 'U302': (75, 25),
    'R301': (75, 18), 'C307': (67, 32), 'C308': (69, 18),
    'C309': (84, 23),
    'R401': (10, 75), 'R402': (15, 75), 'C401': (20, 75),
    'R403': (10, 82), 'R404': (15, 82), 'C402': (20, 82),
    'R405': (10, 89), 'R406': (15, 89), 'C403': (20, 89),
    'R407': (10, 96), 'R408': (15, 96), 'C404': (20, 96),
    'R409': (10, 103), 'R410': (15, 103), 'C405': (20, 103),
    'R411': (50, 116), 'C406': (56, 116),
    'J105': (5, 124), 'J106': (16, 124), 'J107': (30, 124),
    'J109': (42, 124), 'J108': (107.5, 124),
    'J110': (25, 4.45), 'U203': (25, 13.5),
    'R221': (80, 58), 'R222': (80, 64),
    'R223': (18, 17), 'R224': (24, 17),
    'R225': (18, 28), 'R226': (24, 28), 'C204': (30, 28),
    'C205': (30, 17), 'F302': (18, 22), 'J111': (24, 22),
    'D303': (30, 22),
    'J112': (130, 6), 'F303': (108, 14), 'D304': (116, 14),
    'C501': (130, 21), 'C502': (120, 21), 'U501': (130, 43),
    'C503': (136, 38), 'C504': (136, 45),
    'R501': (126, 56), 'R502': (134, 56),
    'R503': (126, 64), 'R504': (134, 64),
    'R505': (110, 51), 'R506': (117, 51),
    'R507': (110, 57), 'R508': (117, 57),
    'R509': (110, 63), 'C505': (117, 63),
    'R510': (110, 69), 'C506': (117, 69),
    'J113': (32, 58), 'F304': (26, 82), 'D305': (32, 82),
    'D306': (34, 86), 'U502': (29, 98), 'Q501': (37, 98),
    'R511': (27, 106), 'R512': (34, 106),
    'R513': (24, 111), 'R514': (30, 111),
    'C507': (25, 88), 'C508': (29, 88),
    'U601': (118, 80), 'U602': (128, 80),
    'R601': (118, 88), 'R602': (124, 88),
    'C601': (130, 88), 'C602': (136, 88),
    'R603': (118, 96), 'R604': (124, 96),
    'R701': (86, 12), 'R702': (82, 12), 'R703': (78, 12), 'C701': (74, 12),
    'R704': (105, 7), 'R705': (111, 7), 'R706': (117, 7), 'C702': (123, 7),
    'J114': (106, 101),
    'J115': (59.04, 120.8), 'J117': (91.02, 120.8),
    'J118': (106.04, 121.3),
    'F701': (128, 52), 'RV701': (119, 55), 'F702': (128, 27),
    'PS701': (105, 89), 'J121': (66, 104),
    'U303': (53, 103), 'L302': (61, 103),
    'C310': (49, 108), 'C311': (57, 108), 'C312': (63, 108),
    'C313': (57, 99), 'R302': (66, 100), 'R303': (66, 104),
    'C314': (66, 108),
    'U603': (50, 79), 'C603': (54, 79), 'Q701': (48, 84),
    'J116': (80.5, 124.2), 'J119': (121.5, 124.0), 'J120': (128.0, 124.0),
    'R801': (44, 80), 'R802': (44, 84), 'D701': (57, 84),
    'K701': (54, 92),
}
# Reviewed package swaps. The new footprint takes the old position and rotation;
# layout_controller_pcb.py then places it. Pads are re-netted below as usual.
FOOTPRINT_REPLACEMENTS = {
    'U201': ('RF_Module:ESP32-S3-WROOM-1', 'RF_Module:ESP32-S3-WROOM-1U'),
}
NEW_ORIENTATIONS = {'J110': 180, 'F701': 90, 'F702': 90, 'PS701': 180}
REFERENCE_POSITIONS = {
    'J110': (34, 4), 'U203': (32, 10.5), 'R224': (34, 20),
    'R221': (76.5, 58), 'R222': (76.5, 64),
    'C501': (130, 26), 'U501': (130, 34),
    'C503': (136, 34), 'C504': (136, 49),
    'J113': (32, 50.5), 'U502': (29, 94), 'Q501': (37, 94),
    'C508': (27, 91.5), 'D306': (34, 90),
    'U601': (118, 76), 'U602': (128, 76),
}


def load_footprint(footprint):
    lib, name = footprint.split(':')
    root = LOCAL_FP_ROOT if lib == 'OpenSaeco' else FP_ROOT/(lib+'.pretty')
    fp = pcb.FootprintLoad(str(root), name)
    if not fp:
        raise RuntimeError(f'Footprint not found: {footprint}')
    return fp


def main():
    xml = ET.parse(BASE/'validation/netlist.xml').getroot()
    verify_netlist(BASE, xml)
    schematic = parse((BASE/'kicad/controller-core-reva.kicad_sch').read_text())
    root_uuid = one(schematic, 'uuid')[1]
    board = pcb.LoadBoard(str(BOARD_PATH))
    assert len([d for d in board.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]) == 4
    before_holes = {fp.GetReference(): fp.GetPosition() for fp in board.GetFootprints()
                    if fp.GetReference().startswith('MH')}
    assert set(before_holes) == {'MH1', 'MH2', 'MH3'}

    nets = {str(name): net for name, net in board.GetNetsByName().items()}
    node_nets = {}
    for net in xml.findall('nets/net'):
        name = net.attrib['name']
        if name not in nets:
            obj = pcb.NETINFO_ITEM(board, name)
            board.Add(obj)
            nets[name] = obj
        for node in net.findall('node'):
            node_nets[(node.attrib['ref'], node.attrib['pin'])] = nets[name]

    desired = {c.attrib['ref']: c for c in xml.findall('components/comp')
               if c.findtext('footprint')}
    existing = {fp.GetReference(): fp for fp in board.GetFootprints()
                if not fp.GetReference().startswith('MH')}
    before_placement = {ref: (fp.GetPosition(), fp.GetOrientationDegrees())
                        for ref, fp in existing.items()}
    assert set(existing) <= set(desired), 'Unexpected electrical footprint; preserve manual work'
    new_refs = set(desired)-set(existing)
    assert new_refs <= set(NEW_POSITIONS), f'No reviewed placement for {sorted(new_refs-set(NEW_POSITIONS))}'

    libs = set()
    for ref, component in desired.items():
        footprint = component.findtext('footprint')
        lib, _ = footprint.split(':')
        libs.add(lib)
        is_new = ref not in existing
        if not is_new:
            fp = existing[ref]
            if fp.GetFPIDAsString() != footprint:
                assert FOOTPRINT_REPLACEMENTS.get(ref) == (fp.GetFPIDAsString(), footprint), \
                    f'Footprint changed for {ref}'
                old = fp
                fp = load_footprint(footprint)
                fp.SetPosition(old.GetPosition())
                fp.SetOrientationDegrees(old.GetOrientationDegrees())
                fp.Reference().SetTextSize(old.Reference().GetTextSize())
                fp.Reference().SetTextThickness(old.Reference().GetTextThickness())
                board.Remove(old)
                board.Add(fp)
        else:
            fp = load_footprint(footprint)
            x, y = NEW_POSITIONS[ref]
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8), pcb.FromMM(.8)))
            fp.Reference().SetTextThickness(pcb.FromMM(.12))
            board.Add(fp)
        if is_new and ref in NEW_POSITIONS:
            x, y = NEW_POSITIONS[ref]
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y-3)))
        if is_new and ref in NEW_ORIENTATIONS:
            fp.SetOrientationDegrees(NEW_ORIENTATIONS[ref])
        if is_new and ref in REFERENCE_POSITIONS:
            x, y = REFERENCE_POSITIONS[ref]
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
        # Library jumpers may be marked BOM-excluded. The schematic remains the
        # source of assembly status, so keep board/schematic attributes in parity.
        fp.SetExcludedFromBOM(False)
        fp.SetReference(ref)
        fp.SetValue(component.findtext('value'))
        fp.SetFPIDAsString(footprint)
        path = pcb.KIID_PATH()
        path.push_back(pcb.KIID(root_uuid))
        path.push_back(pcb.KIID(component.findtext('tstamps')))
        fp.SetPath(path)
        fp.Value().SetVisible(False)
        for prop in component.findall('property'):
            if prop.attrib['name'] in ('manufacturer','mpn','lcsc','jlc_class','pcba_type'):
                fp.SetField(prop.attrib['name'], prop.attrib['value'])
                fp.GetField(prop.attrib['name']).SetVisible(False)
        numbered = {pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        expected = {p.attrib['num'] for p in component.findall('units/unit/pins/pin')}
        assert numbered == expected, f'Footprint/schematic pad mismatch: {ref}'
        for pad in fp.Pads():
            if pad.GetNumber():
                pad.SetNet(node_nets[(ref, pad.GetNumber())])

    for item in board.GetDrawings():
        if (new_refs and isinstance(item, pcb.PCB_TEXT)
                and item.GetText().startswith('UNROUTED COMPONENT STAGING')):
            item.SetText('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\n'
                         'Rev A mechanics accepted; low-voltage connectors and power staged; routing pending')
            item.SetPosition(pcb.VECTOR2I(pcb.FromMM(75), pcb.FromMM(5.5)))
    pcb.SaveBoard(str(BOARD_PATH), board)

    check = pcb.LoadBoard(str(BOARD_PATH))
    assert len([d for d in check.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]) == 4
    after = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for ref, position in before_holes.items():
        assert after[ref].GetPosition() == position, f'Mounting hole moved: {ref}'
    for ref, (position, orientation) in before_placement.items():
        assert after[ref].GetPosition() == position, f'Existing footprint moved: {ref}'
        assert after[ref].GetOrientationDegrees() == orientation, f'Existing footprint rotated: {ref}'
    for ref, component in desired.items():
        fp = after[ref]
        for pad in fp.Pads():
            if pad.GetNumber():
                expected = node_nets[(ref, pad.GetNumber())].GetNetname()
                assert pad.GetNetname() == expected, f'Pad net mismatch: {ref}.{pad.GetNumber()}'

    def fp_lib_entry(lib):
        if lib == 'OpenSaeco':
            return (' (lib (name "OpenSaeco") (type "KiCad") '
                    '(uri "${KIPRJMOD}/OpenSaeco.pretty") (options "") '
                    '(descr "Open Saeco project footprints"))\n')
        return (f' (lib (name "{lib}") (type "KiCad") '
                f'(uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty") (options "") '
                f'(descr "KiCad standard library"))\n')
    (BASE/'kicad/fp-lib-table').write_text(
        '(fp_lib_table (version 7)\n'+''.join(fp_lib_entry(lib) for lib in sorted(libs))+')\n')
    missing = sorted(c.attrib['ref'] for c in xml.findall('components/comp')
                     if not c.findtext('footprint'))
    (BASE/'validation/pcb-import.json').write_text(json.dumps({
        'status': ('new_footprints_staged_not_fabricable' if new_refs else
                   'synchronized_preserving_existing_placement_not_fabricable'),
        'kicad_version': pcb.GetBuildVersion(),
        'imported': {ref: {'footprint': c.findtext('footprint'),
                          'numbered_pads': len({p.attrib['num'] for p in c.findall('units/unit/pins/pin')})}
                     for ref, c in desired.items()},
        'missing_footprints': missing,
        'newly_staged_footprints': sorted(new_refs),
        'tracks': len(list(check.GetTracks())),
        'outline': True,
        'mounting_holes_preserved': sorted(before_holes),
        'pad_nets_verified_after_reload': True,
    }, indent=2)+'\n')
    print(f'Controller PCB synchronized: {len(desired)} electrical footprints; '
          f'{len(new_refs)} new footprints staged; '
          f'{len(missing)} connector footprints pending.')


if __name__ == '__main__':
    main()
