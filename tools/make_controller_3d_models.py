"""Write simplified VRML bodies for the controller parts that lack a 3D model.

These are render stand-ins: boxes for bodies, pins and tabs, with no fillets,
latches, markings or internal detail. The plan view follows each footprint's
outline and pads; heights come from the maker's figure where one is recorded
(SCOPE below says which) and are otherwise estimated from the part family.
They are fit for renders and for judging clearances by eye, not for MCAD
export, enclosure fit or creepage checks. OpenSaeco.3dshapes/README.md, written
by this script, lists the source of every dimension.

Footprints from OpenSaeco.pretty get the model in the library and on the
board. KiCad-library footprints whose stock model is missing from KiCad 10.0
get a board-only override, so re-importing one of them from the library drops
it until this script runs again. U501 takes the closest stock STEP instead.

Run with KiCad's Python from inside tools/.
"""
import re
from pathlib import Path

import pcbnew as pcb

BASE = Path(__file__).resolve().parents[1]/'hardware/controller/kicad'
PRETTY = BASE/'OpenSaeco.pretty'
SHAPES = BASE/'OpenSaeco.3dshapes'
BOARD_PATH = BASE/'controller-core-reva.kicad_pcb'
MODEL_DIR = '${KIPRJMOD}/OpenSaeco.3dshapes'

