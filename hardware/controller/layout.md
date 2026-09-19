# Colocación de la principal Rev A

Estado: colocación mecánica de conectores y colocación funcional inicial, sin
cobre y no fabricable. La fuente de verdad mecánica es
`mechanical-source.json`; `tools/layout_controller_pcb.py` consume sus
coordenadas, coloca las 132 huellas y comprueba que los tres taladros aceptados
no se muevan.

![Vista superior de la colocación](preview/pcb-staging-top.png)

![Mapa mecánico de conectores](validation/main-connector-map.svg)

## Sustitución física de la placa original

La posición de los mazos ya no se decide por conveniencia eléctrica. Se ha
rectificado IMG_1098 con el contorno aceptado de 141,6 × 135,2 mm y se ha usado
IMG_1101 para confirmar el sentido de entrada lateral. Se fija esta relación:

| Original | Rev A | Borde | Origen de huella X/Y (mm) | Giro |
|---|---|---|---:|---:|
| JP21 | J104, enlace del frontal nuevo | superior | 6,2 / 6,5 | 90° |
| JP16 | J108, grupo y micros | izquierdo | 3,0 / 64,5 | 90° |
| JP14 | J107, puerta/cajón | izquierdo | 3,0 / 73,5 | 90° |
| JP3 | J113, electroválvula | inferior | 3,5 / 125,3 | 0° |
| JP22 | J109, nivel de agua | inferior | 19,0 / 128,2 | 0° |
| JP13 | J105, NTC | inferior | 29,0 / 125,3 | 0° |
| JP5 | J106, caudalímetro | inferior | 38,5 / 125,3 | 0° |

La incertidumbre de posición asignada es ±1,5 mm. J104 ocupa la zona de JP21,
pero no reproduce su interfaz: el IDC 2×8 nuevo es algo más ancho y enlaza con la
nueva placa frontal. J110 queda inmediatamente a su derecha, accesible desde el
mismo borde superior para las pruebas por ordenador.

También se reservan mediante áreas de regla las envolventes fotografiadas de
JP8, JP19, JP24, JP17 y los dos FASTON de tierra. Esas cargas de red no están
implementadas eléctricamente en la Rev A de baja tensión, pero otros componentes,
pistas, vías o planos no pueden invadir su espacio si una revisión posterior
recupera el control completo de la máquina.

## Zonas funcionales

- Borde superior izquierdo: enlace al frontal en la zona de JP21, USB-C a su
  derecha y protección ESD.
- Parte superior: ESP32 con la antena orientada hacia el borde y toda la zona de
  exclusión del footprint libre de componentes y cobre.
- Superior central: entrada de 12 V, buck de 3,3 V y corte de alimentación del
  frontal.
- Superior derecho: entrada de 24 V, protección, bulk y puente H del grupo.
- Centro: STM32, desacoplo, reset, watchdog e interlock hardware.
- Lateral izquierdo: JP16 del grupo y JP14 de puerta/cajón en sus zonas originales.
- Borde inferior izquierdo: JP3, JP22, JP13 y JP5, con el mismo orden y sentido
  de entrada observados en la placa original.
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

Antes del routing completo se comprobarán interferencias de los cuerpos 3D y se
imprimirá el mapa a escala 1:1 para presentarlo sobre la placa original. Después
se rutearán USB, el buck y los desacoplos; sensores y señales lógicas; y por
último las ramas de 24 V con anchos y retorno revisados. Los planos de masa se
añadirán cuando las rutas críticas estén fijadas. No se generarán Gerbers de la
principal mientras queden conexiones abiertas.
