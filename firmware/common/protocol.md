# Protocolo v0

ESP32 solicita, STM32 decide. USB termina en el ESP32 y usa esta misma frontera:
ningún comando del ordenador controla directamente un GPIO de potencia.
Implementado en [`proto.h`](proto.h) / [`proto.c`](proto.c) (C99 portable,
sin memoria dinámica), usado por los dos firmwares y probado en host
([`tests/test_proto.c`](../../tests/test_proto.c) y la fase F2 del
[simulador](../../sim/README.md)).

## Enlace

USART1 del STM32 (PA9/PA10, AF7) con el ESP32 (GPIO42/GPIO2) a 115200 baudios,
8N1, sin control de flujo.

## Trama

```
SOF 0xA5 | VER | TYPE | SEQ | LEN | PAYLOAD[LEN] | CRC16 lo | CRC16 hi
```

- `VER` = 0. `LEN` ≤ 32. Una trama ocupa como mucho 39 bytes.
- CRC-16/CCITT-FALSE (polinomio 0x1021, inicial 0xFFFF) sobre VER…PAYLOAD.
- El receptor se resincroniza en el siguiente SOF tras cualquier error: CRC,
  versión desconocida o longitud excesiva se descartan y se cuentan.
- `SEQ` lo pone el emisor. El STM32 responde a cada petición con su mismo `SEQ`;
  una petición repetida (mismo tipo y `SEQ` que la anterior) se contesta otra vez
  sin volver a ejecutarse.
- El CRC detecta corrupción; no autentica. Autenticación web, CSRF y provisión de
  red siguen pendientes.

## Mensajes

| Tipo | Código | Sentido | Payload | Respuesta |
|---|---|---|---|---|
| HELLO | 0x01 | ESP → STM | versión, rol | ACK, o ERROR si la versión no es 0 |
| KEEPALIVE | 0x02 | ESP → STM | — | ninguna |
| STATUS | 0x10 | STM → ESP | `osc_status`, 18 bytes | — |
| TEST_REPORT | 0x11 | STM → ESP | `osc_test_report`, 32 bytes | — |
| STOP | 0x20 | ESP → STM | — | ACK; todas las cargas a cero |
| CLEAR_FAULT | 0x21 | ESP → STM | — | ACK, o ERROR 3 si puerta/fallo/enlace no lo permiten |
| START_RECIPE | 0x22 | ESP → STM | receta (u8) | ERROR 3: el núcleo actual no arranca ciclos |
| UI_POWER | 0x23 | ESP → STM | 0 apagar, 1 encender el frontal | ACK |
| TEST | 0x24 | ESP → STM | prueba (u8), parámetro (u16, opcional) | ACK, o ERROR 3 si la rechaza; 0 borra el informe |
| ACK | 0x7E | STM → ESP | tipo aceptado | — |
| ERROR | 0x7F | STM → ESP | tipo, código | — |

Códigos de error: 1 tipo desconocido, 2 longitud incorrecta, 3 rechazado por el
núcleo, 4 no implementado. Un rechazo (START) es una respuesta normal, no un fallo
de comunicación.

`STATUS` (little endian): estado del núcleo (0 BOOT, 1 SAFE_IDLE, 2 FAULT,
3 SERVICE mientras una prueba de puesta a punto mueve cargas),
entradas (bit 0 puerta cerrada, 1 grupo presente, 2 grupo en trabajo, 3 fallo del
DRV8876, 4 frontal alimentado), salidas (bit 0 calentador, 1 bomba, 2 válvula,
3 molinillo, 4 motor del grupo), 12 V y 24 V en mV, corriente del grupo en mA,
código ADC del NTC, tiempo desde el arranque en ms y temperatura de la caldera
en décimas de °C (int16, −32768 con el NTC abierto o en corto).
Los rails y la corriente se escalan con la VDDA que el STM32 mide contra VREFINT.

## Tiempos

- STATUS cada 100 ms; KEEPALIVE del ESP32 cada 100 ms.
- Cada lado da el enlace por perdido si no recibe una trama válida en 350 ms.
- Tras el reset el núcleo espera en BOOT hasta 2 s a que el ESP32 aparezca; sin
  enlace después, o al perderlo, pasa a FAULT con todas las cargas a cero. Salir
  de FAULT exige CLEAR_FAULT con interlocks y enlace correctos; nada se reanuda
  solo.

## Pruebas de puesta a punto

`TEST` arranca una prueba acotada de
[`service_ids.h`](service_ids.h) (`firmware/stm32/src/service.c`): entradas,
ciclo del grupo, válvula, relé K701, bomba y caudal, calentador y molinillo.
El STM32 la rechaza (ERROR 3 y un informe `REFUSED` con el motivo) si el núcleo
no está en SAFE_IDLE, ya corre otra, falta la puerta o el grupo, el NTC no lee o
el parámetro se sale de rango. Mientras corre, `TEST_REPORT` sale cada 100 ms y
al terminar: prueba, fase (0 ninguna, 1 en curso, 2 terminada, 3 abortada,
4 rechazada), paso, motivo, ms transcurridos y seis valores int32 cuyo
significado fija `service_ids.h`. STOP, la pérdida del enlace, la puerta
abierta, nFAULT del DRV8876, el límite de temperatura o el tiempo máximo la
abortan con todas las cargas a cero; nada se reanuda solo. Una prueba con
cargas pasa por K701 con 100 ms de margen antes y después del triac.

Pendientes: STREAM, sesión y límites de receta. Ver
[USB de servicio](../../docs/service-usb.md).
