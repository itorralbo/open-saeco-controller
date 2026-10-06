# ESP32: interfaz

Proyecto ESP-IDF mínimo, candidato ESP32-S3; `main/app_main.c` solo emite
diagnóstico. La lógica de la interfaz está en [`core/`](core), C99 portable sobre
[`esp_hal.h`](core/esp_hal.h), cuyo puerto a ESP-IDF (driver/gpio, i2c_master,
spi_master, uart, ledc) sigue TBD. En host la ejecuta el
[simulador](../../sim/README.md) (F2) contra la placa virtual.

- `frontpanel.c`: TCA9534 del frontal. Configura Output, Polarity y
  Configuration en ese orden, muestrea cada 5 ms o al bajar INT, antirrebote de
  20 ms, ignora una tecla mantenida desde el arranque hasta que se suelta y marca
  el teclado como inválido ante un NACK (no es "ninguna tecla").
- `display.c`: ST7789V por SPI a 10 MHz. Reset y despertar como máquina de
  estados no bloqueante, apaisado (MADCTL 0x60), RGB565 y retroiluminación solo
  sobre una imagen ya pintada. Pinta una pantalla de texto (título de color por
  estado, 12 líneas de 26 caracteres y pie) con la fuente 5×7 de `font5x7.c`
  (generada por [`tools/make_font5x7.py`](../../tools/make_font5x7.py)), y solo
  repinta lo que cambia; LVGL 9 con `esp_lcd` la sustituirá en el destino
  ([display + UI](../../docs/display-ui.md)).
- `ui.c`: menús, lógica pura (teclas dentro, una petición fuera, pantalla de
  texto). Inicio con estado, caldera, puerta, grupo y rails; MENU con café,
  puesta a punto, información y borrar fallo. Puesta a punto lista las pruebas
  de [`service_ids.h`](../common/service_ids.h): cada una explica qué hace y qué
  preparar, deja ajustar su parámetro (ml, °C o ms), y muestra en vivo paso,
  tiempo y valores. Tras la de bomba se introduce el volumen pesado y calcula
  los pulsos por litro del caudalímetro. La de molinillo muestra la corriente
  y para si falta grano o se atasca; la de dosis muele, prensa y dice si llegó
  café a la cámara.
- `esp_app.c`: enlace con el STM32 ([protocolo v0](../common/protocol.md)),
  STATUS y TEST_REPORT, teclas hacia `ui.c` y su pantalla hacia `display.c`.
  Si el teclado no responde durante 1 s pide al STM32 apagar y encender el
  frontal (UI_POWER), con todas sus líneas en alta impedancia mientras está
  apagado.

Mapa de teclas provisional, hasta cerrar la UX ([`ui.h`](core/ui.h)): columna
izquierda SW1 ▲, SW2 ▼, SW3 volver; derecha SW7 STOP, SW6 MENU, SW5 OK; SW4 (la
de STBY) standby con el LED. En inicio, OK pide café (que el núcleo aún rechaza)
o borra el fallo. STOP para cualquier prueba desde cualquier página.

En consola con ESP-IDF instalado y activado:
```
cd firmware/esp32
idf.py set-target esp32s3
idf.py build
```
Versión SDK validada: TBD. Registrar versión y placa en el primer build verificado.
