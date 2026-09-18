"""Write the project footprints of the front panel into OpenSaeco.pretty.

SW_HRO_K2-1102SP-A4SC-04: Korean Hroparts 6x6x4.3 mm SMD tact switch, JLC C83916.
Land pattern from the EasyEDA footprint published on the JLCPCB part page
(2026-09-18): pads 1.40 x 2.30 mm at x = +/-2.25, y = +/-4.643 mm; left pads
(EasyEDA 1-2) and right pads (EasyEDA 3-4) are bridged inside the switch, so
each pair shares a number and is declared as a jumper group. Actuator 3.3 mm.
Run with KiCad's bundled Python.
"""
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT/'hardware/front-panel/kicad/OpenSaeco.pretty'
MM = pcb.FromMM


def shape(fp, kind, layer, width, a, b):
    item = pcb.PCB_SHAPE(fp)
    item.SetShape(kind)
    item.SetLayer(layer)
    item.SetWidth(MM(width))
    item.SetStart(pcb.VECTOR2I(MM(a[0]), MM(a[1])))
    item.SetEnd(pcb.VECTOR2I(MM(b[0]), MM(b[1])))
    fp.Add(item)


def switch():
    fp = pcb.FOOTPRINT(None)
    fp.SetFPIDAsString('OpenSaeco:SW_HRO_K2-1102SP-A4SC-04')
    fp.SetLibDescription('Tact switch 6x6 mm, H4.3 mm, SMD, Korean Hroparts K2-1102SP-A4SC-04 '
                         '(LCSC C83916); land pattern from the EasyEDA footprint of the JLCPCB part page')
    fp.SetKeywords('SPST tact switch 6x6 SMD HRO K2-1102SP')
    fp.SetAttributes(pcb.FP_SMD)
    fp.SetReference('REF**')
    fp.SetValue('K2-1102SP-A4SC-04')
    fp.Reference().SetPosition(pcb.VECTOR2I(0, MM(-6.9)))
    fp.Value().SetPosition(pcb.VECTOR2I(0, MM(6.9)))
    fp.Value().SetLayer(pcb.F_Fab)
    for number, x in (('1', -2.25), ('2', 2.25)):
        for y in (-4.643, 4.643):
            pad = pcb.PAD(fp)
            pad.SetNumber(number)
            pad.SetAttribute(pcb.PAD_ATTRIB_SMD)
            pad.SetShape(pcb.PAD_SHAPE_ROUNDRECT)
            pad.SetRoundRectRadiusRatio(0.2)
            pad.SetSize(pcb.VECTOR2I(MM(1.4), MM(2.3)))
            pad.SetLayerSet(pcb.PAD.SMDMask())
            pad.SetPosition(pcb.VECTOR2I(MM(x), MM(y)))
            fp.Add(pad)
    fp.SetDuplicatePadNumbersAreJumpers(True)
    shape(fp, pcb.SHAPE_T_RECT, pcb.F_Fab, 0.1, (-3, -3), (3, 3))
    circle = pcb.PCB_SHAPE(fp)
    circle.SetShape(pcb.SHAPE_T_CIRCLE)
    circle.SetLayer(pcb.F_Fab)
    circle.SetWidth(MM(0.1))
    circle.SetCenter(pcb.VECTOR2I(0, 0))
    circle.SetEnd(pcb.VECTOR2I(MM(1.65), 0))
    fp.Add(circle)
    # Silkscreen: body sides only, clear of the pads (pad edge at x = +/-2.95).
    for x in (-3.12, 3.12):
        shape(fp, pcb.SHAPE_T_SEGMENT, pcb.F_SilkS, 0.12, (x, -3.12), (x, 3.12))
    shape(fp, pcb.SHAPE_T_RECT, pcb.F_CrtYd, 0.05, (-3.25, -6.05), (3.25, 6.05))
    fp.Models().push_back(switch_model())
    return fp


def switch_model():
    """C&K PTS645 6x6x4.3 as a visual stand-in (same body and height), turned 90 degrees."""
    model = pcb.FP_3DMODEL()
    model.m_Filename = '${KICAD10_3DMODEL_DIR}/Button_Switch_SMD.3dshapes/SW_SPST_PTS645Sx43SMTR92.step'
    model.m_Rotation = pcb.VECTOR3D(0, 0, 90)
    return model


def main():
    io = pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP)
    if not LIB.exists():
        io.CreateLibrary(str(LIB))
    io.FootprintSave(str(LIB), switch())
    check = pcb.FootprintLoad(str(LIB), 'SW_HRO_K2-1102SP-A4SC-04')
    pads = sorted((p.GetNumber(), round(pcb.ToMM(p.GetPosition().x), 3), round(pcb.ToMM(p.GetPosition().y), 3))
                  for p in check.Pads())
    assert pads == [('1', -2.25, -4.643), ('1', -2.25, 4.643), ('2', 2.25, -4.643), ('2', 2.25, 4.643)], pads
    assert check.GetDuplicatePadNumbersAreJumpers()
    print(f'Wrote {LIB.name}/SW_HRO_K2-1102SP-A4SC-04.kicad_mod')


if __name__ == '__main__':
    main()