NYLON = (0.93, 0.91, 0.84)
TE_NYLON = (0.90, 0.88, 0.80)
RED_PBT = (0.72, 0.12, 0.10)
TIN = (0.80, 0.80, 0.82)
BRASS = (0.83, 0.76, 0.52)
BLACK = (0.10, 0.10, 0.11)
STEEL = (0.75, 0.76, 0.78)
SOLDER_MASK = (0.08, 0.10, 0.12)
GLASS = (0.78, 0.86, 0.88)
COPPER = (0.72, 0.45, 0.20)
METAL = (TIN, BRASS, STEEL, COPPER)


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box in footprint millimetres (y grows south, z up)."""
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


def prism(outline, z0, z1):
    """Convex outline (footprint mm) extruded from z0 to z1."""
    return [(x, y, z0) for x, y in outline], [(x, y, z1) for x, y in outline]


def vrml(parts):
    """parts: list of (colour, solid); solid is a box (8 points) or a prism."""
    out = ['#VRML V2.0 utf8\n']
    for colour, solid in parts:
        if isinstance(solid, tuple):
            bottom, top = solid
            n = len(bottom)
            pts = bottom+top
            faces = [list(range(n-1, -1, -1)), list(range(n, 2*n))]
            faces += [[i, (i+1) % n, n+(i+1) % n, n+i] for i in range(n)]
        else:
            pts = solid
            faces = [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4],
                     [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        # KiCad reads VRML in 0.1 in units with y pointing north.
        coords = ', '.join(f'{x/2.54:.5f} {-y/2.54:.5f} {z/2.54:.5f}' for x, y, z in pts)
        # Negating y mirrors the solid, so every face is wound back outward.
        index = ', '.join(', '.join(map(str, reversed(f)))+', -1' for f in faces)
        r, g, b = colour
        shininess = 0.6 if colour in METAL else 0.15
        out.append(
            'Shape {\n'
            f'  appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} '
            f'specularColor {0.5 if shininess > 0.5 else 0.1} {0.5 if shininess > 0.5 else 0.1} '
            f'{0.5 if shininess > 0.5 else 0.1} shininess {shininess} transparency 0 }} }}\n'
            f'  geometry IndexedFaceSet {{ solid TRUE coord Coordinate {{ point [ {coords} ] }} '
            f'coordIndex [ {index} ] }}\n'
            '}\n')
    return ''.join(out)


def hr_a2506(n):
    """HR A2506WV-0nP: shrouded 2.50 mm wafer, open to the north flange side.
    Plan from the footprint (10 x 4.90 mm for three circuits, chamfer at the
    south-east corner); height estimated at 6.0 mm, XH-like."""
    x0, x1, y0, y1, h, wall = -2.5, 2.5*(n-1)+2.5, -3.05, 1.85, 6.0, 0.8
    parts = [(NYLON, prism([(x0, y0), (x1, y0), (x1, y1-0.8), (x1-0.8, y1), (x0, y1)], 0, 1.2))]
    parts += [(NYLON, box(x0, x1-0.8, y1-wall, y1, 1.2, h)),          # rib wall
              (NYLON, box(x0, x0+wall, y0, y1, 1.2, h)),
              (NYLON, box(x1-wall, x1, y0, y1-0.8, 1.2, h)),
              (NYLON, box(x0, x1, y0, y0+0.6, 1.2, 3.0))]             # low flange
    for i in range(n):
        x = 2.5*i
        parts.append((TIN, box(x-0.32, x+0.32, -0.32, 0.32, -3.2, h-0.6)))
    return parts


def leoco(n, pitch, x0, x1):
    """LEOCO 3941/5001 friction-lock header: flat back wall to the north, free
    pins and the lock ramp to the south. Plan 9.6 mm deep from the footprint;
    height estimated at 11.0 mm, VH-like."""
    y0, y1, h = -4.8, 4.8, 11.0
    parts = [(NYLON, box(x0, x1, y0, 3.6, 0, 2.2)),
             (NYLON, box(x0, x1, y0, y0+1.4, 2.2, h)),
             (NYLON, box(x0+1.0, x1-1.0, 3.6, y1, 0, 4.5))]           # lock ramp
    for i in range(n - 1):
        x = pitch*i + pitch/2
        parts.append((NYLON, box(x-0.5, x+0.5, y0+1.4, -1.0, 2.2, h-1.0)))  # separators
    for i in range(n):
        x = pitch*i
        parts.append((TIN, box(x-0.57, x+0.57, -0.57, 0.57, -3.5, h-0.8)))
    return parts


def rast5(n):
    """TE 1971845-n RAST 5 tab header: 14.9 mm wide, 12.8 mm tall housing
    (TE drawing C-1971845), 6.3 x 0.8 mm tabs on 5 mm pitch in a column,
    each with two staggered tails into the board."""
    half = (5*n + 2.3)/2
    x0, x1, y0, y1, h, wall = -7.45, 7.45, -half, half, 12.8, 1.0
    parts = [(TE_NYLON, box(x0, x1, y0, y1, 0, 3.0)),
             (TE_NYLON, box(x0, x0+wall, y0, y1, 3.0, h)),
             (TE_NYLON, box(x1-wall, x1, y0, y1, 3.0, h)),
             (TE_NYLON, box(x0+wall, x1-wall, y0, y0+wall, 3.0, h)),
             (TE_NYLON, box(x0+wall, x1-wall, y1-wall, y1, 3.0, h))]
    text = (PRETTY/f'TE_RAST5_1971845-{n}_1x0{n}_P5.00mm_Vertical.kicad_mod').read_text()
    for i in range(n):
        y = 5*i - 5*(n-1)/2
        parts.append((TIN, box(-3.15, 3.15, y-0.4, y+0.4, 3.0, h-1.0)))
    for num, x, y in re.findall(r'\(pad "(\d*)" \w+ \w+ \(at (\S+) ([^)\s]+)\)', text):
        x, y = float(x), float(y)
        if num:
            parts.append((TIN, box(x-0.4, x+0.4, y-0.4, y+0.4, -3.0, 3.0)))
        else:
            parts.append((TE_NYLON, box(x-1.1, x+1.1, y-1.1, y+1.1, -2.5, 0)))   # polarizing post
    return parts


def faston():
    """TE 63824-1 FASTON .250 PCB tab with two legs on 5.08 mm; the tab rises
    about 8 mm above the board (estimated)."""
    return [(BRASS, box(-0.41, 0.41, -3.18, 3.18, 1.0, 8.9)),
            (BRASS, box(-0.41, 0.41, -3.96, 3.96, 0, 1.0)),
            (BRASS, box(-0.41, 0.41, -2.94, -2.14, -3.0, 0)),
            (BRASS, box(-0.41, 0.41, 2.14, 2.94, -3.0, 0))]


def esp32_s3_wroom_1u():
    """ESP32-S3-WROOM-1U: 18 x 19.2 mm from the footprint, 3.2 mm tall per the
    Espressif datasheet (not re-checked); 0.8 mm module board, shield over the
    south part, U.FL where the footprint marks it."""
    return [(SOLDER_MASK, box(-9, 9, -9.6, 9.6, 0, 0.8)),
            (STEEL, box(-8.4, 8.4, -5.3, 9.0, 0.8, 3.2)),
            (STEEL, box(4.7, 7.3, -8.44, -5.84, 0.8, 1.4)),
            (STEEL, box(5.5, 6.5, -7.64, -6.64, 1.4, 2.05))]


def relay_g5rl():
    """Omron G5RL-1A-E: 29 x 12.7 mm case from the silkscreen outline, 15.7 mm
    tall per the series figure (not checked against the drawing)."""
    parts = [(BLACK, box(-14.5, 14.5, -6.35, 6.35, 0.3, 15.7))]
    for x, y in ((10, -3.75), (10, 3.75), (-5, -3.75), (-5, 3.75), (-10, -3.75), (-10, 3.75)):
        parts.append((TIN, box(x-0.5, x+0.5, y-0.25, y+0.25, -3.5, 0.3)))
    return parts


def meanwell_irm30():
    """Mean Well IRM-30: 69.5 x 39 x 24 mm potted case (footprint, from the
    IRM-30 drawing), four 1 mm pins."""
    parts = [(BLACK, box(-34.75, 34.75, -19.5, 19.5, 0, 24.0))]
    for x, y in ((-30.75, -15), (-30.75, -9.5), (30.75, -15), (30.75, -6)):
        parts.append((TIN, box(x-0.5, x+0.5, y-0.5, y+0.5, -4.0, 0)))
    return parts


def usb_c_vertical():
    """HRO TYPE-C-31-D-06: 8.94 x 3.16 mm shell, 6.40 mm tall (footprint, from
    the HRO drawing), mouth on top, four 0.95 mm shell legs."""
    parts = [(STEEL, box(-4.47, 4.47, -1.58, 1.58, 0, 6.4)),
             (BLACK, box(-4.1, 4.1, -1.25, 1.25, 6.38, 6.42))]
    for x, y in ((-2.4, -2.15), (2.4, -2.15), (-2.4, 2.15), (2.4, 2.15)):
        parts.append((STEEL, box(x-0.3, x+0.3, y-0.2, y+0.2, -0.95, 0)))
    return parts


def fuse_axial_vertical():
    """Littelfuse 215 axial (0215xxx.XEP) on end: 5.5 mm body, 21.5 mm long,
    1.5 mm above the board, caps at both ends and the far lead bent back
    down to pad 2 at 5.08 mm (215 datasheet, revised 01/12/17)."""
    import math
    ring = [(2.75*math.cos(2*math.pi*k/16), 2.75*math.sin(2*math.pi*k/16)) for k in range(16)]
    z0, z1 = 1.5, 23.0
    return [(GLASS, prism(ring, z0+1.0, z1-1.0)),
            (TIN, prism(ring, z0, z0+1.0)),
            (TIN, prism(ring, z1-1.0, z1)),
            (TIN, box(-0.33, 0.33, -0.33, 0.33, -1.5, z0)),
            (TIN, box(-0.33, 5.41, -0.33, 0.33, z1+1.0, z1+1.66)),
            (TIN, box(4.75, 5.41, -0.33, 0.33, -1.5, z1+1.66))]


def inductor(sx, sy, h, pads):
    """Shielded SMD power inductor drawn as a block on its two terminals."""
    parts = [(BLACK, box(-sx/2, sx/2, -sy/2, sy/2, 0.05, h))]
    for x0, x1, y0, y1 in pads:
        parts.append((TIN, box(x0, x1, y0, y1, 0, 0.3)))
    return parts


def wr_mm(n):
    """Wurth WR-MM female PCB connector, n contacts at 1.27 mm stagger: a
    22.32 x 5 mm, 4.2 mm base and a 20.85 x 4 mm, 1.9 mm upper block with the
    receptacles (Wurth drawing 690367181672); latch and cavities omitted."""
    xc, yc, pl = -(n-1)*1.27/2, 1.27, (n-1)*1.27
    parts = [(RED_PBT, box(xc-11.16, xc+11.16, yc-2.5, yc+2.5, 0, 4.2)),
             (RED_PBT, box(xc-10.425, xc+10.425, yc-2.0, yc+2.0, 4.2, 6.1))]
    for i in range(n):
        x, y = -1.27*i, 0 if i % 2 == 0 else 2.54
        parts.append((TIN, box(x-0.28, x+0.28, y-0.2, y+0.2, -2.9, 0.4)))
    assert abs(pl-19.05) < 1e-9 or n != 16
    return parts


def fuseholder_111():
    """Two Littelfuse 111 clips 20 mm apart holding a 5 x 20 mm glass fuse.
    Clip outline from the footprint; 9 mm clip height and the fuse axis at
    6.5 mm are estimated."""
    parts = []
    for x0 in (-0.5, 14.5):
        parts += [(TIN, box(x0, x0+6, -2.65, -2.35, 0, 9.0)),
                  (TIN, box(x0, x0+6, 2.35, 2.65, 0, 9.0)),
                  (TIN, box(x0, x0+6, -2.65, 2.65, 0, 0.4))]
        for x in (x0+0.5, x0+5.5):
            parts.append((TIN, box(x-0.4, x+0.4, -0.25, 0.25, -3.5, 0)))
    parts += [(GLASS, box(0.5, 19.5, -2.3, 2.3, 4.2, 8.8)),
              (STEEL, box(0, 5.2, -2.45, 2.45, 4.05, 8.95)),
              (STEEL, box(14.8, 20, -2.45, 2.45, 4.05, 8.95))]
    return parts


def soic10w_dvg():
    """TI DVG0010A: 7.5 x 10.3 mm body, 2.65 mm max height (TI drawing
    4226847/C); two wide input leads on the west, eight on the east."""
    parts = [(BLACK, box(-3.75, 3.75, -5.15, 5.15, 0.1, 2.5))]
    for y in (-2.54, 2.54):
        parts.append((TIN, box(-5.2, -3.75, y-2.11, y+2.11, 0, 0.25)))
    for n in range(8):
        y = 4.445-n*1.27
        parts.append((TIN, box(3.75, 5.2, y-0.2, y+0.2, 0, 0.25)))
    return parts


# footprint: (library, parts or stock STEP, scope note for the README)
SCOPE = {
    'HR_A2506WV-02P_1x02_P2.50mm_Vertical': ('OpenSaeco', hr_a2506(2),
        'Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH).'),
    'HR_A2506WV-03P_1x03_P2.50mm_Vertical': ('OpenSaeco', hr_a2506(3),
        'Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH).'),
    'HR_A2506WV-05P_1x05_P2.50mm_Vertical': ('OpenSaeco', hr_a2506(5),
        'Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH).'),
    'LEOCO_3941P03_1x03_P3.96mm_Vertical': ('OpenSaeco', leoco(3, 3.96, -1.99, 9.91),
        'Planta del plano LEOCO 394105S; altura de 11 mm y rampa estimadas (familia VH).'),
    'LEOCO_5001P02_1x02_P5.00mm_Vertical': ('OpenSaeco', leoco(2, 5.0, -2.5, 7.5),
        'Planta del plano LEOCO 500101S; altura de 11 mm y rampa estimadas.'),
    'TE_RAST5_1971845-3_1x03_P5.00mm_Vertical': ('OpenSaeco', rast5(3),
        'Carcasa 17,3 x 14,9 x 12,8 mm del plano TE C-1971845; paredes y lengüetas simplificadas.'),
    'TE_RAST5_1971845-4_1x04_P5.00mm_Vertical': ('OpenSaeco', rast5(4),
        'Carcasa 22,3 x 14,9 x 12,8 mm del plano TE C-1971845; paredes y lengüetas simplificadas.'),
    'Wurth_WR-MM_690367181672_2x08_P1.27mm_Vertical': ('OpenSaeco', wr_mm(16),
        'Cuerpo de 22,32 x 5 x 6,1 mm del plano Würth 690367181672; sin pestillo ni cavidades.'),
    'TE_FASTON_63824-1_Tab_6.35mm_Vertical': ('OpenSaeco', faston(),
        'Lengüeta de 6,35 x 0,81 mm del plano TE C-63824; altura de unos 9 mm estimada.'),
    'Relay_SPST_Omron_G5RL-1A-E-TV8': ('OpenSaeco', relay_g5rl(),
        'Planta de 29 x 12,7 mm de la serigrafía; 15,7 mm de alto según la serie G5RL, sin cotejar con el plano.'),
    'MeanWell_IRM-30_THT': ('OpenSaeco', meanwell_irm30(),
        'Caja de 69,5 x 39 x 24 mm del plano Mean Well IRM-30.'),
    'USB_C_Receptacle_HRO_TYPE-C-31-D-06_Vertical': ('OpenSaeco', usb_c_vertical(),
        'Carcasa de 8,94 x 3,16 x 6,40 mm del plano HRO; sin contactos internos.'),
    'TI_DVG0010A_SOIC-10W_HV': ('OpenSaeco', soic10w_dvg(),
        'Cuerpo de 7,5 x 10,3 mm y 2,65 mm de alto del plano TI 4226847/C; patas simplificadas.'),
    'Fuse_Littelfuse_0215_5x20mm_Axial_Vertical_P5.08mm': ('OpenSaeco', fuse_axial_vertical(),
        'Cuerpo de 5,5 x 21,5 mm de pie, 1,5 mm sobre la placa, de la hoja Littelfuse 215; patilla doblada simplificada.'),
    'ESP32-S3-WROOM-1U': ('RF_Module', esp32_s3_wroom_1u(),
        'Planta de 18 x 19,2 mm de la huella; 3,2 mm de alto según la hoja Espressif, sin cotejar; blindaje y U.FL simplificados.'),
    'L_Bourns-SRN6028': ('Inductor_SMD', inductor(6.0, 6.0, 2.8,
                          [(-3.0, -1.7, -2.85, 2.85), (1.7, 3.0, -2.85, 2.85)]),
        'Bloque de 6,0 x 6,0 x 2,8 mm según la serie Bourns SRN6028, sin cotejar con el plano.'),
    'L_Bourns_SRP7028A_7.3x6.6mm': ('Inductor_SMD', inductor(7.3, 6.6, 2.8,
                          [(-3.65, -1.9, -1.75, 1.75), (1.9, 3.65, -1.75, 1.75)]),
        'Planta de 7,3 x 6,6 mm de la huella; 2,8 mm de alto según la serie SRP7028A, sin cotejar.'),
    'Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal':
        ('Fuse', fuseholder_111(),
         'Clips en la planta de la huella con fusible de 5 x 20 mm; altura de 9 mm estimada.'),
    'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm':
        ('Package_SO', '${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/'
                       'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm.step',
         'STEP de KiCad del mismo cuerpo 4,4 x 5 mm; solo cambia la pastilla térmica, que no se ve.'),
}

README = """# Modelos 3D de sustitución

