# Reverse engineering HD8911

## Evidencias iniciales
- E001: identificación aportada por propietario: HD8911, 421941308981/01, 220–230 V.
- E002: `docs/Service_manual_-_HD8911_01_-_2016-05-16.pdf`, referencia local de terceros.
  Páginas PDF 34–37 del capítulo 05 consultadas y cotejadas visualmente.
  Cubre variantes: cotejar con la unidad concreta.
- E003: `docs/Exploded view Saeco Incanto.pdf`, localizado; análisis pendiente.
- E004: siete fotografías HEIC en `docs/fotos/`, IMG_1085 a IMG_1091.
  HEIC inventariados; observaciones sobre JPEG de la conversación en [photos.md](photos.md).
- E005: conversación previa. Las inferencias del asistente no son evidencia medida.

No hay pinouts ni medidas de continuidad confirmados. No se han importado esquemas,
firmware ni conclusiones eléctricas del fabricante. Los archivos fuente no se incluyen
en este paquete y conservan sus derechos originales.

## Procedimiento inicial
1. Confirmar variante, revisión, etiquetas y orientación de cada conector por fotografía.
2. Inventariar cavidades, cables y destinos físicos con máquina desconectada y ausencia
   de tensión verificada; energía almacenada tratada por personal cualificado.
3. Registrar continuidad y dominios de aislamiento sin inferirlos por aspecto.
4. Leer marcajes de cargas; separar catálogo, hipótesis y resultados medidos.
5. Definir ensayos apropiados para sensores, caudal, motor y calibraciones.
6. Revisar el mapa antes de elegir fuentes, drivers y pines MCU.

Ensayos de red requieren procedimiento separado revisado y personal cualificado.
Este documento no proporciona instrucciones de trabajo bajo tensión.
