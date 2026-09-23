"""Main-board logic core, low-voltage supplies and brew-motor bridge.

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
# Espressif WROOM-1/-1U module pads (identical), including exposed ground pad 41.
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
    # AP63200 shares package and pinout with AP63203 but exposes FB for an
    # adjustable 24 V -> 12 V stage.
    d.DEFS['AP63200'] = d.DEFS['AP63203']
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
    d.DEFS['MOV'] = (two, 2.54, 1.5)
    d.DEFS['ACDC4'] = ([
        # The module is an isolated source, but its mains terminals and return
        # are passive from ERC's point of view. Only +V sources the DC rail.
        ('1', 'AC/L', 'passive', -10.16, 3.81, 0),
        ('2', 'AC/N', 'passive', -10.16, -3.81, 0),
        ('3', '-V', 'passive', 10.16, -3.81, 180),
        ('4', '+V', 'power_out', 10.16, 3.81, 180),
    ], 7.62, 6.35)
    # High-capacity G5RL-1A-E duplicates each 16 A contact terminal. The two
    # pads on each side are intentionally assigned to the same schematic net.
    d.DEFS['RELAY_G5RL'] = ([
        ('1', 'COIL_A', 'passive', -10.16, 7.62, 0),
        ('8', 'COIL_B', 'passive', -10.16, 3.81, 0),
        ('3', 'COM_A', 'passive', -10.16, -3.81, 0),
        ('6', 'COM_B', 'passive', -10.16, -7.62, 0),
        ('4', 'NO_A', 'passive', 10.16, -3.81, 180),
        ('5', 'NO_B', 'passive', 10.16, -7.62, 180),
    ], 7.62, 10.16)
    # USB-C USB 2.0 receptacle: duplicated A/B contacts and a separate shield pad.
    usb_a = [('A1', 'GND', 'passive'), ('A4', 'VBUS', 'passive'),
             ('A5', 'CC1', 'passive'), ('A6', 'D+', 'passive'),
             ('A7', 'D-', 'passive'), ('A8', 'SBU1', 'passive'),
             ('A9', 'VBUS', 'passive'), ('A12', 'GND', 'passive'),
             ('SH', 'SHIELD', 'passive')]
    usb_b = [('B1', 'GND', 'passive'), ('B4', 'VBUS', 'passive'),
             ('B5', 'CC2', 'passive'), ('B6', 'D+', 'passive'),
             ('B7', 'D-', 'passive'), ('B8', 'SBU2', 'passive'),
             ('B9', 'VBUS', 'passive'), ('B12', 'GND', 'passive')]
    d.DEFS['USB_C_16'] = ([
        (number, name, typ, -12.7, 15.24-i*3.81, 0)
        for i, (number, name, typ) in enumerate(usb_a)
    ] + [
        (number, name, typ, 12.7, 15.24-i*3.81, 180)
        for i, (number, name, typ) in enumerate(usb_b)
    ], 10.16, 17.78)
    d.DEFS['USBLC6'] = ([
        ('1', 'I/O1', 'passive', -7.62, 3.81, 0),
        ('2', 'GND', 'passive', -7.62, 0, 0),
        ('3', 'I/O2', 'passive', -7.62, -3.81, 0),
        ('6', 'I/O1', 'passive', 7.62, 3.81, 180),
        ('5', 'VBUS', 'passive', 7.62, 0, 180),
        ('4', 'I/O2', 'passive', 7.62, -3.81, 180),
    ], 5.08, 6.35)
    d.DEFS['DRV8876PWP'] = ([
        ('1', 'EN/IN1', 'input', -12.7, 15.24, 0),
        ('2', 'PH/IN2', 'input', -12.7, 11.43, 0),
        ('3', 'nSLEEP', 'input', -12.7, 7.62, 0),
        ('4', 'nFAULT', 'open_collector', -12.7, 3.81, 0),
        ('5', 'VREF', 'input', -12.7, 0, 0),
        ('6', 'IPROPI', 'output', -12.7, -3.81, 0),
        ('7', 'IMODE', 'input', -12.7, -7.62, 0),
        ('8', 'OUT1', 'power_out', -12.7, -11.43, 0),
        ('9', 'PGND', 'power_in', 12.7, -11.43, 180),
        ('10', 'OUT2', 'power_out', 12.7, -7.62, 180),
        ('11', 'VM', 'power_in', 12.7, -3.81, 180),
        ('12', 'VCP', 'passive', 12.7, 0, 180),
        ('13', 'CPH', 'passive', 12.7, 3.81, 180),
        ('14', 'CPL', 'passive', 12.7, 7.62, 180),
        ('15', 'GND', 'power_in', 12.7, 11.43, 180),
        ('16', 'PMODE', 'input', 12.7, 15.24, 180),
        ('17', 'EP', 'power_in', 12.7, -15.24, 180),
    ], 10.16, 17.78)
    d.DEFS['UCC27517DBV'] = ([
        ('1', 'IN+', 'input', -7.62, 3.81, 0),
        ('2', 'GND', 'power_in', -7.62, 0, 0),
        ('3', 'IN-', 'input', -7.62, -3.81, 0),
        ('5', 'VDD', 'power_in', 7.62, 3.81, 180),
        ('4', 'OUT', 'output', 7.62, -3.81, 180),
    ], 5.08, 6.35)
    # Zero-cross phototriac driver. Pins 3 and 5 are not connected inside.
    d.DEFS['OPTO_TRIAC'] = ([
        ('1', 'A', 'passive', -7.62, 5.08, 0),
        ('2', 'K', 'passive', -7.62, 0, 0),
        ('3', 'NC1', 'passive', -7.62, -5.08, 0),
        ('6', 'MT_IN', 'passive', 7.62, 5.08, 180),
        ('5', 'NC2', 'passive', 7.62, 0, 180),
        ('4', 'MT_G', 'passive', 7.62, -5.08, 180),
    ], 5.08, 7.62)
    # TRIAC in TO-220AB: A1 and A2 are the main terminals, G the gate.
    d.DEFS['TRIAC_TO220'] = ([
        ('1', 'A1', 'passive', -7.62, -3.81, 0),
        ('2', 'A2', 'passive', -7.62, 3.81, 0),
        ('3', 'G', 'input', 7.62, 0, 180),
    ], 5.08, 6.35)
    # Single-phase bridge in the KBP SIP-4 package: + ~ ~ - from pin 1.
    d.DEFS['BRIDGE_KBP'] = ([
        ('2', 'AC1', 'passive', -7.62, 2.54, 0),
        ('3', 'AC2', 'passive', -7.62, -2.54, 0),
        ('1', '+', 'passive', 7.62, 2.54, 180),
        ('4', '-', 'passive', 7.62, -2.54, 180),
    ], 5.08, 5.08)
    d.DEFS['NMOS_SOT23'] = ([
        ('1', 'G', 'input', -7.62, 0, 0),
        ('2', 'S', 'power_in', 7.62, -3.81, 180),
        ('3', 'D', 'power_out', 7.62, 3.81, 180),
    ], 5.08, 5.08)
    d.DEFS['TPS3828DBV'] = ([
        ('1', '~{RESET}', 'open_collector', -7.62, 3.81, 0),
        ('2', 'GND', 'power_in', -7.62, 0, 0),
        ('3', '~{MR}', 'input', -7.62, -3.81, 0),
        ('5', 'VDD', 'power_in', 7.62, 3.81, 180),
        ('4', 'WDI', 'input', 7.62, -3.81, 180),
    ], 5.08, 6.35)
    d.DEFS['DUAL_AND'] = ([
        ('1', '1A', 'input', -7.62, 7.62, 0),
        ('2', '1B', 'input', -7.62, 3.81, 0),
        ('5', '2A', 'input', -7.62, 0, 0),
        ('6', '2B', 'input', -7.62, -3.81, 0),
        ('8', 'VCC', 'power_in', 7.62, 7.62, 180),
        ('4', 'GND', 'power_in', 7.62, 3.81, 180),
        ('7', '1Y', 'output', 7.62, 0, 180),
        ('3', '2Y', 'output', 7.62, -3.81, 180),
    ], 5.08, 8.89)


def main():
    d.PROJECT = 'controller-core-reva'
    d.OUT = d.ROOT/'hardware/controller'
    d.objects.clear(); d.components.clear(); d.svg.clear()
    chip('STM32G431RB', STM_PINS)
    chip('ESP32S3WROOM1', ESP_PINS)
    power_symbols()
    for n in (1, 2, 3, 4, 5, 6, 8):
        d.DEFS[f'J{n}'] = (d.connector(n), 5.08, n*1.905+1.27)
    v, g = '3V3_CORE', 'GND_UI'
    stm = {'VBAT': v, 'VDD': v, 'VSS': g, 'VSSA': g, 'VDDA': v, 'VREF+': v,
           'NRST': 'STM_NRST', 'PB8': 'STM_BOOT0', 'PA13': 'STM_SWDIO',
           'PA14': 'STM_SWCLK', 'PB3': 'STM_SWO',
           'PA9': 'STM_TX_RAW', 'PA10': 'ESP_TO_STM', 'PB12': 'UI_PWR_EN',
           'PA3': 'NTC_ADC', 'PA2': 'FLOW_TIM', 'PA1': 'DOOR_CLOSED_N',
           'PC3': 'WATER_LEVEL', 'PC2': 'BU_PRESENT_N', 'PA0': 'BU_WORK_N',
           'PC0': 'BREW_CURRENT_ADC', 'PF1': 'RAIL_12V_ADC',
           'PC1': 'RAIL_24V_ADC', 'PC14': 'BREW_DIR_RAW',
           'PA7': 'VALVE_EN_RAW',
           'PF0': 'BREW_PWM_RAW', 'PB5': 'BREW_SLEEP_RAW',
           'PB4': 'WATCHDOG_KICK_RAW', 'PB6': 'BREW_FAULT_N',
           'PB7': 'MAINS_ARM_RAW', 'PB10': 'HEATER_EN_RAW',
           'PB11': 'PUMP_EN_RAW', 'PC4': 'GRINDER_EN_RAW'}
    esp = {'GND': g, 'EP_GND': g, '3V3': v, 'EN': 'ESP_EN', 'IO0': 'ESP_BOOT0',
           'IO42': 'ESP_TX_RAW', 'IO2': 'STM_TO_ESP', 'TXD0': 'ESP_DEBUG_TX',
           'RXD0': 'ESP_DEBUG_RX', 'IO4': 'KEY_SDA', 'IO5': 'KEY_SCL',
           'IO6': 'KEY_INT_N', 'IO7': 'BL_RAW', 'IO8': 'RST_RAW', 'IO9': 'DC_RAW',
           'IO10': 'CS_RAW', 'IO11': 'MOSI_RAW', 'IO12': 'SCLK_RAW',
           'IO19': 'USB_DM_RAW', 'IO20': 'USB_DP_RAW',
           'IO15': 'USB_VBUS_SENSE'}
    d.note('OPEN SAECO / PRINCIPAL — NÚCLEO LÓGICO A.0', 12, 12, 3)
    d.note('BORRADOR PARCIAL: lógica, USB, sensores y dos cargas de 24V. La principal final integra red.', 12, 22, 1.8)
    d.note('01 / STM32 de control — C431633', 20, 36, 1.8)
    d.add('U101','STM32G431RB','STM32G431RBT6',82,112,[stm.get(n) for n in STM_PINS],
          'Package_QFP:LQFP-64_10x10mm_P0.5mm')
    d.note('NC = sin asignar en esta hoja parcial; revisar al integrar sensores y drivers.', 20, 187)
    d.note('Reloj HSI interno. USART1 PA9/PA10, AF7. VREFBUF interno deshabilitado.', 20, 194)
    d.note('02 / ESP32 de interfaz, antena externa U.FL — C2980300', 195, 36, 1.8)
    d.add('U201','ESP32S3WROOM1','ESP32-S3-WROOM-1U-N8R8',263,112,
          [esp.get(n) for n in ESP_PINS], 'RF_Module:ESP32-S3-WROOM-1U')
    d.note('GPIO35/36/37 reservados PSRAM. USB nativo en GPIO19/20; GPIO15 detecta VBUS.',195,163)
    d.note('03 / Conexiones internas y programación',390,36,1.8)
    d.add('J101','J2','12V_ISOLATED_INPUT / JST XH',440,60,['12V_ISO_RAW',g],
          'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',
          status='candidate', part_key='CONN:JST_XH_2_V')
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
    d.note('PB12 controla UI_PWR_EN; pull-up mantiene el frontal encendido durante reset.',610,244,1.2)
    d.note('QOD unido a VOUT; CT=1nF limita inrush. Verificar rampa y descarga con el display final.',610,250,1.2)

    d.note('09 / USB-C de servicio — datos ESP32 y alimentación de banco opcional',610,276,1.8)
    d.add('J110','USB_C_16','USB-C SERVICE / USB 2.0',650,326,
          [g,'USB_VBUS','USB_CC1','USB_DP_PORT','USB_DM_PORT',None,
           'USB_VBUS',g,g,g,'USB_VBUS','USB_CC2','USB_DP_PORT',
           'USB_DM_PORT',None,'USB_VBUS',g],
          'OpenSaeco:USB_C_Receptacle_HRO_TYPE-C-31-D-06_Vertical',
          status='candidate', part_key='CONN:USB_C_HRO_16_V')
    d.add('U203','USBLC6','USBLC6-2SC6',742,326,
          ['USB_DP_PORT',g,'USB_DM_PORT','USB_DP_DEVICE','USB_VBUS','USB_DM_DEVICE'],
          'Package_TO_SOT_SMD:SOT-23-6', part_key='USBLC6-2SC6')
    d.passive('R221','R','33',805,315,'USB_DM_DEVICE','USB_DM_RAW')
    d.passive('R222','R','33',805,334,'USB_DP_DEVICE','USB_DP_RAW')
    d.passive('R223','R','5.1k / CC1 Rd',625,357,'USB_CC1',g)
    d.passive('R224','R','5.1k / CC2 Rd',685,357,'USB_CC2',g)
    d.passive('R225','R','100k / VBUS sense top',745,357,'USB_VBUS','USB_VBUS_SENSE')
    d.passive('R226','R','100k / VBUS sense bottom',805,357,'USB_VBUS_SENSE',g)
    d.passive('C204','C','10nF / VBUS sense',805,375,'USB_VBUS_SENSE',g)
    d.passive('C205','C','1uF / USB VBUS',745,375,'USB_VBUS',g)
    d.add('F302','FUSE','500mA resettable PTC',625,390,['USB_VBUS','USB_VBUS_FUSED'],
          'Fuse:Fuse_1206_3216Metric', part_key='F:500mA_PTC')
    d.add('J111','J2','USB BENCH POWER / OPEN',700,390,
          ['USB_VBUS_FUSED','USB_BENCH_ENABLE'],
          'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
          status='dnp_open_by_default')
    d.add('D303','DIODE','SS34 / USB power OR',775,390,
          ['USB_BENCH_ENABLE','12V_PROTECTED'],
          'Diode_SMD:D_SMA', part_key='D:SS34')
    d.note('GPIO19=D-, GPIO20=D+. R221/R222 junto al ESP; par diferencial 90 ohm y misma longitud.',610,402,1.1)
    d.note('J111 se fabrica ABIERTO. Cerrarlo solo en banco: USB limitado a 500mA alimenta el buck; no cargas.',610,408,1.1)
    d.note('10 / Entradas pasivas — huellas candidatas según fotos con calibre', 12, 406, 1.8)
    d.add('J105','J2','JP13 NTC / 2 vías',62,445,['NTC_RAW',g],
          'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',
          status='photo_candidate', part_key='CONN:JST_XH_2_V')
    d.passive('R401','R','4.7k / NTC pull-up',145,430,v,'NTC_RAW')
    d.passive('R402','R','1k / NTC serie',145,447,'NTC_RAW','NTC_ADC')
    d.passive('C401','C','100nF / NTC filtro',145,464,'NTC_ADC',g)
    d.note('PA3 ADC1_IN4. NTC a masa; abierto≈3V3, corto≈0V. Usar tabla del manual.',20,486,1.2)

    d.add('J106','J3','JP5 FLOW ADAPTER / VCC-GND-OC',292,445,
          ['FLOW_RAW',g,'12V_PROTECTED'],
          'Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical',
          status='photo_candidate_owner_pinout', part_key='CONN:JST_XH_3_V')
    d.passive('R403','R','4.7k / FLOW pull-up',385,430,v,'FLOW_RAW')
    d.passive('R404','R','1k / FLOW serie',385,447,'FLOW_RAW','FLOW_TIM')
    d.passive('C402','C','10nF / FLOW filtro',385,464,'FLOW_TIM',g)
    d.note('PA2 TIM2_CH3. Pin 1 señal, 2 GND, 3 VCC; pin 1 es pad cuadrado/izquierda en vista cenital.',245,486,1.2)
    d.note('Digmesa 932-9521-B: NPN OC, 3,8–20V. VCC=12V_PROTECTED; pull-up separado a 3V3.',245,493,1.2)

    d.add('J107','J2','JP14 DOOR / contacto seco',520,445,['DOOR_RAW',g],
          'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',
          status='photo_candidate', part_key='CONN:JST_XH_2_V')
    d.passive('R405','R','10k / DOOR pull-up',605,430,v,'DOOR_RAW')
    d.passive('R406','R','1k / DOOR serie',605,447,'DOOR_RAW','DOOR_CLOSED_N')
    d.passive('C403','C','100nF / DOOR filtro',605,464,'DOOR_CLOSED_N',g)
    d.note('PA1: 0=cajón y puerta colocados; 1=abierto. Medido sin tensión.',490,486,1.2)

    d.add('J108','J8','JP16 VISUAL V1..V8 / XH-8',705,457,
          # OUT2 on V1 and OUT1 on V2 keep both motor leads uncrossed on the PCB.
          ['BREW_OUT2','BREW_OUT1','BU_BRIDGE','BU_BRIDGE',g,'BU_PRESENT_RAW',g,'BU_WORK_RAW'],
          'Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical',
          status='photo_candidate', part_key='CONN:JST_XH_8_V')
    d.passive('R407','R','10k / PRES pull-up',805,421,v,'BU_PRESENT_RAW')
    d.passive('R408','R','1k / PRES serie',805,438,'BU_PRESENT_RAW','BU_PRESENT_N')
    d.passive('C404','C','100nF / PRES filtro',805,455,'BU_PRESENT_N',g)
    d.passive('R409','R','10k / WORK pull-up',805,472,v,'BU_WORK_RAW')
    d.passive('R410','R','1k / WORK serie',805,489,'BU_WORK_RAW','BU_WORK_N')
    d.passive('C405','C','100nF / WORK filtro',805,506,'BU_WORK_N',g)
    d.note('PC2 (presencia) / PA0 (trabajo) activos a 0. V1 rojo=OUT1, V2 azul=OUT2, V3/V4 puente,',660,530,1.1)
    d.note('V5/V6 verde presencia, V7/V8 rojo trabajo: vista manual, no numeración física.',660,536,1.1)

    d.add('J109','J3','JP22 WATER / RED-WHITE-BLACK',520,536,
          [v,'WATER_RAW',g],
          'Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',
          status='photo_candidate_owner_pinout', part_key='CONN:JST_PH_3_V')
    d.passive('R411','R','1k / WATER serie',610,543,'WATER_RAW','WATER_LEVEL')
    d.passive('C406','C','10nF / WATER filtro',680,543,'WATER_LEVEL',g)
    d.note('PC3 ADC12_IN9/GPIO. Pin 1 rojo=3V3, 2 blanco=señal, 3 negro=GND; salida por caracterizar.',470,562,1.2)
    d.note('11 / Motor del grupo 24V — DRV8876, PH/EN, límite candidato 1A',870,36,1.8)
    d.add('J112','J2','24V_ACTUATOR_INPUT / JST XH',905,62,['24V_ACT_RAW',g],
          'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',
          status='candidate', part_key='CONN:JST_XH_2_V')
    d.add('#FLG105','PWR_FLAG','Isolated 24V motor source / J112',1000,62,['24V_BREW'])
    d.add('F303','FUSE','1A / 72VDC',970,82,['24V_ACT_RAW','24V_BREW_FUSED'],
          'Fuse:Fuse_1206_3216Metric',part_key='F:1A')
    d.add('D304','DIODE','SS34',1040,82,['24V_BREW_FUSED','24V_BREW'],
          'Diode_SMD:D_SMA',part_key='D:SS34')
    d.add('C501','C','100uF / 35V motor bulk',1110,72,['24V_BREW',g],
          'Capacitor_SMD:CP_Elec_6.3x7.7',part_key='C:100uF_35V_SMD')
    d.add('C502','C','100nF / VM local',1155,72,['24V_BREW',g],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.add('U501','DRV8876PWP','DRV8876PWPR',1030,165,
          ['BREW_EN_DRV','BREW_DIR_DRV','BREW_SLEEP_DRV','BREW_FAULT_N',
           'BREW_VREF','BREW_CURRENT_ADC',g,'BREW_OUT1',g,'BREW_OUT2',
           '24V_BREW','BREW_VCP','BREW_CPH','BREW_CPL',g,g,g],
          'Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm',
          part_key='DRV8876PWPR')
    d.add('C503','C','100nF / VCP-VM',1110,125,['BREW_VCP','24V_BREW'],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.add('C504','C','22nF / CPH-CPL',1110,145,['BREW_CPH','BREW_CPL'],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:22nF')
    d.passive('R501','R','33 / EN',900,116,'BREW_PWM_RAW','BREW_EN_DRV')
    d.passive('R502','R','10k / EN pull-down',900,133,'BREW_EN_DRV',g)
    d.passive('R503','R','33 / PH',900,150,'BREW_DIR_RAW','BREW_DIR_DRV')
    d.passive('R504','R','10k / PH pull-down',900,167,'BREW_DIR_DRV',g)
    d.passive('R505','R','33 / nSLEEP',900,184,'BREW_SLEEP_INTERLOCK','BREW_SLEEP_DRV')
    d.passive('R506','R','10k / nSLEEP pull-down',900,201,'BREW_SLEEP_DRV',g)
    d.passive('R507','R','10k / nFAULT pull-up',900,218,v,'BREW_FAULT_N')
    d.passive('R508','R','16k / VREF top',970,235,v,'BREW_VREF')
    d.passive('R509','R','49.9k / VREF bottom',1040,235,'BREW_VREF',g)
    d.passive('C505','C','100nF / VREF',1110,235,'BREW_VREF',g)
    d.passive('R510','R','2.49k / IPROPI',970,255,'BREW_CURRENT_ADC',g)
    d.passive('C506','C','10nF / IPROPI',1040,255,'BREW_CURRENT_ADC',g)
    d.note('PF0 PWM (TIM1_CH3N), PC14 dirección, PB5 nSLEEP, PB6 nFAULT, PC0 ADC. PMODE/IMODE a GND.',870,280,1.1)
    d.note('R510 y divisor R508/R509 fijan ITRIP≈1A; validar corriente, térmica, bulk y frenado.',870,287,1.1)
    d.note('J112 exige 24V DC aislados. Protección de sobretensión pendiente de tolerancia/energía de la fuente.',870,294,1.1)
    d.note('12 / Electroválvula 24V — low-side, fusible propio y rueda libre',870,326,1.8)
    d.add('J113','J5','JP3 VALVE / JST XH',905,354,
          ['24V_VALVE','VALVE_RETURN',None,None,None],
          'Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical',
          status='owner_pinout_candidate', part_key='CONN:JST_XH_5_V')
    d.add('F304','FUSE','1A / 72VDC',970,354,['24V_ACT_RAW','24V_VALVE_FUSED'],
          'Fuse:Fuse_1206_3216Metric',part_key='F:1A')
    d.add('D305','DIODE','SS34',1040,354,['24V_VALVE_FUSED','24V_VALVE'],
          'Diode_SMD:D_SMA',part_key='D:SS34')
    d.add('#FLG106','PWR_FLAG','Protected valve rail',1110,354,['24V_VALVE'])
    d.add('D306','DIODE','SS34 / flyback',1040,386,['VALVE_RETURN','24V_VALVE'],
          'Diode_SMD:D_SMA',part_key='D:SS34')
    d.add('U502','UCC27517DBV','UCC27517DBVR',970,430,
          ['VALVE_EN_DRV',g,g,'12V_PROTECTED','VALVE_GATE_RAW'],
          'Package_TO_SOT_SMD:SOT-23-5',part_key='UCC27517DBVR')
    d.add('Q501','NMOS_SOT23','SI2308A',1070,430,
          ['VALVE_GATE',g,'VALVE_RETURN'],
          'Package_TO_SOT_SMD:SOT-23',part_key='MOSFET:SI2308A_60V')
    d.passive('R511','R','33 / IN',875,410,'VALVE_EN_INTERLOCK','VALVE_EN_DRV')
    d.passive('R512','R','10k / IN pull-down',875,430,'VALVE_EN_DRV',g)
    d.passive('R513','R','33 / gate',1020,454,'VALVE_GATE_RAW','VALVE_GATE')
    d.passive('R514','R','100k / gate pull-down',1090,454,'VALVE_GATE',g)
    d.passive('C507','C','100nF / driver local',940,480,'12V_PROTECTED',g)
    d.passive('C508','C','1uF / driver local',1010,480,'12V_PROTECTED',g)
    d.note('JP3.1=+24V, JP3.2=retorno conmutado; JP3.3–5 sin uso. PA7 gobierna U502.',870,510,1.1)
    d.note('D306 es obligatoria: la medida 0,073V en ambos sentidos no demuestra diodo interno polarizado.',870,518,1.1)
    d.note('F304 separa la válvula de F303; validar corriente en caliente, transitorio y térmica en banco.',870,526,1.1)
    d.note('13 / Supervisor y corte hardware — reset + watchdog + AND doble',12,610,1.8)
    d.add('U601','TPS3828DBV','TPS3828-33DBVR',180,660,
          ['STM_NRST',g,v,v,'WATCHDOG_KICK'],
          'Package_TO_SOT_SMD:SOT-23-5',part_key='TPS3828-33DBVR')
    d.add('U602','DUAL_AND','SN74LVC2G08DCTR',340,660,
          ['BREW_SLEEP_RAW','STM_NRST','VALVE_EN_RAW','STM_NRST',v,g,
           'BREW_SLEEP_INTERLOCK','VALVE_EN_INTERLOCK'],
          'Package_SO:SSOP-8_2.95x2.8mm_P0.65mm',part_key='SN74LVC2G08DCTR')
    d.passive('R601','R','33 / WDI',60,640,'WATCHDOG_KICK_RAW','WATCHDOG_KICK')
    d.passive('R602','R','1k / WDI pull-down',60,680,'WATCHDOG_KICK',g)
    d.passive('R603','R','10k / brew arm pull-down',260,630,'BREW_SLEEP_RAW',g)
    d.passive('R604','R','10k / valve pull-down',260,690,'VALVE_EN_RAW',g)
    d.passive('C601','C','100nF / supervisor local',180,710,v,g)
    d.passive('C602','C','100nF / logic local',340,710,v,g)
    d.note('PB4 debe producir flancos antes de 0,9s (mínimo). Timeout típico 1,6s; reset 120–300ms.',12,744,1.1)
    d.note('~RESET open-drain comparte STM_NRST y fuerza ambas salidas a 0 mediante U602.',12,752,1.1)
    d.note('R602 mantiene WDI activo si PB4 queda Hi-Z; R603/R604 aseguran órdenes inactivas al arrancar.',12,760,1.1)
    d.note('14 / Telemetría de alimentación y cabecera de medida',470,610,1.8)
    d.passive('R701','R','100k / 12V div A',500,640,'12V_PROTECTED','RAIL_12V_DIV')
    d.passive('R702','R','100k / 12V div B',570,640,'RAIL_12V_DIV','RAIL_12V_ADC')
    d.passive('R703','R','10k / 12V div low',640,640,'RAIL_12V_ADC',g)
    d.passive('C701','C','100nF / 12V ADC',710,640,'RAIL_12V_ADC',g)
    d.passive('R704','R','100k / 24V div A',500,684,'24V_ACT_RAW','RAIL_24V_DIV')
    d.passive('R705','R','100k / 24V div B',570,684,'RAIL_24V_DIV','RAIL_24V_ADC')
    d.passive('R706','R','10k / 24V div low',640,684,'RAIL_24V_ADC',g)
    d.passive('C702','C','100nF / 24V ADC',710,684,'RAIL_24V_ADC',g)
    d.add('J114','J6','POWER MONITOR / MEASURE ONLY',805,672,
          [g,v,'12V_PROTECTED','24V_ACT_RAW','RAIL_12V_ADC','RAIL_24V_ADC'],
          'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
          status='candidate', part_key='CONN:HDR_1X6_2.54')
    d.note('PF1=ADC2_IN10, PC1=ADC2_IN7. Divisor 200k/10k: Vin=21×ADC; RC≈0,95ms.',470,728,1.1)
    d.note('J114 es de medida; no inyectar alimentación. 12V/24V comparten GND aislada de banco.',470,736,1.1)
    d.note('15 / Red, fuente aislada y conectores de potencia — misma PCB',870,610,1.8)
    d.add('J115','J3','JP8 GRINDER / 320VDC',1100,641,
          ['GRINDER_DC_PLUS',None,'GRINDER_DC_MINUS'],
          'Connector_JST:JST_VH_B3P-VH_1x03_P3.96mm_Vertical',
          status='photo_candidate_owner_wiring', part_key='CONN:JST_VH_3_V')
    # Owner: only tabs 1 and 3 are wired, and they are the two ends of the
    # same boiler element, so which is which does not matter. 1900 W element
    # measured at 27.5 ohm, so 8.4 A at 230 V.
    # Tab 3 sits nearest the board edge, so it takes the neutral return and
    # tab 1 takes the switched live coming down from the heatsink.
    d.add('J116','J4','JP19 HEATER / 1900W 27R5',1155,674,
          ['HEATER_AC_SWITCHED',None,'MAINS_N',None],
          'OpenSaeco:TE_RAST5_1971845-4_1x04_P5.00mm_Vertical',
          status='owner_identified', part_key='CONN:TE_RAST5_1971845-4')
    d.add('J117','J2','JP24 PUMP / 230VAC',1100,702,
          ['PUMP_AC_SWITCHED','MAINS_N'],
          'Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical',
          status='photo_candidate', part_key='CONN:JST_VH_2_V')
    d.add('J118','J3','JP17 MAINS / L-N',1155,738,
          ['MAINS_L_IN',None,'MAINS_N'],
          'Connector_JST:JST_VH_B3P-VH_1x03_P3.96mm_Vertical',
          status='photo_candidate_owner_wiring', part_key='CONN:JST_VH_3_V')
    # Owner: both are protective-earth tabs, JP1 to the boiler body and JP9 to
    # the mains inlet. The board is the junction between them.
    d.add('J119','J1','JP1 PE TO BOILER',1100,768,['PROTECTIVE_EARTH'],
          'OpenSaeco:FASTON_Tab_6.3x0.8mm_PE',
          status='faston_provisional_leg_pattern')
    d.add('J120','J1','JP9 PE INPUT',1155,768,['PROTECTIVE_EARTH'],
          'OpenSaeco:FASTON_Tab_6.3x0.8mm_PE',
          status='faston_provisional_leg_pattern')
    # Main input protection and the isolated supply. Values for F701/F702/RV701
    # remain provisional until the complete inrush and fault-current budget exists.
    d.add('F701','FUSE','T10A / 250V MAIN / provisional',835,640,
          ['MAINS_L_IN','MAINS_L_FUSED'],
          'Fuse:Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal',
          status='rating_and_holder_tbd')
    d.add('RV701','MOV','275VAC MOV / energy TBD',835,665,
          ['MAINS_L_FUSED','MAINS_N'],
          'Varistor:RV_Disc_D15.5mm_W5mm_P7.5mm',status='mpn_and_energy_tbd')
    d.add('F702','FUSE','T1A / PSU / provisional',835,690,
          ['MAINS_L_FUSED','PSU_L_FUSED'],
          'Fuse:Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal',
          status='rating_and_holder_tbd')
    d.add('PS701','ACDC4','IRM-30-24',930,676,
          ['PSU_L_FUSED','MAINS_N',g,'24V_INTERNAL_RAW'],
          'OpenSaeco:MeanWell_IRM-30_THT',
          status='candidate_pending_motor_current_validation',part_key='PSU:IRM-30-24')
    d.add('J121','J2','24V INTERNAL SELECT / OPEN FOR BENCH',1008,647,
          ['24V_INTERNAL_RAW','24V_ACT_RAW'],
          'Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm',
          status='normally_closed_open_for_external_24V')

    # 24 V -> 12 V is required because the existing logic and valve gate driver
    # cannot be fed directly from the IRM-30 output.
    d.add('U303','AP63200','AP63200WU-7 / 24V to 12V',808,739,
          ['BUCK12_FB','24V_ACT_RAW','24V_ACT_RAW','BUCK12_BST','BUCK12_SW',g],
          'Package_TO_SOT_SMD:TSOT-23-6',part_key='AP63200WU-7')
    d.add('L302','L','10uH / 3.5A',870,732,['BUCK12_SW','12V_ISO_RAW'],
          'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm',part_key='L:10uH_3.5A')
    d.add('C310','C','10uF / 50V input',772,770,['24V_ACT_RAW',g],
          'Capacitor_SMD:C_1206_3216Metric',part_key='C:10uF_50V_1206')
    d.add('C311','C','22uF / 25V output A',842,780,['12V_ISO_RAW',g],
          'Capacitor_SMD:C_1210_3225Metric',part_key='C:22uF_25V_1210')
    d.add('C312','C','22uF / 25V output B',880,780,['12V_ISO_RAW',g],
          'Capacitor_SMD:C_1210_3225Metric',part_key='C:22uF_25V_1210')
    d.add('C313','C','100nF / BST',924,744,['BUCK12_BST','BUCK12_SW'],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:100nF')
    d.add('R302','R','249k / 12V FB high',938,772,['12V_ISO_RAW','BUCK12_FB'],
          'Resistor_SMD:R_0603_1608Metric',part_key='R:249k')
    d.add('R303','R','18k / 12V FB low',978,772,['BUCK12_FB',g],
          'Resistor_SMD:R_0603_1608Metric',part_key='R:18k')
    d.add('C314','C','56pF / feed-forward',1018,772,['12V_ISO_RAW','BUCK12_FB'],
          'Capacitor_SMD:C_0603_1608Metric',part_key='C:56pF')
    # J121 intentionally permits disconnecting the onboard supply. Mark the
    # selected actuator rail as powered on the load side of that jumper.
    d.add('#FLG113','PWR_FLAG','Selected 24V actuator source',990,703,['24V_ACT_RAW'])

    # Independent normally-open phase cut. U603 is a second known dual-AND;
    # its unused channel is tied low so the relay cannot arm on floating inputs.
    # C603 gives it the same local decoupling U601 and U602 already have; the
    # gate that arms mains must not see a supply dip as a valid high.
    # The second gate was strapped low while it had no job. It now gates the
    # heater enable with reset, exactly as gate 1 does for the mains arm.
    d.add('U603','DUAL_AND','SN74LVC2G08DCTR',735,660,
          ['MAINS_ARM_RAW','STM_NRST','HEATER_EN_RAW','STM_NRST',v,g,
           'MAINS_RELAY_EN','HEATER_EN_INTERLOCK'],
          'Package_SO:SSOP-8_2.95x2.8mm_P0.65mm',part_key='SN74LVC2G08DCTR')
    d.add('Q701','NMOS_SOT23','SI2308A / relay coil',735,716,
          ['MAINS_RELAY_GATE',g,'MAINS_RELAY_RETURN'],
          'Package_TO_SOT_SMD:SOT-23',part_key='MOSFET:SI2308A_60V')
    d.passive('C603','C','100nF / arm gate local',800,660,v,g)
    d.passive('R801','R','33 / relay gate',680,704,'MAINS_RELAY_EN','MAINS_RELAY_GATE')
    d.passive('R802','R','100k / relay off',680,724,'MAINS_RELAY_GATE',g)
    d.add('D701','DIODE','SS34 / relay flyback',735,756,
          ['MAINS_RELAY_RETURN','24V_ACT_RAW'],'Diode_SMD:D_SMA',part_key='D:SS34')
    d.add('K701','RELAY_G5RL','G5RL-1A-E-TV8 DC24',1040,716,
          ['24V_ACT_RAW','MAINS_RELAY_RETURN','MAINS_L_FUSED','MAINS_L_FUSED',
           'LOAD_L_ENABLED','LOAD_L_ENABLED'],
          'OpenSaeco:Relay_SPST_Omron_G5RL-1A-E-TV8',
          status='candidate_not_released',part_key='RELAY:G5RL-1A-E-TV8_24V')
    d.note('16 / Etapa del calentador — 1900 W, 27,5 ohm, 8,36 A',870,850,1.8)
    d.passive('R711','R','10k / heater arm pull-down',880,872,'HEATER_EN_RAW',g)
    d.passive('R707','R','33 / opto LED gate',940,872,'HEATER_EN_INTERLOCK','HEATER_LED_GATE')
    d.passive('R708','R','100k / opto LED off',940,892,'HEATER_LED_GATE',g)
    d.add('Q705','NMOS_SOT23','SI2308A / heater opto LED',1000,880,
          ['HEATER_LED_GATE',g,'HEATER_LED_RETURN'],
          'Package_TO_SOT_SMD:SOT-23',part_key='MOSFET:SI2308A_60V')
    d.passive('R709','R','1k / opto LED series',1060,872,'12V_PROTECTED','HEATER_LED_ANODE')
    d.add('U701','OPTO_TRIAC','MOC3083 / zero-cross',1120,880,
          # Pins 4 and 6 are the two ends of the same output triac, so they
          # are interchangeable. U701 sits at the top of the optocoupler stack
          # with R710 above it: the feed takes pin 6 and the gate pin 4.
          ['HEATER_LED_ANODE','HEATER_LED_RETURN',None,'HEATER_GATE_FEED',
           None,'HEATER_TRIAC_GATE'],
          # C10797 is the plain 300 mil DIP; the footprint carries the milled
          # slot that lets it straddle the barrier.
          'OpenSaeco:DIP-6_W7.62mm_BarrierSlot',part_key='OPTO:MOC3083')
    # Anti-surge 1206 with a 500 V limiting element voltage: the gate
    # resistor sees up to 325 V peak if the opto ever fires off the zero.
    # 390 ohm keeps that worst case at 0.83 A, under the 1 A opto surge.
    d.add('R710','R','390 / gate limit 500V',1180,872,
          ['LOAD_L_ENABLED','HEATER_GATE_FEED'],
          'Resistor_SMD:R_1206_3216Metric', part_key='R:390_1206_500V')
    d.add('Q703','TRIAC_TO220','BTA24-800BWRG / heater',1240,880,
          ['HEATER_AC_SWITCHED','LOAD_L_ENABLED','HEATER_TRIAC_GATE'],
          'Package_TO_SOT_THT:TO-220-3_Vertical', part_key='TRIAC:BTA24-800BWRG')
    d.note('Disipador de perfil extruido 33 x 21 x 35 mm compartido con la bomba; '
           'lengueta aislada, asi que el perfil no es parte activa.',870,912,1.1)
    d.note('R710 ve 325 V de pico al disparar: ERJ-P08 antisobretension, 500 V '
           'de tension limite, 390 ohm.',870,920,1.1)

    # Pump: ULKA EP5/S GW, 48 W. The pump carries its own series diode, so it
    # draws current on one half-cycle only and a zero-cross driver restarts it
    # at every voltage zero; flow is set by skipping half-cycles. Same opto,
    # triac and gate resistor as the heater. U604 is a third dual-AND: gate 1
    # holds the pump off in reset, gate 2 does the same for the grinder.
    d.note('17 / Etapa de la bomba — ULKA EP5/S GW, 48 W, semionda',870,940,1.8)
    d.passive('R713','R','10k / pump arm pull-down',880,962,'PUMP_EN_RAW',g)
    d.add('U604','DUAL_AND','SN74LVC2G08DCTR',880,1000,
          ['PUMP_EN_RAW','STM_NRST','GRINDER_EN_RAW','STM_NRST',v,g,
           'PUMP_EN_INTERLOCK','GRINDER_EN_INTERLOCK'],
          'Package_SO:SSOP-8_2.95x2.8mm_P0.65mm',part_key='SN74LVC2G08DCTR')
    d.passive('C604','C','100nF / pump gate local',940,1010,v,g)
    d.passive('R714','R','33 / opto LED gate',940,962,'PUMP_EN_INTERLOCK','PUMP_LED_GATE')
    d.passive('R715','R','100k / opto LED off',940,982,'PUMP_LED_GATE',g)
    d.add('Q706','NMOS_SOT23','SI2308A / pump opto LED',1000,970,
          ['PUMP_LED_GATE',g,'PUMP_LED_RETURN'],
          'Package_TO_SOT_SMD:SOT-23',part_key='MOSFET:SI2308A_60V')
    d.passive('R716','R','1k / opto LED series',1060,962,'12V_PROTECTED','PUMP_LED_ANODE')
    d.add('U702','OPTO_TRIAC','MOC3083 / zero-cross',1120,970,
          # Here the feed takes pin 6, nearest R712, and the gate pin 4.
          ['PUMP_LED_ANODE','PUMP_LED_RETURN',None,'PUMP_GATE_FEED',
           None,'PUMP_TRIAC_GATE'],
          'OpenSaeco:DIP-6_W7.62mm_BarrierSlot',part_key='OPTO:MOC3083')
    d.add('R712','R','390 / gate limit 500V',1180,962,
          ['LOAD_L_ENABLED','PUMP_GATE_FEED'],
          'Resistor_SMD:R_1206_3216Metric', part_key='R:390_1206_500V')
    d.add('Q704','TRIAC_TO220','BTA24-800BWRG / pump',1240,970,
          ['PUMP_AC_SWITCHED','LOAD_L_ENABLED','PUMP_TRIAC_GATE'],
          'Package_TO_SOT_THT:TO-220-3_Vertical', part_key='TRIAC:BTA24-800BWRG')
    d.note('Sin snubber RC: triac snubberless y diodo serie en la bomba. Medir '
           'dV/dt en el apagado antes de liberar.',870,1010,1.1)

    # Grinder: V3.2 motor fed with rectified mains, 68 ohm winding. Its running
    # current has not been measured; Rev A assumes 1 A and the first prototype
    # measures it (docs/HD8911/characterization-plan.md). A triac switches the
    # AC side and a bridge after it gives JP8 fixed polarity, so the motor sees
    # nothing once the triac drops out. No bus capacitor, so no bleed resistor.
    # Same zero-cross opto as heater and pump: the grinder is on/off only.
    d.note('18 / Etapa del molinillo — V3.2, 68 ohm, 320 V DC; 1 A supuesto',870,1030,1.8)
    d.passive('R717','R','10k / grinder arm pull-down',880,1052,'GRINDER_EN_RAW',g)
    d.passive('R718','R','33 / opto LED gate',940,1052,'GRINDER_EN_INTERLOCK','GRINDER_LED_GATE')
    d.passive('R719','R','100k / opto LED off',940,1072,'GRINDER_LED_GATE',g)
    d.add('Q707','NMOS_SOT23','SI2308A / grinder opto LED',1000,1060,
          ['GRINDER_LED_GATE',g,'GRINDER_LED_RETURN'],
          'Package_TO_SOT_SMD:SOT-23',part_key='MOSFET:SI2308A_60V')
    d.passive('R720','R','1k / opto LED series',1060,1052,'12V_PROTECTED','GRINDER_LED_ANODE')
    d.add('U703','OPTO_TRIAC','MOC3083 / zero-cross',1120,1060,
          ['GRINDER_LED_ANODE','GRINDER_LED_RETURN',None,'GRINDER_GATE_FEED',
           None,'GRINDER_TRIAC_GATE'],
          'OpenSaeco:DIP-6_W7.62mm_BarrierSlot',part_key='OPTO:MOC3083')
    d.add('R721','R','390 / gate limit 500V',1180,1052,
          ['LOAD_L_ENABLED','GRINDER_GATE_FEED'],
          'Resistor_SMD:R_1206_3216Metric', part_key='R:390_1206_500V')
    d.add('Q708','TRIAC_TO220','BTA24-800BWRG / grinder',1240,1060,
          ['GRINDER_AC_SWITCHED','LOAD_L_ENABLED','GRINDER_TRIAC_GATE'],
          'Package_TO_SOT_THT:TO-220-3_Vertical', part_key='TRIAC:BTA24-800BWRG')
    # F703 is the grinder's own fuse, owner's decision on 2026-09-23. A 2 A
    # time-lag part rides through the 3.4 A start; a shorted bridge or winding
    # blows it without taking F701 and the whole machine with it.
    d.add('F703','FUSE','T2A / 250V grinder',1270,1030,
          ['GRINDER_AC_SWITCHED','GRINDER_AC_FUSED'],
          'OpenSaeco:Fuse_2410_JDT_JFC2410', part_key='FUSE:JFC2410-1200TS')
    d.add('BR701','BRIDGE_KBP','KBP410 / grinder bridge',1300,1060,
          ['GRINDER_AC_FUSED','MAINS_N','GRINDER_DC_PLUS','GRINDER_DC_MINUS'],
          'Diode_THT:Diode_Bridge_Vishay_KBPM', part_key='BRIDGE:KBP410')
    d.note('Q708 en el perfil del calentador y la bomba: ~0,8 W a 1 A. Bloqueo = '
           '230/68 = 3,4 A ef.: lo corta el firmware; F703 T2A cubre cortos.',870,1092,1.1)
    d.note('BR701 KBP410 4 A / 1 kV, RthJA 55 C/W: ~1,7 W y +95 K a 1 A continuo; '
           'el molido es intermitente. Medir en el prototipo.',870,1100,1.1)

    d.add('#FLG115','PWR_FLAG','Relay-enabled load phase',1045,792,['LOAD_L_ENABLED'])
    d.add('#FLG116','PWR_FLAG','Mains neutral endpoint',1085,792,['MAINS_N'])
    d.add('#FLG123','PWR_FLAG','Protective earth bond',1160,834,['PROTECTIVE_EARTH'])
    d.note('PS701 está en la misma PCB. J121 se abre antes de inyectar 24V externos por J112.',650,806,1.0)
    d.note('JP17: negro=L y azul=N; JP8: blanco=+ y negro=-. Centro libre en ambos.',870,817,1.0)
    d.note('Siguiente: filtro EMI, huellas PE y medidas de caracterización del molino.',12,804)
    d.note('Contorno/taladros aceptados; conectores incompletos y rutas pendientes. BOM no liberada.',12,812)
    d.write_outputs('Open Saeco main logic + low-voltage power / INCOMPLETE - REVIEW ONLY','A0',1189,841)


if __name__ == '__main__':
    main()
