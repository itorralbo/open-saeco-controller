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
  sobre una imagen ya pintada. Pinta pantallas por estado; LVGL 9 con `esp_lcd` la
  sustituirá en el destino ([display + UI](../../docs/display-ui.md)).
- `esp_app.c`: enlace con el STM32 ([protocolo v0](../common/protocol.md)),
  pantallas (arranque, enlace perdido, BOOT, reposo, FALLO, standby) y teclas.
  Si el teclado no responde durante 1 s pide al STM32 apagar y encender el
  frontal (UI_POWER), con todas sus líneas en alta impedancia mientras está
  apagado.

Mapa de teclas provisional, hasta cerrar la UX: SW1 START (que el núcleo actual
rechaza), SW2 CLEAR_FAULT, SW4 (la de STBY) standby con el LED, SW7 STOP.

En consola con ESP-IDF instalado y activado:
```
cd firmware/esp32
idf.py set-target esp32s3
idf.py build
```
Versión SDK validada: TBD. Registrar versión y placa en el primer build verificado.
