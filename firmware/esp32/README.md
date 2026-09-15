# ESP32: interfaz

Proyecto mínimo ESP-IDF, candidato ESP32-S3. Solo emite diagnóstico, sin configurar
GPIO, UART, Wi-Fi, web ni actuadores. USB/web son objetivos pendientes.
En consola con ESP-IDF instalado y activado:
```
cd firmware/esp32
idf.py set-target esp32s3
idf.py build
```
Versión SDK validada: TBD. Registrar versión y placa en el primer build verificado.
