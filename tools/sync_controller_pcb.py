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
}


def load_footprint(footprint):
    lib, name = footprint.split(':')
    fp = pcb.FootprintLoad(str(FP_ROOT/(lib+'.pretty')), name)
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
    assert set(existing) <= set(desired), 'Unexpected electrical footprint; preserve manual work'
    new_refs = set(desired)-set(existing)
    assert new_refs <= set(NEW_POSITIONS), f'No reviewed placement for {sorted(new_refs-set(NEW_POSITIONS))}'

    libs = set()
    for ref, component in desired.items():
        footprint = component.findtext('footprint')
        lib, _ = footprint.split(':')
        libs.add(lib)
        if ref in existing:
            fp = existing[ref]
            assert fp.GetFPIDAsString() == footprint, f'Footprint changed for {ref}'
        else:
            fp = load_footprint(footprint)
            x, y = NEW_POSITIONS[ref]
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8), pcb.FromMM(.8)))
            fp.Reference().SetTextThickness(pcb.FromMM(.12))
            board.Add(fp)
        if ref in NEW_POSITIONS:
            x, y = NEW_POSITIONS[ref]
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y-3)))
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
        if isinstance(item, pcb.PCB_TEXT) and item.GetText().startswith('UNROUTED COMPONENT STAGING'):
            item.SetText('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\n'
                         'Rev A mechanics accepted; low-voltage connectors and power staged; routing pending')
            item.SetPosition(pcb.VECTOR2I(pcb.FromMM(75), pcb.FromMM(5.5)))
    pcb.SaveBoard(str(BOARD_PATH), board)

    check = pcb.LoadBoard(str(BOARD_PATH))
    assert len([d for d in check.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]) == 4
    after = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for ref, position in before_holes.items():
        assert after[ref].GetPosition() == position, f'Mounting hole moved: {ref}'
    for ref, component in desired.items():
        fp = after[ref]
        for pad in fp.Pads():
            if pad.GetNumber():
                expected = node_nets[(ref, pad.GetNumber())].GetNetname()
                assert pad.GetNetname() == expected, f'Pad net mismatch: {ref}.{pad.GetNumber()}'

    (BASE/'kicad/fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(
        f' (lib (name "{lib}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty") (options "") (descr "KiCad standard library"))\n'
        for lib in sorted(libs))+')\n')
    missing = sorted(c.attrib['ref'] for c in xml.findall('components/comp')
                     if not c.findtext('footprint'))
    (BASE/'validation/pcb-import.json').write_text(json.dumps({
        'status': 'unrouted_staging_not_fabricable',
        'kicad_version': pcb.GetBuildVersion(),
        'imported': {ref: {'footprint': c.findtext('footprint'),
                          'numbered_pads': len({p.attrib['num'] for p in c.findall('units/unit/pins/pin')})}
                     for ref, c in desired.items()},
        'missing_footprints': missing,
        'staged_footprints': sorted(set(NEW_POSITIONS) & set(desired)),
        'tracks': len(list(check.GetTracks())),
        'outline': True,
        'mounting_holes_preserved': sorted(before_holes),
        'pad_nets_verified_after_reload': True,
    }, indent=2)+'\n')
    print(f'Controller PCB synchronized: {len(desired)} electrical footprints; '
          f'{len(set(NEW_POSITIONS) & set(desired))} reviewed footprints staged; '
          f'{len(missing)} connector footprints pending.')


if __name__ == '__main__':
    main()
