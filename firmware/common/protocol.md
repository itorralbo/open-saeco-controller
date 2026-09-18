# Protocolo v0 — propuesta no implementada

ESP32 solicita, STM32 decide. USB termina en el ESP32 y usa esta misma frontera:
ningún comando del ordenador controla directamente un GPIO de potencia. Mensajes
futuros: HELLO, STATUS, STREAM, TEST, STOP, CLEAR_FAULT, START_RECIPE, ACK y ERROR.
TEST será una prueba acotada con timeout; START se rechaza en el núcleo actual.
Framing futuro: versión, tipo, longitud acotada, secuencia, sesión e integridad.
Codificación, CRC, timeout y límites numéricos TBD. Rechazar corrupción, versión
desconocida, comandos duplicados y datos caducados. CRC no autentica usuarios.
Autenticación web, CSRF y provisión de red pendientes. Sin GPIO remoto directo.
La desconexión USB, pérdida de UART o caducidad de la sesión cancela cualquier
prueba activa. Véase [USB de servicio](../../docs/service-usb.md).
