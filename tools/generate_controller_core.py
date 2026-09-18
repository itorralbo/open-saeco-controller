"""Main-board logic core plus protected 12V-to-3V3 power stage.

Uses the same draft drawing primitives as the front-panel generator. Both outputs
remain review-only. Unassigned MCU pins marked NC must be reassigned as sheets grow.
"""
import generate_front_panel as d

# ST DS12589 rev 6, figure 10 / table 12, LQFP64 (not a development board).
STM_PINS = (
    'VBAT PC13 PC14 PC15 PF0 PF1 NRST PC0 PC1 PC2 PC3 VSS VDD PA0 PA1 PA2 '
    'PA3 VSSA VREF+ VDDA PA4 PA5 PA6 PA7 PC4 PC5 PB0 PB1 PB2 PB10 VSS VDD '
    'PB11 PB12 PB13 PB14 PB15 PC6 PC7 PC8 PC9 PA8 PA9 PA10 PA11 PA12 VSS VDD '
    'PA13 PA14 PA15 PC10 PC11 PC12 PD2 PB3 PB4 PB5 PB6 PB7 PB8 PB9 VSS VDD'
).split()
# Espressif WROOM-1 module pads, including exposed ground pad 41.
ESP_PINS = (
    'GND 3V3 EN IO4 IO5 IO6 IO7 IO15 IO16 IO17 IO18 IO8 IO19 IO20 IO3 IO46 '
    'IO9 IO10 IO11 IO12 IO13 IO14 IO21 IO47 IO48 IO45 IO0 IO35 IO36 IO37 '
    'IO38 IO39 IO40 IO41 IO42 RXD0 TXD0 IO2 IO1 GND EP_GND'
).split()


def chip(kind, names):
    split = (len(names)+1)//2
    pins = []
    for index, name in enumerate(names):
        side = -1 if index < split else 1
        row = index if side < 0 else index-split
        typ = ('power_in' if name in ('VBAT','VDD','VSS','VSSA','VDDA','VREF+','GND','3V3','EP_GND')
               else 'input' if name in ('EN', 'NRST') else 'bidirectional')
        pins.append((str(index+1), name, typ, side*17.78,
                     (split-1)*1.905-row*3.81, 0 if side < 0 else 180))
    d.DEFS[kind] = (pins, 15.24, split*1.905+1.27)


def power_symbols():
    """Symbols follow the orderable devices' top-view pin numbering."""
    d.DEFS['AP63203'] = ([
        ('1', 'FB', 'input', -7.62, 3.81, 0),
        ('2', 'EN', 'input', -7.62, 0, 0),
        ('3', 'VIN', 'power_in', -7.62, -3.81, 0),
        ('6', 'BST', 'passive', 7.62, 3.81, 180),
        ('5', 'SW', 'power_out', 7.62, 0, 180),
        ('4', 'GND', 'power_in', 7.62, -3.81, 180),
    ], 5.08, 6.35)
    d.DEFS['TPS22918'] = ([
        ('1', 'VIN', 'power_in', -7.62, 3.81, 0),
        ('2', 'GND', 'power_in', -7.62, 0, 0),
        ('3', 'ON', 'input', -7.62, -3.81, 0),
        ('6', 'VOUT', 'power_out', 7.62, 3.81, 180),
        ('5', 'QOD', 'passive', 7.62, 0, 180),
        ('4', 'CT', 'output', 7.62, -3.81, 180),
    ], 5.08, 6.35)
    two = [('1', '1', 'passive', -5.08, 0, 0),
           ('2', '2', 'passive', 5.08, 0, 180)]
    # Diode order is A=2 on the left, K=1 on the right, matching KiCad convention.
    d.DEFS['DIODE'] = ([('2', 'A', 'passive', -5.08, 0, 0),
                         ('1', 'K', 'passive', 5.08, 0, 180)], 2.54, 1.5)
    d.DEFS['FUSE'] = (two, 2.54, 1.5)
    d.DEFS['L'] = (two, 2.54, 1.5)


