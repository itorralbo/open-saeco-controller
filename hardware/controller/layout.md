# Colocación de la principal Rev A

Estado: colocación funcional completa, sin cobre y no fabricable. La fuente de
verdad es `tools/layout_controller_pcb.py`; el script coloca las 132 huellas y
comprueba que los tres taladros aceptados no se muevan.

![Vista superior de la colocación](preview/pcb-staging-top.png)

## Zonas funcionales

- Borde superior izquierdo: enlace al frontal, USB-C y protección ESD.
- Parte superior: ESP32 con la antena orientada hacia el borde y toda la zona de
  exclusión del footprint libre de componentes y cobre.
- Superior central: entrada de 12 V, buck de 3,3 V y corte de alimentación del
  frontal.
- Superior derecho: entrada de 24 V, protección, bulk y puente H del grupo.
- Centro: STM32, desacoplo, reset, watchdog e interlock hardware.
- Borde inferior: conectores de sensores, JP3 de válvula y JP16 del grupo; sus
  redes de acondicionamiento quedan inmediatamente encima.
- Zona inferior central: rama de válvula de 24 V y cabeceras SWD/medida.

La colocación mantiene separadas las redes conmutadas del puente H y la válvula
de los adaptadores de NTC, caudal, nivel y contactos. Los condensadores del buck,
los desacoplos de MCU y los componentes de carga de bomba del DRV8876 están en su
bloque, pero su distancia final a cada pad se optimizará durante el routing.

## Validación

- 132/132 huellas eléctricas colocadas; contorno 141,6 × 135,2 mm y MH1–MH3
  preservados.
- DRC KiCad 10.0.6: 0 infracciones geométricas/de reglas.
- 307 conexiones sin rutear y tres diferencias de paridad correspondientes a
  los taladros mecánicos intencionales.
- El keepout de antena del ESP32 está libre; esta comprobación se hace mediante
  la propia regla del footprint y falló durante la primera iteración hasta mover
  los componentes afectados.

Las referencias se dejan temporalmente en `F.Fab` para que la colocación densa no
genere conflictos de serigrafía. Se añadirán identificadores legibles de
conectores, polaridad, puntos de medida y seguridad después del routing.

## Siguiente paso

Primero se rutearán USB, el buck y los desacoplos; después sensores y señales
lógicas; por último, las ramas de 24 V con anchos y retorno revisados. Los planos
de masa se añadirán cuando las rutas críticas estén fijadas. No se generarán
Gerbers de la principal mientras queden conexiones abiertas.
