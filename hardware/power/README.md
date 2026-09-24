# Potencia experimental / no verificada

Ya se midieron 68 Ω en el molino, 56,7 Ω en la electroválvula y 54,7 Ω en el
motor del grupo. El grupo dispone de un primer puente H en el esquema y la
[electroválvula tiene una etapa low-side candidata](valve-driver.md), ya incorporada
con el pinout confirmado. Un [watchdog e interlock hardware](watchdog-interlock.md)
bloquea ambas salidas durante reset o timeout. La
[etapa de red y cargas](mains-stage.md) ya fija la topología y los primeros
componentes candidatos; aún no está dibujada en el esquema ni enrutada.

La [arquitectura de alimentación de Rev A](power-architecture.md) conserva
entradas externas aisladas de 12 V y 24 V para el banco e integra red, bomba,
calentador y molino en la misma PCB, físicamente fuera del dominio SELV. Incluye
el presupuesto provisional y el orden de diseño. Las fotos confirman que la
original usa una fuente flyback; Rev A sustituye ese primario a medida por un
módulo Mean Well IRM-30-24 encapsulado montado en la propia tarjeta.

Faltan corrientes dinámicas, arranque, aislamiento y modos de fallo de cada carga.
Un motor DC puede trabajar a tensión peligrosa. Fuente aislada y corte independiente
requieren revisión. No se autoriza fabricación.

Las fotos dimensionales se tomaron como JST VH de 3,96 mm, en versión
vertical: B3P-VH para JP8 y B2P-VH para JP24. La revisión del 2026-09-24 mide
esas carcasas más anchas que las VH, así que siguen sin identificar. JP17 es un
TE RAST 5 1971845-3, identificado por el propietario. Se añadirán al esquema junto
con la separación de red, el corte de seguridad y los drivers de molino y bomba.
JP19 continúa sin huella identificada.
