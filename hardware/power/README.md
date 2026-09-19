# Potencia experimental / no verificada

Ya se midieron 68 Ω en el molino, 56,7 Ω en la electroválvula y 54,7 Ω en el
motor del grupo. El grupo dispone de un primer puente H en el esquema y la
[electroválvula tiene una etapa low-side candidata](valve-driver.md), ya incorporada
con el pinout confirmado. Un [watchdog e interlock hardware](watchdog-interlock.md)
bloquea ambas salidas durante reset o timeout. Molino, bomba y calentador siguen
sin driver.

La [arquitectura de alimentación de Rev A](power-architecture.md) conserva
entradas externas aisladas de 12 V y 24 V para el banco y mantiene red, bomba,
calentador y molino fuera del dominio de baja tensión. Incluye el presupuesto
provisional y la secuencia de puesta en marcha.

Faltan corrientes dinámicas, arranque, aislamiento y modos de fallo de cada carga.
Un motor DC puede trabajar a tensión peligrosa. Fuente aislada y corte independiente
requieren revisión. No se autoriza fabricación.

Las fotos dimensionales permiten reservar JST VH acodado de 3,96 mm como familia
candidata: S3P-VH para JP8/JP17 y S2P-VH para JP24. No se añaden todavía al
esquema porque su identificación mecánica no resuelve la separación de red, el
corte de seguridad ni los drivers de molino y bomba. JP19 continúa sin huella.
