# USB de servicio y control en banco

La principal usa el periférico USB nativo del ESP32-S3 en J110. Su objetivo es
flashear, registrar telemetría y controlar las pruebas desde un ordenador sin
necesitar un adaptador USB-UART. El ESP32 actúa como pasarela; el STM32 conserva
la autoridad sobre estados, interlocks y actuadores.

## Hardware Rev A

- J110: USB-C USB 2.0 vertical HRO TYPE-C-31-D-06, junto a la posición del JP21 rojo.
- GPIO19 = D− y GPIO20 = D+, con 33 Ω junto al módulo.
- USBLC6-2SC6 junto al conector para ESD; 5,1 kΩ a masa en CC1 y CC2.
- GPIO21 detecta VBUS con divisor 100 kΩ/100 kΩ y filtro de 10 nF.
- J111 se fabrica abierto. Solo al cerrarlo en banco, VBUS pasa por un PTC de
  500 mA y un SS34 hasta el buck de 3,3 V. No alimentar cargas por esta vía.

El equipo puede funcionar autoalimentado desde J101 con J111 abierto. En ese caso
el firmware debe comprobar VBUS antes de habilitar el dispositivo USB. La unión
de la pantalla del conector a `GND_UI` y el dominio aislado deben revisarse antes
de exponer el puerto en una máquina conectada a red.

El par D+/D− se rutará a 90 Ω diferencial ±10 %, sobre referencia de masa continua,
con longitudes igualadas y pocas vías. La protección se coloca junto al conector
y las resistencias serie junto al ESP32, siguiendo la
[guía de esquema](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)
y la [guía de layout](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)
de Espressif.

## Sesión de pruebas prevista

La primera versión expondrá consola serie USB para logs y comandos acotados. El
ESP32 enviará solicitudes por la UART interna y el STM32 responderá con estado y
telemetría. El protocolo debe incluir versión, longitud, número de secuencia, CRC,
timeout y estado de interlocks, como se define en
[el contrato común](../firmware/common/protocol.md).

Conjunto mínimo de operaciones:

| Operación | Resultado | Autoridad |
|---|---|---|
| `HELLO` | Versiones y capacidades | ESP32 + STM32 |
| `STATUS` | Estado, fallos, entradas y alimentación | STM32 |
| `STREAM` | Telemetría periódica con tasa limitada | STM32 |
| `TEST` | Solicitud temporal de una prueba definida | STM32 decide y limita |
| `STOP` | Lleva las salidas al estado inactivo | STM32 |
| `CLEAR_FAULT` | Rearme solo con causa ausente e interlocks válidos | STM32 |

No habrá escritura arbitraria de GPIO ni memoria. Cada prueba de actuador tendrá
un tiempo máximo, límites eléctricos y condición de parada definidos en el STM32.
La desconexión USB, pérdida de UART o bloqueo del ESP32 cancelará la orden activa.
El primer ensayo se hará únicamente con cargas desconectadas y entradas simuladas.

`STATUS` y `STREAM` incluirán como mínimo `rail_12v_mv`, `rail_24v_mv`,
`brew_current_ma`, `brew_fault_n`, estado de puerta/grupo y bits de interlock.
Las tensiones proceden de PF1/ADC2_IN10 y PA5/ADC2_IN13 con factor nominal 21;
el firmware aplicará calibración y límites plausibles antes de usarlas para
diagnóstico. La cabecera J114 permite contrastar los valores sin interrumpir la
sesión USB.

El ESP32-S3 comparte el PHY entre USB-OTG y USB Serial/JTAG. El firmware deberá
elegir una configuración coherente; no puede asumir ambos controladores a la vez.
Véase la [documentación oficial de dispositivo USB](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html).
