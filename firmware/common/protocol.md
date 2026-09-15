# Protocolo v0 — propuesta no implementada

ESP32 solicita, STM32 decide. Mensajes futuros: HELLO, STATUS, STOP, START_RECIPE,
ACK y ERROR. START se rechaza en el núcleo actual.
Framing futuro: versión, tipo, longitud acotada, secuencia, sesión e integridad.
Codificación, CRC, timeout y límites numéricos TBD. Rechazar corrupción, versión
desconocida, comandos duplicados y datos caducados. CRC no autentica usuarios.
Autenticación web, CSRF y provisión de red pendientes. Sin GPIO remoto directo.
