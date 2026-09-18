"""Read the partial main schematic and check MCU rails, debug and UART wiring.

This limited endpoint/label checker is not the KiCad parser, ERC or DRC.
"""
import json
from datetime import date
from pathlib import Path
from check_front_panel import parse, children, one, point

ROOT = Path(__file__).resolve().parents[1]


def read_connections(path):
    root = parse(path.read_text())
    assert not children(root, 'sheet'), 'Only single-sheet drafts supported'
    parent = {}

    def find(p):
        parent.setdefault(p, p)
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

    for wire in children(root, 'wire'):
        a, b = [point(p) for p in children(one(wire, 'pts'), 'xy')]
        parent[find(a)] = find(b)
    labels = {}
    for label in children(root, 'label'):
        p = point(one(label, 'at'))
        assert p in parent, 'Unattached label'
        labels.setdefault(find(p), set()).add(label[1])
    assert all(len(v) == 1 for v in labels.values()), 'Conflicting net labels'
    nc = {point(one(x, 'at')) for x in children(root, 'no_connect')}
    libs = {s[1]: s for s in children(one(root, 'lib_symbols'), 'symbol')}
    nets, fields = {}, {}
    for symbol in children(root, 'symbol'):
        props = {p[1]: p[2] for p in children(symbol, 'property')}
        ref = props['Reference']
        if ref.startswith('#'):
            continue
        assert ref not in nets, 'Duplicate reference'
        fields[ref] = props
        nets[ref] = {}
        at = one(symbol, 'at')
        assert float(at[3]) == 0 and not children(symbol, 'mirror')
        x, y = point(at)
        for unit in children(libs[one(symbol, 'lib_id')[1]], 'symbol'):
            for pin in children(unit, 'pin'):
                dx, dy = point(one(pin, 'at'))
                p = round(x+dx, 4), round(y-dy, 4)
                n = one(pin, 'number')[1]
                assert n not in nets[ref]
                if p in nc:
                    assert p not in parent
                    nets[ref][n] = None
                else:
                    assert p in parent and find(p) in labels, f'Dangling {ref}.{n}'
                    nets[ref][n] = next(iter(labels[find(p)]))
    return nets, fields


