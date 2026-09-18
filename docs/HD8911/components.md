# Componentes identificados y requisitos eléctricos

Consolidación del 2026-09-18 a partir de las referencias aportadas por el
propietario, el manual de servicio y el despiece local de la HD8911. Las cifras
derivadas se identifican como tales; no sustituyen los marcados de la unidad.

## Cargas

| Función | Referencia | Dato confirmado | Consecuencia para el diseño |
|---|---|---|---|
| Calentador XS4 | `421944028841` | 220–230 V AC, 1900 W; el manual especifica dos termostatos de un solo uso de 190 °C | Corriente nominal derivada: 8,26 A a 230 V y 8,64 A a 220 V. Requiere etapa y conectores de red, protección térmica independiente y dimensionado con margen |
| Bomba | `996530007753`, ULKA EP5/S GW | 220–230 V AC, 50 Hz, 48 W, 15 bar, servicio 2 min conectado / 1 min desconectado | Corriente nominal ideal derivada: 0,21 A a 230 V; la conmutación debe admitir la carga inductiva y sus transitorios |
| Electroválvula | `421944029371` | 24 V DC, dos vías; bobina medida 56,7 Ω | Driver low-side con rueda libre. Derivación resistiva: 0,423 A y 10,16 W a 24 V, coherente con el recambio de 10 W |
| Motor del grupo | `996530002796` / `11005214` | 24 V DC, reversible; devanado medido 54,7 Ω | Puente H con medida de corriente, frenado/estado seguro y margen para bloqueo. Límite resistivo derivado ≈0,439 A a 24 V; falta medir transitorio y variación con rotor/temperatura |
| Motor del molino V3.2 | `421944049151` | Conjunto 220–230 V; modo de servicio a 320 V DC; devanado medido 68 Ω | Continua rectificada de red. El límite resistivo parado sería ≈4,71 A a 320 V, no corriente nominal; arranque, funcionamiento y bloqueo siguen pendientes |

El modo de servicio del manual separa expresamente las cargas: motor de grupo a
24 V DC; bomba a 230 V AC; electroválvula a 24 V DC; calentador a 230 V AC y
molino a 320 V DC. El valor de 320 V es coherente con rectificar 230 V RMS
(`230·√2 ≈ 325 V`), pero esta relación es una inferencia y no define por sí sola
la etapa de control.

La nota del propietario identifica un protector térmico de bomba de 100 °C. La
familia EP5 admite un alojamiento para protector y el conjunto tiene régimen 2/1,
pero no se ha encontrado una hoja primaria que vincule ese umbral exacto a esta
referencia; se conserva como dato por verificar en el marcado de la unidad.

## Caudalímetro JP5

