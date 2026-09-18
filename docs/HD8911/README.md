# Reverse engineering HD8911

## Evidencias iniciales
- E001: identificación aportada por propietario: HD8911, 421941308981/01, 220–230 V.
- E002: `docs/HD8911/Service_manual_-_HD8911_01_-_2016-05-16.pdf`, referencia
  local de terceros no incluida en Git. Páginas PDF 34–37 del capítulo 05 y página
  PDF 59, capítulo 10, consultadas y cotejadas visualmente.
  Cubre variantes: cotejar con la unidad concreta.
- E003: `docs/HD8911/Exploded view Saeco Incanto.pdf`; tablas de cargas, sensores,
  arneses y referencias cotejadas con la variante HD8911.
- E004: fotografías HEIC en `docs/HD8911/photos/` y adjuntos del propietario.
  HEIC inventariados; observaciones sobre JPEG de la conversación en [photos.md](photos.md).
- E005: conversación previa. Las inferencias del asistente no son evidencia medida.
- E006: transcripción aportada por el propietario del capítulo 10, contrastada con
  la página PDF 59 y consolidada en [electrical-diagram.md](electrical-diagram.md).
- E007: referencias de cargas y sensores identificadas por el propietario,
  contrastadas con manual, despiece y hojas de fabricante en
  [components.md](components.md).

El manual y las referencias confirman conectores, destinos y buena parte de las
tensiones y potencias. JP5 y los colores funcionales de JP22 ya están identificados;
siguen pendientes la forma de salida del sensor capacitivo, los contactos de JP16
y corrientes dinámicas de motores. Ya hay
resistencias de tres cargas y continuidad funcional de JP14. No se han importado esquemas internos, firmware
ni conclusiones eléctricas no mostradas por el fabricante. Los archivos fuente no
se incluyen en este paquete y conservan sus derechos originales.

## Procedimiento inicial
1. Confirmar variante, revisión, etiquetas y orientación de cada conector por fotografía.
2. Inventariar cavidades, cables y destinos físicos con máquina desconectada y ausencia
   de tensión verificada; energía almacenada tratada por personal cualificado.
3. Registrar continuidad y dominios de aislamiento sin inferirlos por aspecto.
4. Leer marcajes de cargas; separar catálogo, hipótesis y resultados medidos.
5. Definir ensayos apropiados para sensores, caudal, motor y calibraciones.
6. Revisar el mapa antes de elegir fuentes, drivers y pines MCU.

Las comprobaciones físicas que desbloquean el siguiente esquema están preparadas
en el [registro y paquete de medidas](measurements.md).

Ensayos de red requieren procedimiento separado revisado y personal cualificado.
Este documento no proporciona instrucciones de trabajo bajo tensión.
