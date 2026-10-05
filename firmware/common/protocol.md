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
| STATUS | 0x10 | STM → ESP | `osc_status`, 16 bytes | — |
| STOP | 0x20 | ESP → STM | — | ACK; todas las cargas a cero |
| CLEAR_FAULT | 0x21 | ESP → STM | — | ACK, o ERROR 3 si puerta/fallo/enlace no lo permiten |
| START_RECIPE | 0x22 | ESP → STM | receta (u8) | ERROR 3: el núcleo actual no arranca ciclos |
| UI_POWER | 0x23 | ESP → STM | 0 apagar, 1 encender el frontal | ACK |
| ACK | 0x7E | STM → ESP | tipo aceptado | — |
| ERROR | 0x7F | STM → ESP | tipo, código | — |

Códigos de error: 1 tipo desconocido, 2 longitud incorrecta, 3 rechazado por el
núcleo, 4 no implementado. Un rechazo (START) es una respuesta normal, no un fallo
de comunicación.

`STATUS` (little endian): estado del núcleo (0 BOOT, 1 SAFE_IDLE, 2 FAULT),
entradas (bit 0 puerta cerrada, 1 grupo presente, 2 grupo en trabajo, 3 fallo del
DRV8876, 4 frontal alimentado), salidas (bit 0 calentador, 1 bomba, 2 válvula,
3 molinillo, 4 motor del grupo), 12 V y 24 V en mV, corriente del grupo en mA,
código ADC del NTC (hasta calibrar la tabla) y tiempo desde el arranque en ms.
Los rails y la corriente se escalan con la VDDA que el STM32 mide contra VREFINT.

## Tiempos

- STATUS cada 100 ms; KEEPALIVE del ESP32 cada 100 ms.
- Cada lado da el enlace por perdido si no recibe una trama válida en 350 ms.
- Tras el reset el núcleo espera en BOOT hasta 2 s a que el ESP32 aparezca; sin
  enlace después, o al perderlo, pasa a FAULT con todas las cargas a cero. Salir
  de FAULT exige CLEAR_FAULT con interlocks y enlace correctos; nada se reanuda
  solo.

Pendientes: STREAM, TEST (prueba acotada con timeout que la desconexión USB o la
pérdida de UART cancelan), sesión y límites de receta. Ver
[USB de servicio](../../docs/service-usb.md).