La pieza de recambio `996530059843` / `NV99.099` se comercializa actualmente
asociada al marcado `932-9521-B`, correspondiente al **Digmesa FHKSC** con boquilla
de 1,2 mm y orientación 0°. El despiece local, sin embargo, imprime
`932-8521/00`; puede ser una revisión anterior o una errata y debe comprobarse el
marcado de la unidad antes de fijar la calibración. La
[hoja de datos del fabricante](https://digmesa.com/dam/jcr%3A51d2b47b-59a8-4c83-8b94-6bf1a980a2fc/932-952x-Bxxx_GB_20V_V04.pdf)
aporta:

- alimentación de 3,8 a 20 V DC y consumo inferior a 8 mA;
- salida NPN de colector abierto, 20 mA máximo, con pull-up externo;
- nivel bajo inferior a 0,7 V y fuga máxima de 10 µA;
- salida cuadrada con ciclo útil aproximado del 50 %;
- para `932-9521-B`: aproximadamente 1925 pulsos/litro, 0,07–0,56 l/min y
  0,42 bar de pérdida a caudal máximo;
- exactitud indicada ±2 % y repetibilidad mejor que ±0,25 %;
- instalación horizontal, contactos hacia arriba, en aspiración entre depósito
  y bomba; temperatura hasta 65 °C.

El valor nominal equivale a **0,519 ml/pulso**. Los 200 pulsos de reserva descritos
por Saeco representan unos **104 ml**. Digmesa exige calibrar pulsos/litro en el
conjunto real, por lo que 1925 es una constante inicial, no la calibración final.
El propio manual redondea la relación a unos 2000 pulsos/litro. El propietario
identificó la unidad física como `932-9521-B` y siguió el pad cuadrado para fijar
el orden eléctrico en vista cenital de la tarjeta: **pin 1 izquierdo = señal,
pin 2 = GND y pin 3 = VCC**.

La Rev A alimenta VCC desde `12V_PROTECTED`, dentro del intervalo admitido, y
eleva la salida de colector abierto a 3,3 V con 4,7 kΩ. Una resistencia serie de
1 kΩ y 10 nF protegen/filtran la entrada PA1/TIM2_CH2. Así el sensor trabaja a
12 V pero nunca aplica 12 V al GPIO.

## NTC JP13

El despiece identifica `996530073428`, sensor NTC UL de 550 mm. La tabla del
manual es la referencia de conversión. Un ajuste beta de todos sus puntos da,
como aproximación derivada, **R25 ≈ 49,9 kΩ y B ≈ 4037 K**; el error del ajuste
queda aproximadamente entre −1,1 % y +2,4 % frente a los valores nominales.
Para firmware conviene usar la tabla e interpolación, conservando sus tolerancias,
en vez de tratar el ajuste como especificación del fabricante.

Una resistencia de precisión de 4,7 kΩ a 3,3 V y el NTC a masa produciría
aproximadamente 3,07 V a 20 °C, 1,36 V a 100 °C y 0,53 V a 150 °C. También permite
diagnosticar cable abierto cerca de 3,3 V y cortocircuito cerca de 0 V. Son valores
para diseñar y simular; orientación, protección y umbrales deben cerrarse en el
esquema y ensayarse con el sensor real.

El control proporcional solicitado puede ser la primera implementación de banco,
pero el calentador debe quedar apagado ante NTC abierto/cortocircuitado, MCU sin
ejecución o pérdida de control. El termostato térmico externo no debe depender del
firmware.

El manual ya proporciona criterios funcionales: error 10 para NTC en corto,
error 11 para NTC abierto, error 14 al alcanzar 170 °C y error 15 si la máquina no
calienta. El calentamiento inicial se describe en unos 45 s. La temperatura medida
en taza debe quedar entre 69 y 85 °C para el primer producto y entre 72 y 85 °C
para el segundo; esos límites de taza no son el setpoint directo de la caldera.

## Grupo de infusión y autodosis

JP16 reúne el motor de grupo y dos microinterruptores. El manual indica que al
arrancar el motor busca el micro de reposo, invierte el sentido y se separa unos
1–2 mm. Por ello hacen falta control bidireccional y timeout incluso cuando el
contacto funciona.

El algoritmo de ajuste de dosis mide la corriente del **motor del grupo** durante
la compresión. Define una corriente base sin café `I0` entre 100 y 300 mA y
objetivos:

| Aroma | Objetivo del motor del grupo | Tiempo de molino |
|---|---:|---:|
| 1–2 | `I0 + 55 mA` | 3,0–8,1 s |
| 3 | `I0 + 100 mA` | 3,5–9,0 s |
| 4–5 | `I0 + 200 mA` | 4,0–10,0 s |

Esto lleva el punto de medida esperado hasta 500 mA, aunque no acota la corriente
de arranque o bloqueo. La primera etapa puede dimensionar el shunt para buena
resolución hasta aproximadamente 1 A y reservar margen mayor en el puente H; el
rating definitivo depende de medir bloqueo con una fuente limitada.

La lógica física es que una cantidad mayor de café opone más resistencia al
movimiento del pistón y eleva el par y la corriente del motor del grupo. `I0` se
actualiza durante un movimiento sin café, por ejemplo un aclarado, para descontar
rozamientos, temperatura y envejecimiento. El resultado corrige el **tiempo de
molido de los ciclos posteriores**; por eso el apartado aparece junto al molino.

La corriente del **motor del molino también se mide**, pero el manual le asigna
otra función: corriente anormalmente baja para detectar falta de grano y corriente
alta para detectar muelas bloqueadas. Por tanto, el diseño necesita dos medidas
distintas: una de baja tensión en el puente H del grupo para autodosis y otra en
el dominio de 320 V DC del molino para diagnóstico y protección.

El micro `996530073474` corresponde a la familia Zippy SM1. La
[familia SM1](https://www.zippy.com/es/04_switch_pro_page.aspx?ps_rfnbr=261)
declara hasta 300 mΩ iniciales y variantes de 0,1 a 16 A a 125/250 V AC, pero la
referencia Saeco no revela el sufijo eléctrico exacto. El arnés solo usa dos
terminales de cada contacto; queda por medir si son COM–NO o COM–NC.

## Puerta y nivel de agua

- La puerta/cajón usa `996530073209` / `12001890`, descrito como
  `MICROSWITCH XG/V3D`. No se ha localizado una hoja de datos primaria que una
  inequívocamente ese código Saeco con un rating y una configuración de contactos.
  JP14 usa dos hilos. La medida física confirma circuito abierto con puerta o
  cajón retirados y cerrado únicamente cuando ambos están colocados. La entrada
  activa a cero de la Rev A representa por tanto `DOOR_CLOSED_N`.
- El nivel de agua es el conjunto capacitivo V3 `421941306721`, con soporte
  `996530073436` y cable de tres polos `421946035161`. Está situado aproximadamente
  a un tercio de la altura del depósito. El cable observado usa rojo=VCC,
  blanco=señal y negro=GND; el propietario confirma alimentación válida a 3,3 o
  5 V. La Rev A elige 3,3 V y lleva la señal a PA2 mediante 1 kΩ/10 nF. Sigue
  pendiente medir si la salida es analógica, push-pull o colector abierto y sus
  niveles con depósito lleno/vacío.

## Datos que aún requieren la unidad física

1. Forma y niveles de salida del módulo capacitivo `421941306721` con depósito lleno/vacío.
2. COM–NO/COM–NC de los dos contactos de JP16.
3. Corrientes de arranque y bloqueo del motor de grupo y del molino.
4. Corriente en caliente de la electroválvula.
5. Referencia completa marcada en los microinterruptores y verificación de acoplamiento de las carcasas candidatas.