def main():
    base = ROOT/'hardware/controller'
    nets, fields = read_connections(base/'kicad/controller-core-reva.kicad_sch')
    v, g = '3V3_CORE', 'GND_UI'
    assert len(nets['U101']) == 64 and len(nets['U201']) == 41
    # Independent checks against ST DS12589 LQFP64 supply / debug pin table.
    for pin in (1,13,19,20,32,48,64):
        assert nets['U101'][str(pin)] == v, f'STM power pad {pin}'
    for pin in (12,18,31,47,63):
        assert nets['U101'][str(pin)] == g, f'STM ground pad {pin}'
    for pin, net in {7:'STM_NRST',43:'STM_TX_RAW',44:'ESP_TO_STM',49:'STM_SWDIO',
                     50:'STM_SWCLK',56:'STM_SWO',61:'STM_BOOT0',27:'UI_PWR_EN',
                     14:'NTC_ADC',15:'FLOW_TIM',8:'DOOR_CLOSED_N',9:'BU_PRESENT_N',
                     16:'WATER_LEVEL',10:'BU_WORK_N',17:'BREW_CURRENT_ADC',
                     23:'BREW_DIR_RAW',42:'BREW_PWM_RAW',58:'BREW_SLEEP_RAW',
                     59:'BREW_FAULT_N'}.items():
        assert nets['U101'][str(pin)] == net
    assert nets['U201']['2'] == v
    for pin in (1,40,41):
        assert nets['U201'][str(pin)] == g, f'ESP ground/EP pad {pin}'
    for pin in (28,29,30):
        assert nets['U201'][str(pin)] is None, 'Do not use octal PSRAM pins'
    for pin, net in {3:'ESP_EN',27:'ESP_BOOT0',10:'ESP_TX_RAW',11:'STM_TO_ESP',
                     4:'KEY_SDA',5:'KEY_SCL',6:'KEY_INT_N',7:'BL_RAW',12:'RST_RAW',
                     17:'DC_RAW',18:'CS_RAW',19:'MOSI_RAW',20:'SCLK_RAW',
                     13:'USB_DM_RAW',14:'USB_DP_RAW',23:'USB_VBUS_SENSE'}.items():
        assert nets['U201'][str(pin)] == net
    expected_link = ['3V3_UI',g,'LCD_SCLK',g,'LCD_MOSI',g,'LCD_CS_N','LCD_DC',
                     'LCD_RST_N','LCD_BL_PWM','KEY_SCL','KEY_SDA','KEY_INT_N',g,g,None]
    assert nets['J104'] == dict(zip(map(str, range(1,17)), expected_link))
    for ref,a,b in [('R211','STM_TX_RAW','STM_TO_ESP'),('R212','ESP_TX_RAW','ESP_TO_STM'),
                    ('R213','SCLK_RAW','LCD_SCLK'),('R214','MOSI_RAW','LCD_MOSI'),
                    ('R215','CS_RAW','LCD_CS_N'),('R216','DC_RAW','LCD_DC'),
                    ('R217','RST_RAW','LCD_RST_N'),('R218','BL_RAW','LCD_BL_PWM')]:
        assert nets[ref] == {'1':a,'2':b}
        assert fields[ref]['Value'] == '33'
    for ref, val, a, b in [('R101','10k',v,'STM_NRST'),('C101','100nF','STM_NRST',g),
                           ('R102','10k','STM_BOOT0',g),('R201','10k',v,'ESP_EN'),
                           ('C201','1uF','ESP_EN',g),('R202','10k',v,'ESP_BOOT0')]:
        assert nets[ref] == {'1':a,'2':b} and fields[ref]['Value'] == val
    for ref in [f'C{i}' for i in range(102,112)] + ['C202','C203']:
        assert nets[ref] == {'1':v,'2':g}, f'Decoupling missing at {ref}'
    assert nets['J101'] == {'1':'12V_ISO_RAW','2':g}
    assert nets['F301'] == {'1':'12V_ISO_RAW','2':'12V_FUSED'}
    assert nets['D301'] == {'2':'12V_FUSED','1':'12V_PROTECTED'}
    assert nets['D302'] == {'2':g,'1':'12V_PROTECTED'}
    assert nets['U301'] == {'1':v,'2':'12V_PROTECTED','3':'12V_PROTECTED',
                            '6':'BST_NODE','5':'SW_NODE','4':g}
    assert nets['C303'] == {'1':'BST_NODE','2':'SW_NODE'}
    assert nets['L301'] == {'1':'SW_NODE','2':v}
    for ref in ('C304','C305','C306'):
        assert nets[ref] == {'1':v,'2':g}
    assert nets['U302'] == {'1':v,'2':g,'3':'UI_PWR_EN','6':'3V3_UI',
                            '5':'3V3_UI','4':'UI_RISE'}
    assert nets['R301'] == {'1':v,'2':'UI_PWR_EN'}
    assert nets['C307'] == {'1':'UI_RISE','2':g}
    assert nets['C308'] == {'1':v,'2':g}
    assert nets['C309'] == {'1':'3V3_UI','2':g}
    assert nets['J105'] == {'1':'NTC_RAW','2':g}
    assert nets['R401'] == {'1':v,'2':'NTC_RAW'}
    assert nets['R402'] == {'1':'NTC_RAW','2':'NTC_ADC'}
    assert nets['C401'] == {'1':'NTC_ADC','2':g}
    assert nets['J106'] == {'1':'FLOW_RAW','2':g,'3':'12V_PROTECTED'}
    assert nets['R403'] == {'1':v,'2':'FLOW_RAW'}
    assert nets['R404'] == {'1':'FLOW_RAW','2':'FLOW_TIM'}
    assert nets['C402'] == {'1':'FLOW_TIM','2':g}
    assert nets['J107'] == {'1':'DOOR_RAW','2':g}
    assert nets['R405'] == {'1':v,'2':'DOOR_RAW'}
    assert nets['R406'] == {'1':'DOOR_RAW','2':'DOOR_CLOSED_N'}
    assert nets['C403'] == {'1':'DOOR_CLOSED_N','2':g}
    assert nets['J108'] == {'1':'BREW_OUT1','2':'BREW_OUT2',
                            '3':'BU_BRIDGE','4':'BU_BRIDGE','5':g,
                            '6':'BU_PRESENT_RAW','7':g,'8':'BU_WORK_RAW'}
    for prefix, raw, conditioned in [('PRES','BU_PRESENT_RAW','BU_PRESENT_N'),
                                     ('WORK','BU_WORK_RAW','BU_WORK_N')]:
        refs = {'PRES':('R407','R408','C404'), 'WORK':('R409','R410','C405')}[prefix]
        assert nets[refs[0]] == {'1':v,'2':raw}
        assert nets[refs[1]] == {'1':raw,'2':conditioned}
        assert nets[refs[2]] == {'1':conditioned,'2':g}
    assert nets['J109'] == {'1':v,'2':'WATER_RAW','3':g}
    assert nets['R411'] == {'1':'WATER_RAW','2':'WATER_LEVEL'}
    assert nets['C406'] == {'1':'WATER_LEVEL','2':g}
    assert nets['J110'] == {
        'A1':g,'A4':'USB_VBUS','A5':'USB_CC1','A6':'USB_DP_PORT',
        'A7':'USB_DM_PORT','A8':None,'A9':'USB_VBUS','A12':g,'SH':g,
        'B1':g,'B4':'USB_VBUS','B5':'USB_CC2','B6':'USB_DP_PORT',
        'B7':'USB_DM_PORT','B8':None,'B9':'USB_VBUS','B12':g}
    assert nets['U203'] == {'1':'USB_DP_PORT','2':g,'3':'USB_DM_PORT',
                            '6':'USB_DP_DEVICE','5':'USB_VBUS','4':'USB_DM_DEVICE'}
    assert nets['R221'] == {'1':'USB_DM_DEVICE','2':'USB_DM_RAW'}
    assert nets['R222'] == {'1':'USB_DP_DEVICE','2':'USB_DP_RAW'}
    assert nets['R223'] == {'1':'USB_CC1','2':g}
    assert nets['R224'] == {'1':'USB_CC2','2':g}
    assert nets['R225'] == {'1':'USB_VBUS','2':'USB_VBUS_SENSE'}
    assert nets['R226'] == {'1':'USB_VBUS_SENSE','2':g}
    assert nets['C204'] == {'1':'USB_VBUS_SENSE','2':g}
    assert nets['C205'] == {'1':'USB_VBUS','2':g}
    assert nets['F302'] == {'1':'USB_VBUS','2':'USB_VBUS_FUSED'}
    assert nets['J111'] == {'1':'USB_VBUS_FUSED','2':'USB_BENCH_ENABLE'}
    assert nets['D303'] == {'2':'USB_BENCH_ENABLE','1':'12V_PROTECTED'}
    assert nets['J112'] == {'1':'24V_BREW_RAW','2':g}
    assert nets['F303'] == {'1':'24V_BREW_RAW','2':'24V_BREW_FUSED'}
    assert nets['D304'] == {'2':'24V_BREW_FUSED','1':'24V_BREW'}
    assert nets['C501'] == {'1':'24V_BREW','2':g}
    assert nets['C502'] == {'1':'24V_BREW','2':g}
    assert nets['U501'] == {
        '1':'BREW_EN_DRV','2':'BREW_DIR_DRV','3':'BREW_SLEEP_DRV',
        '4':'BREW_FAULT_N','5':'BREW_VREF','6':'BREW_CURRENT_ADC','7':g,
        '8':'BREW_OUT1','9':g,'10':'BREW_OUT2','11':'24V_BREW',
        '12':'BREW_VCP','13':'BREW_CPH','14':'BREW_CPL','15':g,'16':g,'17':g}
    assert nets['C503'] == {'1':'BREW_VCP','2':'24V_BREW'}
    assert nets['C504'] == {'1':'BREW_CPH','2':'BREW_CPL'}
    for ref, a, b in [('R501','BREW_PWM_RAW','BREW_EN_DRV'),
                      ('R502','BREW_EN_DRV',g),('R503','BREW_DIR_RAW','BREW_DIR_DRV'),
                      ('R504','BREW_DIR_DRV',g),('R505','BREW_SLEEP_RAW','BREW_SLEEP_DRV'),
                      ('R506','BREW_SLEEP_DRV',g),('R507',v,'BREW_FAULT_N'),
                      ('R508',v,'BREW_VREF'),('R509','BREW_VREF',g),
                      ('R510','BREW_CURRENT_ADC',g),('C505','BREW_VREF',g),
                      ('C506','BREW_CURRENT_ADC',g)]:
        assert nets[ref] == {'1':a,'2':b}
    for ref, footprint, lcsc in [
            ('J110','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12','C165948'),
            ('U203','Package_TO_SOT_SMD:SOT-23-6','C7519'),
            ('F302','Fuse:Fuse_1206_3216Metric','C163512'),
            ('J112','Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal','C163035'),
            ('U501','Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm','C575551'),
            ('C501','Capacitor_SMD:CP_Elec_6.3x7.7','C176683'),
            ('C504','Capacitor_SMD:C_0603_1608Metric','C77571')]:
        assert fields[ref]['Footprint'] == footprint and fields[ref]['lcsc'] == lcsc
    for ref, footprint, lcsc in [
            ('J105','Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal','C163035'),
            ('J106','Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal','C157928'),
            ('J107','Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal','C163035'),
            ('J108','Connector_JST:JST_XH_S8B-XH-A_1x08_P2.50mm_Horizontal','C157914'),
            ('J109','Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal','C545716')]:
        assert fields[ref]['Footprint'] == footprint and fields[ref]['lcsc'] == lcsc
    exported = json.loads((base/'design-nets.json').read_text())
    assert nets == {c['reference']:c['pins'] for c in exported['components']}

    catalog = json.loads((ROOT/'hardware/assembly/parts-catalog.json').read_text())['parts']
    by_code = {p['lcsc']:p for p in catalog.values()}
    for board, path in [('main', base/'kicad/controller-core-reva.kicad_sch'),
                        ('front', ROOT/'hardware/front-panel/kicad/front-panel-reva.kicad_sch')]:
        _, props = read_connections(path)
        matched = 0
        for ref, p in props.items():
            code = p.get('lcsc')
            if not code:
                assert ref.startswith(('J','SW')), f'Unsourced electronic part {board}:{ref}'
                continue
            part = by_code[code]
            assert p['mpn'] == part['mpn'] and p['Footprint'] == part['footprint']
            assert part['stock_observed'] > 0, f'No stock at last check: {code}'
            checked = date.fromisoformat(part['stock_checked_on'])
            assert (date.today()-checked).days <= 7, f'Stale stock observation: {code}'
            matched += 1
        print(f'{board}: {matched}/{len(props)} positions have MPN + JLC code; remainder mechanical TBD.')
    print('Core rail, UART, debug, passive inputs and sourcing checks pass. '
          'This checker does not run native ERC/DRC.')


if __name__ == '__main__':
    main()
