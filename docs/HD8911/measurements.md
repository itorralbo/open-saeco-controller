# Registro de medidas

Medidas aportadas por el propietario. Cuando no se indicó instrumento, temperatura
o incertidumbre, se conserva expresamente como dato pendiente.

| ID | Fecha/operador | PCB | Conector/cavidad/orientación | Instrumento | Condiciones | Resultado/unidad | Evidencia | Revisión |
|---|---|---|---|---|---|---|---|---|
| MAIN-W | 2026-09-17 / foto | principal | borde izquierdo–derecho | calibre 0,05 mm | PCB desmontada, IMG_1098 | 141,6 ± 0,15 mm | [mecánica](main-board-mechanics.md) | Aceptada Rev A |
| MAIN-H | 2026-09-17 / foto | principal | borde superior–inferior | calibre 0,05 mm | PCB desmontada, IMG_1099 | 135,2 ± 0,15 mm | [mecánica](main-board-mechanics.md) | Aceptada Rev A |
| MAIN-MH | 2026-09-17 / fotogrametría | principal | 3 taladros, origen superior izquierdo | cuadrícula + contorno calibrado | vista casi normal, IMG_1098 | centros y diámetro en documento | [mecánica](main-board-mechanics.md) | Aceptada Rev A |
| LOAD-GRINDER-R | 2026-09-18 / propietario | molino | terminales del motor | multímetro/modelo TBD | desconectado; temperatura TBD | 68 Ω | comunicación del propietario | Medida inicial |
| LOAD-VALVE-R | 2026-09-18 / propietario | electroválvula | terminales de bobina | multímetro/modelo TBD | desconectada; temperatura TBD | 56,7 Ω | comunicación del propietario | Confirma ≈10 W a 24 V |
| LOAD-BU-R | 2026-09-18 / propietario | motor del grupo | rojo–azul de JP16 | multímetro/modelo TBD | desconectado; temperatura/posición de rotor TBD | 54,7 Ω | comunicación del propietario | Medida inicial |
| JP14-CONT | 2026-09-18 / propietario | puerta/cajón | dos blancos | continuidad/modelo TBD | puerta o cajón retirados | circuito abierto | comunicación del propietario | Estado funcional confirmado |
| JP14-CONT | 2026-09-18 / propietario | puerta/cajón | dos blancos | continuidad/modelo TBD | cajón y puerta colocados | circuito cerrado | comunicación del propietario | Estado funcional confirmado |
| JP5-PINOUT | 2026-09-18 / propietario | caudalímetro | vista cenital, pad cuadrado a la izquierda | seguimiento visual | unidad identificada 932-9521-B | 1 señal; 2 GND; 3 VCC | comunicación del propietario + hoja Digmesa | Pinout adoptado Rev A |
| JP22-PINOUT | 2026-09-18 / propietario | sensor de agua | arnés de tres hilos | seguimiento por color | módulo desconectado | rojo VCC; blanco señal; negro GND; VCC 3,3/5 V | comunicación del propietario + foto JP22 | Pinout adoptado Rev A; salida TBD |

Clasificar cada entrada como documento, observación, hipótesis o medida. Conservar
datos contradictorios y bloquear decisiones dependientes hasta resolverlos.

## Paquete de medidas prioritario para cerrar Rev A

Todas estas comprobaciones se hacen con la máquina desenchufada, los conectores
separados de la placa y ausencia de tensión verificada. No hace falta energizar la
máquina ni medir la red. Anotar siempre desde qué lado se mira el conector.

### 1. Fotos y conectores

Las fotos de cavidades con calibre de JP5, JP13, JP14, JP16 y JP22 ya están en
`photos/Conectores/`. Permiten seleccionar huellas candidatas XH/PH. Para liberar
la mecánica todavía conviene una comprobación real de acoplamiento con una muestra.

1. Frontal de cavidades, con la pestaña de retención visible.
2. Lateral de placa y carcasa, con calibre o regla en el mismo plano.

Registrar paso entre centros, ancho y alto de la carcasa, distancia desde el borde
de PCB, número de cavidades, cavidades vacías, orientación de pestaña y cualquier
logo o referencia moldeada. Añadir una foto legible del marcado del caudalímetro
para resolver `932-8521` frente a `932-9521` y fotos de ambas caras del módulo
capacitivo `421941306721`.

### 2. Continuidad de contactos

Usar continuidad u ohmios; registrar resistencia aproximada y estado mecánico:

| ID propuesto | Par | Estado A | Estado B | Resultado esperado del trabajo |
|---|---|---|---|---|
| JP14-CONT | dos blancos | puerta/cajón abierto | cerrado | **Cerrado únicamente con cajón y puerta colocados** |
| JP16-BRIDGE | dos negros | reposo | reposo | Confirmar puente local cercano a 0 Ω |
| JP16-PRES | dos verdes | grupo retirado | insertado | Determinar NO/NC funcional |
| JP16-WORK | dos rojos | fuera de posición | posición de trabajo | Determinar NO/NC funcional |

### 3. Resistencias de cargas desconectadas

Registrar resistencia en frío, temperatura ambiente y polaridad/colores usados:

| ID propuesto | Elemento | Par |
|---|---|---|
| LOAD-BU-R | motor del grupo `996530002796` | rojo–azul de JP16 |
| LOAD-VALVE-R | electroválvula `421944029371` | sus dos terminales |
| LOAD-GRINDER-R | molino `421944049151` | blanco–negro del motor desconectado |

Estas resistencias ayudan a detectar variantes y dimensionar el banco, pero no
sustituyen las corrientes de arranque y bloqueo. Ese ensayo se definirá después
con una fuente aislada y limitada; no se obtiene bloqueando motores desde la máquina.

### 4. Orden de conductores

JP5 ya queda identificado como 1 señal, 2 GND y 3 VCC. JP22 queda identificado
por color como rojo VCC, blanco señal y negro GND. Antes de fabricar todavía
conviene confirmar que la orientación de las huellas candidatas conserva ese
orden al enchufar los arneses. Para JP16, comprobar si la secuencia visual del manual coincide físicamente con
rojo motor, azul motor, negro, negro, verde, verde, rojo, rojo.

Para JP3 faltan dos comprobaciones que bloquean el driver de la válvula: identificar
las dos cavidades usadas respecto al pad cuadrado/pin 1 y medir en modo diodo en
ambos sentidos. Una caída solo en un sentido indicaría supresión integrada y
obligaría a conservar polaridad; dos cables negros no permiten descartarla.

## Plantilla para devolver resultados

| ID | Vista/orientación | Estado/condiciones | Medida | Foto asociada |
|---|---|---|---|---|
| JP14-CONT | dos blancos | puerta/cajón retirados | abierto | comunicación del propietario |
| JP14-CONT | dos blancos | cajón y puerta colocados | cerrado | comunicación del propietario |
| JP16-BRIDGE | pestaña arriba | desconectado |  |  |
| JP16-PRES | pestaña arriba | grupo retirado/insertado |  |  |
| JP16-WORK | pestaña arriba | fuera/en trabajo |  |  |
| LOAD-BU-R | rojo–azul | desconectado; temperatura TBD | 54,7 Ω | comunicación del propietario |
| LOAD-VALVE-R | terminales bobina | desconectada; temperatura TBD | 56,7 Ω | comunicación del propietario |
| JP3-DIODE | terminales bobina, ambas polaridades | desconectada |  |  |
| LOAD-GRINDER-R | blanco–negro | desconectado; temperatura TBD | 68 Ω | comunicación del propietario |
