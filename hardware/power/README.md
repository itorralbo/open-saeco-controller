# Potencia experimental / no verificada

Ya se midieron 27,5 Ω en el calentador, 68 Ω en el molino, 56,7 Ω en la
electroválvula y 54,7 Ω en el motor del grupo. El grupo tiene un puente H
DRV8876 y la [electroválvula una etapa low-side](valve-driver.md) con el pinout
confirmado. La [etapa de red y cargas](mains-stage.md) (relé general, fusibles,
varistor y triacs de calentador, bomba y molinillo) está en el esquema y en la
PCB ruteada. Un [watchdog e interlock hardware](watchdog-interlock.md) anula
todas las órdenes de carga durante reset o timeout.

La [arquitectura de alimentación de Rev A](power-architecture.md) integra red,
bomba, calentador y molino en la misma PCB, físicamente fuera del dominio SELV,
y conserva entradas externas aisladas de 12 V y 24 V para el banco. Incluye el
presupuesto provisional y lo que queda por diseñar. Las fotos confirman que la
original usa una fuente flyback; Rev A sustituye ese primario a medida por un
módulo Mean Well IRM-30-24 encapsulado montado en la propia tarjeta.

Faltan corrientes dinámicas, arranque, aislamiento y modos de fallo de cada carga.
Un motor DC puede trabajar a tensión peligrosa. Fuente aislada y corte independiente
requieren revisión. No se autoriza fabricación.

JP8 y JP24 son las cabeceras LEOCO 3941P03*000 (3 vías a 3,96 mm) y
5001P020013 (2 vías a 5,00 mm), identificadas por el propietario el 2026-09-29;
JLCPCB no las tiene. JP17 es un TE RAST 5 1971845-3, identificado por el
propietario. Los tres están ya en el esquema y en la PCB, igual que JP19, el TE
RAST 5 1971845-4.