def main():
    d.PROJECT = 'controller-core-reva'
    d.OUT = d.ROOT/'hardware/controller'
    d.objects.clear(); d.components.clear(); d.svg.clear()
    chip('STM32G431RB', STM_PINS)
    chip('ESP32S3WROOM1', ESP_PINS)
    power_symbols()
    for n in (2, 3, 4, 6, 8):
        d.DEFS[f'J{n}'] = (d.connector(n), 5.08, n*1.905+1.27)
    v, g = '3V3_CORE', 'GND_UI'
    stm = {'VBAT': v, 'VDD': v, 'VSS': g, 'VSSA': g, 'VDDA': v, 'VREF+': v,
           'NRST': 'STM_NRST', 'PB8': 'STM_BOOT0', 'PA13': 'STM_SWDIO',
           'PA14': 'STM_SWCLK', 'PB3': 'STM_SWO',
           'PA9': 'STM_TX_RAW', 'PA10': 'ESP_TO_STM', 'PB0': 'UI_PWR_EN',
           'PA0': 'NTC_ADC', 'PA1': 'FLOW_TIM', 'PC0': 'DOOR_CLOSED_N',
           'PA2': 'WATER_LEVEL', 'PC1': 'BU_PRESENT_N', 'PC2': 'BU_WORK_N'}
    esp = {'GND': g, 'EP_GND': g, '3V3': v, 'EN': 'ESP_EN', 'IO0': 'ESP_BOOT0',
           'IO17': 'ESP_TX_RAW', 'IO18': 'STM_TO_ESP', 'TXD0': 'ESP_DEBUG_TX',
           'RXD0': 'ESP_DEBUG_RX', 'IO4': 'KEY_SDA', 'IO5': 'KEY_SCL',
           'IO6': 'KEY_INT_N', 'IO7': 'BL_RAW', 'IO8': 'RST_RAW', 'IO9': 'DC_RAW',
           'IO10': 'CS_RAW', 'IO11': 'MOSI_RAW', 'IO12': 'SCLK_RAW'}
    d.note('OPEN SAECO / PRINCIPAL — NÚCLEO LÓGICO A.0', 12, 12, 3)
    d.note('BORRADOR: lógica, alimentación y sensores de baja tensión. Sin red, drivers de cargas, watchdog ni USB.', 12, 22, 1.8)
    d.note('01 / STM32 de control — C431633', 20, 36, 1.8)
    d.add('U101','STM32G431RB','STM32G431RBT6',82,112,[stm.get(n) for n in STM_PINS],
          'Package_QFP:LQFP-64_10x10mm_P0.5mm')
    d.note('NC = sin asignar en esta hoja parcial; revisar al integrar sensores y drivers.', 20, 187)
    d.note('Reloj HSI interno. USART1 PA9/PA10, AF7. VREFBUF interno deshabilitado.', 20, 194)
    d.note('02 / ESP32 de interfaz — C2913201', 195, 36, 1.8)
    d.add('U201','ESP32S3WROOM1','ESP32-S3-WROOM-1-N8R8',263,112,
          [esp.get(n) for n in ESP_PINS], 'RF_Module:ESP32-S3-WROOM-1')
    d.note('GPIO35/36/37 reservados PSRAM. USB19/20 sin conectar en esta hoja.',195,163)
    d.note('03 / Conexiones internas y programación',390,36,1.8)
    d.add('J101','J2','12V_ISOLATED_INPUT / JST XH',440,60,['12V_ISO_RAW',g],
          'Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal',
          status='candidate', part_key='CONN:JST_XH_2_RA')
    d.add('#FLG101', 'PWR_FLAG', 'Isolated 12V source / J101', 540, 48, ['12V_ISO_RAW'])
    d.add('#FLG102', 'PWR_FLAG', 'Isolated return / J101', 540, 61, [g])
    d.add('#FLG103', 'PWR_FLAG', 'Regulated output / U301', 540, 74, [v])
    d.add('#FLG104', 'PWR_FLAG', 'Protected 12V after F301/D301', 540, 87, ['12V_PROTECTED'])
    d.add('J102','J6','STM_SWD / 1x6 2.54mm',440,108,
          [v,'STM_SWDIO',g,'STM_SWCLK','STM_NRST','STM_SWO'],
          'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
          status='candidate', part_key='CONN:HDR_1X6_2.54')
    d.add('J103','J6','ESP_UART / 1x6 2.54mm',540,108,
          [v,g,'ESP_DEBUG_TX','ESP_DEBUG_RX','ESP_EN','ESP_BOOT0'],
          'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
          status='candidate', part_key='CONN:HDR_1X6_2.54')
    d.note('J102/J103 pinout propio; 3V3 es referencia, no alimentar desde el programador.',390,133)
    d.add('J104','J16','UI_LINK / IDC 2x8 2.54mm',440,185,d.UPLINK,
          'Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical',
          status='candidate', part_key='CONN:IDC_2X8_2.54')
    d.note('J101 recibe 12V DC aislados. Nunca conectar a red.',390,229)
    d.note('04 / Reset y arranque',20,213,1.8)
    for args in [
        ('R101','R','10k',56,227,v,'STM_NRST'),
        ('C101','C','100nF',56,244,'STM_NRST',g),
        ('R102','R','10k',56,261,'STM_BOOT0',g),
        ('R201','R','10k',155,227,v,'ESP_EN'),
        ('C201','C','1uF',155,244,'ESP_EN',g),
        ('R202','R','10k',155,261,v,'ESP_BOOT0')]:
        d.passive(*args)
    d.note('EN/BOOT accesibles por J103. BOOT0 STM: opción de arranque por SWD pendiente.',20,278)
    d.note('05 / UART entre MCU y resistencias de origen SPI',230,213,1.8)
    for i,(a,b) in enumerate([('STM_TX_RAW','STM_TO_ESP'),('ESP_TX_RAW','ESP_TO_STM'),
                              ('SCLK_RAW','LCD_SCLK'),('MOSI_RAW','LCD_MOSI'),
                              ('CS_RAW','LCD_CS_N'),('DC_RAW','LCD_DC'),
                              ('RST_RAW','LCD_RST_N'),('BL_RAW','LCD_BL_PWM')]):
        x=274+(i%3)*120; y=244+(i//3)*19
        d.passive(f'R{211+i}','R','33',x,y,a,b)
    d.note('UART cruzada. 33 ohm candidato, ajustar con flancos y arnés real.',230,300)
    d.note('06 / Desacoplo — colocar junto al pin indicado, comprobar capacitancia efectiva',20,315,1.8)
    caps=[('C102','100nF','VDD13'),('C103','100nF','VDD32'),
          ('C104','100nF','VDD48'),('C105','100nF','VDD64'),
          ('C106','4.7uF','bulk STM'),('C107','10nF','VDDA20'),
          ('C108','1uF','VDDA20'),('C109','100nF','VREF19'),
          ('C110','1uF','VREF19'),('C111','100nF','VBAT1'),
          ('C202','100nF','ESP pad2'),('C203','10uF','ESP pad2')]
    for i,(ref,val,pin) in enumerate(caps):
        d.passive(ref,'C',val+' / '+pin,56+(i%6)*98,335+(i//6)*22,v,g)
    d.note('07 / Entrada aislada protegida y buck 3V3 — AP63203, 2A',610,36,1.8)
    d.add('F301','FUSE','1A / 72VDC',645,58,['12V_ISO_RAW','12V_FUSED'],
          'Fuse:Fuse_1206_3216Metric',part_key='F:1A')
    d.add('D301','DIODE','SS34',690,58,['12V_FUSED','12V_PROTECTED'],
          'Diode_SMD:D_SMA',part_key='D:SS34')
    d.add('D302','DIODE','SMAJ18A',735,58,[g,'12V_PROTECTED'],
          'Diode_SMD:D_SMA',part_key='D:SMAJ18A')
    d.add('C301','C','10uF / 25V input',775,58,['12V_PROTECTED',g],
          'Capacitor_SMD:C_0805_2012Metric',part_key='C:10uF_25V_0805')
    d.add('C302','C','100nF / input HF',775,78,['12V_PROTECTED',g],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.add('U301','AP63203','AP63203WU-7',680,110,
          [v,'12V_PROTECTED','12V_PROTECTED','BST_NODE','SW_NODE',g],
          'Package_TO_SOT_SMD:TSOT-23-6')
    d.add('C303','C','100nF / bootstrap',742,101,['BST_NODE','SW_NODE'],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.add('L301','L','3.9uH',742,119,['SW_NODE',v],
          'Inductor_SMD:L_Bourns-SRN6028',part_key='L:3.9uH')
    for ref, x in [('C304',772),('C305',807)]:
        d.add(ref,'C','22uF / 10V output',x,119,[v,g],
              'Capacitor_SMD:C_0805_2012Metric',part_key='C:22uF_10V_0805')
    d.add('C306','C','100nF / output HF',807,101,[v,g],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.note('Fusible + bloqueo de polaridad + TVS. Valores del circuito recomendado Diodes, tabla 2.',610,145,1.2)
    d.note('Entrada exclusivamente desde una fuente AC/DC aislada y certificada; el módulo de red aún no está seleccionado.',610,151,1.2)
    d.note('08 / Corte y descarga del frontal — TPS22918, 2A',610,174,1.8)
    d.add('U302','TPS22918','TPS22918DBVR',690,207,
          [v,g,'UI_PWR_EN','3V3_UI','3V3_UI','UI_RISE'],
          'Package_TO_SOT_SMD:SOT-23-6')
    d.passive('R301','R','100k',625,218,v,'UI_PWR_EN')
    d.add('C307','C','1nF / CT',750,218,['UI_RISE',g],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:1nF')
    d.passive('C308','C','1uF / switch input',625,196,v,g)
    d.passive('C309','C','10uF / switch output',795,196,'3V3_UI',g)
    d.note('PB0 controla UI_PWR_EN; pull-up mantiene el frontal encendido durante reset.',610,244,1.2)
    d.note('QOD unido a VOUT; CT=1nF limita inrush. Verificar rampa y descarga con el display final.',610,250,1.2)
    d.note('09 / Entradas pasivas — huellas candidatas según fotos con calibre', 12, 406, 1.8)
    d.add('J105','J2','JP13 NTC / 2 vías',62,445,['NTC_RAW',g],
          'Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal',
          status='photo_candidate', part_key='CONN:JST_XH_2_RA')
    d.passive('R401','R','4.7k / NTC pull-up',145,430,v,'NTC_RAW')
    d.passive('R402','R','1k / NTC serie',145,447,'NTC_RAW','NTC_ADC')
    d.passive('C401','C','100nF / NTC filtro',145,464,'NTC_ADC',g)
    d.note('PA0 ADC1_IN1. NTC a masa; abierto≈3V3, corto≈0V. Usar tabla del manual.',20,486,1.2)

    d.add('J106','J3','JP5 FLOW ADAPTER / VCC-GND-OC',292,445,
          ['FLOW_RAW',g,'12V_PROTECTED'],
          'Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal',
          status='photo_candidate_owner_pinout', part_key='CONN:JST_XH_3_RA')
    d.passive('R403','R','4.7k / FLOW pull-up',385,430,v,'FLOW_RAW')
    d.passive('R404','R','1k / FLOW serie',385,447,'FLOW_RAW','FLOW_TIM')
    d.passive('C402','C','10nF / FLOW filtro',385,464,'FLOW_TIM',g)
    d.note('PA1 TIM2_CH2. Pin 1 señal, 2 GND, 3 VCC; pin 1 es pad cuadrado/izquierda en vista cenital.',245,486,1.2)
    d.note('Digmesa 932-9521-B: NPN OC, 3,8–20V. VCC=12V_PROTECTED; pull-up separado a 3V3.',245,493,1.2)

    d.add('J107','J2','JP14 DOOR / contacto seco',520,445,['DOOR_RAW',g],
          'Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal',
          status='photo_candidate', part_key='CONN:JST_XH_2_RA')
    d.passive('R405','R','10k / DOOR pull-up',605,430,v,'DOOR_RAW')
    d.passive('R406','R','1k / DOOR serie',605,447,'DOOR_RAW','DOOR_CLOSED_N')
    d.passive('C403','C','100nF / DOOR filtro',605,464,'DOOR_CLOSED_N',g)
    d.note('PC0: 0=cajón y puerta colocados; 1=abierto. Medido sin tensión.',490,486,1.2)

    d.add('J108','J8','JP16 VISUAL V1..V8 / XH-8',705,457,
          [None,None,'BU_BRIDGE','BU_BRIDGE',g,'BU_PRESENT_RAW',g,'BU_WORK_RAW'],
          'Connector_JST:JST_XH_S8B-XH-A_1x08_P2.50mm_Horizontal',
          status='photo_candidate', part_key='CONN:JST_XH_8_RA')
    d.passive('R407','R','10k / PRES pull-up',805,421,v,'BU_PRESENT_RAW')
    d.passive('R408','R','1k / PRES serie',805,438,'BU_PRESENT_RAW','BU_PRESENT_N')
    d.passive('C404','C','100nF / PRES filtro',805,455,'BU_PRESENT_N',g)
    d.passive('R409','R','10k / WORK pull-up',805,472,v,'BU_WORK_RAW')
    d.passive('R410','R','1k / WORK serie',805,489,'BU_WORK_RAW','BU_WORK_N')
    d.passive('C405','C','100nF / WORK filtro',805,506,'BU_WORK_N',g)
    d.note('PC1/PC2 activos a 0. V1 rojo motor+, V2 azul motor-, V3/V4 puente,',660,530,1.1)
    d.note('V5/V6 verde presencia, V7/V8 rojo trabajo: vista manual, no numeración física.',660,536,1.1)

    d.add('J109','J3','JP22 WATER / RED-WHITE-BLACK',520,536,
          [v,'WATER_RAW',g],
          'Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal',
          status='photo_candidate_owner_pinout', part_key='CONN:JST_PH_3_RA')
    d.passive('R411','R','1k / WATER serie',610,543,'WATER_RAW','WATER_LEVEL')
    d.passive('C406','C','10nF / WATER filtro',680,543,'WATER_LEVEL',g)
    d.note('PA2 ADC1_IN3/GPIO. Pin 1 rojo=3V3, 2 blanco=señal, 3 negro=GND; salida por caracterizar.',470,562,1.2)
    d.note('Falta: fuente aislada 24V, USB/ESD, watchdog, contactos JP16 y etapas de potencia.',12,574)
    d.note('Contorno/taladros aceptados; huellas de conector candidatas, colocación y rutas pendientes. BOM no liberada.',12,582)
    d.write_outputs('Open Saeco main logic + low-voltage power / INCOMPLETE - REVIEW ONLY','A1',841,594)


if __name__ == '__main__':
    main()
