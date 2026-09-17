"""Import selected footprints and native nets into an UNROUTED KiCad workspace.

Run with KiCad's Python (pcbnew). Run validate_kicad.py first. This deliberately
has no Edge.Cuts, tracks, vias or copper zones: coordinates are staging positions,
not the dimensions or placement of a replacement Saeco PCB. Missing mechanical
footprints are recorded, never guessed. Existing boards are not overwritten.
"""
import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as pcb
from check_front_panel import parse, one
from validate_kicad import ROOT, BOARDS, verify_netlist


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--footprints', type=Path, default=Path(os.environ.get(
        'KICAD10_FOOTPRINT_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')))
    args = parser.parse_args()
    for directory, name in BOARDS:
        base = ROOT/'hardware'/directory
        output = base/'kicad'/f'{name}.kicad_pcb'
        if output.exists():
            raise SystemExit(f'Refusing to overwrite editable PCB: {output}')
        xml = ET.parse(base/'validation/netlist.xml').getroot()
        verify_netlist(base, xml)
        schematic = parse((base/'kicad'/f'{name}.kicad_sch').read_text())
        root_uuid = one(schematic, 'uuid')[1]
        board = pcb.BOARD()
        nets, node_nets = {}, {}
        for net in xml.findall('nets/net'):
            name_net = net.attrib['name']
            obj = pcb.NETINFO_ITEM(board, name_net)
            board.Add(obj)
            nets[name_net] = obj
            for node in net.findall('node'):
                node_nets[(node.attrib['ref'], node.attrib['pin'])] = obj
        missing, libs, imported, passive_index = [], set(), {}, 0
        for c in xml.findall('components/comp'):
            ref, footprint = c.attrib['ref'], c.findtext('footprint')
            if not footprint:
                missing.append(ref)
                continue
            lib, fp_name = footprint.split(':')
            libs.add(lib)
            fp = pcb.FootprintLoad(str(args.footprints/(lib+'.pretty')), fp_name)
            if not fp:
                raise RuntimeError(f'Footprint not found: {footprint}')
            fp.SetReference(ref)
            fp.SetValue(c.findtext('value'))
            fp.SetFPIDAsString(footprint)
            path = pcb.KIID_PATH()
            path.push_back(pcb.KIID(root_uuid))
            path.push_back(pcb.KIID(c.findtext('tstamps')))
            fp.SetPath(path)
            for p in c.findall('property'):
                if p.attrib['name'] in ('manufacturer', 'mpn', 'lcsc', 'jlc_class', 'pcba_type'):
                    fp.SetField(p.attrib['name'], p.attrib['value'])
                    fp.GetField(p.attrib['name']).SetVisible(False)
            if ref == 'U101' or ref == 'U1':
                x, y = 55, 55
            elif ref == 'U201':
                x, y = 95, 55
            else:
                x, y = 40+(passive_index % 8)*10, 80+(passive_index//8)*8
                passive_index += 1
            fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
            fp.Value().SetVisible(False)
            fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8), pcb.FromMM(.8)))
            fp.Reference().SetTextThickness(pcb.FromMM(.12))
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y-2)))
            if ref.startswith('U'):
                fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y-15)))
            board.Add(fp)
            numbered = set()
            for pad in fp.Pads():
                number = pad.GetNumber()
                if not number:
                    continue
                numbered.add(number)
                pad.SetNet(node_nets[(ref, number)])
            expected_pins = {p.attrib['num'] for p in c.findall('units/unit/pins/pin')}
            assert numbered == expected_pins, f'Footprint/schematic pad mismatch: {ref}'
            imported[ref] = {'footprint': footprint, 'numbered_pads': len(numbered)}
        note = pcb.PCB_TEXT(board)
        note.SetText('UNROUTED COMPONENT STAGING / NOT FOR FABRICATION\nNo outline; connector footprints and mechanical dimensions pending')
        note.SetLayer(pcb.Dwgs_User)
        note.SetPosition(pcb.VECTOR2I(pcb.FromMM(75), pcb.FromMM(30)))
        note.SetTextSize(pcb.VECTOR2I(pcb.FromMM(1), pcb.FromMM(1)))
        note.SetTextThickness(pcb.FromMM(.15))
        board.Add(note)
        pcb.SaveBoard(str(output), board)
        # Reopen serialized data and independently check every physical pad/net.
        saved = pcb.LoadBoard(str(output))
        assert len(list(saved.GetFootprints())) == len(imported)
        for fp in saved.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNumber():
                    expected = node_nets[(fp.GetReference(), pad.GetNumber())].GetNetname()
                    assert pad.GetNetname() == expected
        (base/'kicad/fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(
            f' (lib (name "{lib}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty") (options "") (descr "KiCad standard library"))\n'
            for lib in sorted(libs))+')\n')
        (base/'validation/pcb-import.json').write_text(json.dumps({
            'status': 'unrouted_staging_not_fabricable', 'kicad_version': pcb.GetBuildVersion(),
            'imported': imported, 'missing_footprints': sorted(missing),
            'tracks': 0, 'outline': False, 'pad_nets_verified_after_reload': True
        }, indent=2)+'\n')
        print(f'{directory}: {len(imported)} footprints imported, {len(missing)} mechanical footprints pending.')


if __name__ == '__main__':
    main()
