"""Safely add newly selected front-panel footprints and refresh pad nets.

The outline and milled holes come from mechanical-source.json via
apply_front_panel_mechanics.py and must stay untouched; footprint coordinates
remain staging only. Existing editable footprints are preserved and unexpected
changes stop the script. Run with KiCad's bundled Python after validate_kicad.py.
"""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as pcb

from check_front_panel import parse, one
from validate_kicad import ROOT, verify_netlist

BASE = ROOT/'hardware/front-panel'
BOARD_PATH = BASE/'kicad/front-panel-reva.kicad_pcb'
FP_ROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
NEW_POSITIONS = {'J1': (130, 100)}
MECHANICS = json.loads((BASE/'mechanical-source.json').read_text(encoding='utf-8'))
EDGE_ITEMS = len(MECHANICS['outline_mm']['vertices'])+len(MECHANICS['holes'])


def main():
    xml = ET.parse(BASE/'validation/netlist.xml').getroot()
    verify_netlist(BASE, xml)
    schematic = parse((BASE/'kicad/front-panel-reva.kicad_sch').read_text())
    root_uuid = one(schematic, 'uuid')[1]
    board = pcb.LoadBoard(str(BOARD_PATH))
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]
    assert len(edges) == EDGE_ITEMS, 'Unexpected Edge.Cuts; run apply_front_panel_mechanics.py'

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
    existing = {fp.GetReference(): fp for fp in board.GetFootprints()}
    assert set(existing) <= set(desired), 'Unexpected footprint; preserve manual work'
    new_refs = set(desired)-set(existing)
    assert new_refs <= set(NEW_POSITIONS), f'No reviewed position for {sorted(new_refs)}'

    libs = set()
    for ref, component in desired.items():
        footprint = component.findtext('footprint')
        lib, name = footprint.split(':')
        libs.add(lib)
        if ref in existing:
            fp = existing[ref]
            assert fp.GetFPIDAsString() == footprint, f'Footprint changed for {ref}'
        else:
            fp = pcb.FootprintLoad(str(FP_ROOT/(lib+'.pretty')), name)
            if not fp:
                raise RuntimeError(f'Footprint not found: {footprint}')
            x, y = NEW_POSITIONS[ref]
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8), pcb.FromMM(.8)))
            fp.Reference().SetTextThickness(pcb.FromMM(.12))
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y-7)))
            board.Add(fp)
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

    pcb.SaveBoard(str(BOARD_PATH), board)
    check = pcb.LoadBoard(str(BOARD_PATH))
    assert len([d for d in check.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]) == EDGE_ITEMS
    by_ref = {fp.GetReference(): fp for fp in check.GetFootprints()}
    for ref, component in desired.items():
        for pad in by_ref[ref].Pads():
            if pad.GetNumber():
                assert pad.GetNetname() == node_nets[(ref, pad.GetNumber())].GetNetname()

    (BASE/'kicad/fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(
        f' (lib (name "{lib}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty") (options "") (descr "KiCad standard library"))\n'
        for lib in sorted(libs))+')\n')
    missing = sorted(c.attrib['ref'] for c in xml.findall('components/comp')
                     if not c.findtext('footprint'))
    (BASE/'validation/pcb-import.json').write_text(json.dumps({
        'status': 'unrouted_staging_not_fabricable',
        'kicad_version': pcb.GetBuildVersion(),
        'imported': {ref: {'footprint': c.findtext('footprint')}
                     for ref, c in desired.items()},
        'missing_footprints': missing,
        'new_connector_footprints_staged': sorted(new_refs),
        'tracks': len(list(check.GetTracks())),
        'outline': True,
        'edge_cuts_items': EDGE_ITEMS,
        'outline_source': 'hardware/front-panel/mechanical-source.json',
        'pad_nets_verified_after_reload': True,
    }, indent=2)+'\n')
    print(f'Front PCB synchronized: {len(desired)} footprints; '
          f'{len(missing)} mechanical footprints pending.')


if __name__ == '__main__':
    main()
