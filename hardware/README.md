# Hardware

- [Frontal](front-panel/README.md): botones, LED y conector de pantalla, con la
  mecánica recuperada de la placa original. PCB ruteada, DRC limpio y paquete
  JLCPCB candidato, pendiente de las comprobaciones previas al pedido.
- [Principal](controller/core-design.md): lógica, USB de servicio, sensores,
  cargas de 24 V y de red y fuente aislada en una sola placa de cuatro capas,
  ruteada y con DRC limpio. [Contrato con el frontal](controller/front-panel-interface.md).
- [Potencia](power/README.md): etapas de red, válvula y watchdog.
- [Selección para montaje JLCPCB](assembly/README.md) y
  [proyectos KiCad](kicad-workflow.md).

La principal no es fabricable: faltan la comprobación 1:1 de conectores, la
identificación de JP14, JP16 y JP22 y la revisión independiente de
aislamiento y seguridad. Su paquete JLCPCB es candidato: no pedirlo hasta
cerrarlos.