Los genera `tools/make_controller_3d_models.py`; no se editan a mano.

**Alcance:** son cuerpos simplificados (cajas para cuerpo, pines y lengüetas,
sin redondeos, pestillos, marcas ni detalle interior) para los renders y para
juzgar holguras a ojo. No sirven para exportar a CAD mecánico, comprobar el
encaje en la carcasa ni medir distancias de aislamiento. La planta sigue la
huella; las alturas marcadas como estimadas no proceden de un plano.

Las huellas de `OpenSaeco.pretty` llevan el modelo en la biblioteca y en la
placa. Las de la biblioteca de KiCad cuyo modelo falta en KiCad 10.0 lo llevan
solo en la placa: si se vuelven a importar desde la biblioteca, hay que repetir
el script.

| Huella | Placa | Origen de las medidas |
|---|---|---|
"""


def main():
    SHAPES.mkdir(exist_ok=True)
    paths = {}
    for name, (lib, parts, _) in SCOPE.items():
        if isinstance(parts, str):
            paths[(lib, name)] = parts
            continue
        (SHAPES/f'{name}.wrl').write_text(vrml(parts))
        path = paths[(lib, name)] = f'{MODEL_DIR}/{name}.wrl'
        if lib != 'OpenSaeco':
            continue
        mod = PRETTY/f'{name}.kicad_mod'
        text = re.sub(r'\n  \(model "[^"]*"(?:\n    [^\n]*)*\n  \)', '', mod.read_text())
        text = text.rstrip()
        assert text.endswith(')')
        text = (text[:-1].rstrip()+'\n'
                f'  (model "{path}"\n'
                '    (offset (xyz 0 0 0))\n    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )\n)\n')
        mod.write_text(text)

    board = pcb.LoadBoard(str(BOARD_PATH))
    fitted = {}
    for fp in board.GetFootprints():
        key = (fp.GetFPID().GetLibNickname().wx_str(), fp.GetFPID().GetLibItemName().wx_str())
        if key not in paths:
            continue
        fp.Models().clear()
        model = pcb.FP_3DMODEL()
        model.m_Filename = paths[key]
        fp.Models().push_back(model)
        fitted.setdefault(key[1], []).append(fp.GetReference())
    pcb.SaveBoard(str(BOARD_PATH), board)
    assert set(fitted) == set(SCOPE), f'Unused models: {set(SCOPE) - set(fitted)}'

    rows = [f'| `{name}` | {", ".join(sorted(fitted[name]))} | {note} |'
            for name, (_, _, note) in SCOPE.items()]
    (SHAPES/'README.md').write_text(README+'\n'.join(rows)+'\n')
    print(f'{len(SCOPE)} models fitted to {sum(map(len, fitted.values()))} footprints.')


if __name__ == '__main__':
    main()
