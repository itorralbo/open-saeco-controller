# Registro de medidas

Sin medidas registradas. Crear una fila por medida, incluyendo incertidumbre y unidad.

| ID | Fecha/operador | PCB | Conector/cavidad/orientación | Instrumento | Condiciones | Resultado/unidad | Evidencia | Revisión |
|---|---|---|---|---|---|---|---|---|
| MAIN-W | 2026-09-17 / foto | principal | borde izquierdo–derecho | calibre 0,05 mm | PCB desmontada, IMG_1098 | 141,6 ± 0,15 mm | [mecánica](main-board-mechanics.md) | Aceptada Rev A |
| MAIN-H | 2026-09-17 / foto | principal | borde superior–inferior | calibre 0,05 mm | PCB desmontada, IMG_1099 | 135,2 ± 0,15 mm | [mecánica](main-board-mechanics.md) | Aceptada Rev A |
| MAIN-MH | 2026-09-17 / fotogrametría | principal | 3 taladros, origen superior izquierdo | cuadrícula + contorno calibrado | vista casi normal, IMG_1098 | centros y diámetro en documento | [mecánica](main-board-mechanics.md) | Aceptada Rev A |

Clasificar cada entrada como documento, observación, hipótesis o medida. Conservar
datos contradictorios y bloquear decisiones dependientes hasta resolverlos.

## Paquete de medidas prioritario para cerrar Rev A

Todas estas comprobaciones se hacen con la máquina desenchufada, los conectores
separados de la placa y ausencia de tensión verificada. No hace falta energizar la
máquina ni medir la red. Anotar siempre desde qué lado se mira el conector.

### 1. Fotos y conectores

Para JP5, JP13, JP14, JP16 y JP22 hacen falta dos fotos nítidas por conector:

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
| JP14-CONT | dos blancos | puerta/cajón abierto | cerrado | Determinar cuál de los estados cierra el contacto |
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

Para JP5 y JP22, registrar los tres colores/identificadores desde izquierda a
derecha mirando las cavidades con la pestaña arriba, y repetir el orden mirando
el cabezal de la PCB. No asignar todavía VCC/GND/señal solo por el color. Para
JP16, comprobar si la secuencia visual del manual coincide físicamente con
rojo motor, azul motor, negro, negro, verde, verde, rojo, rojo.

## Plantilla para devolver resultados

| ID | Vista/orientación | Estado/condiciones | Medida | Foto asociada |
|---|---|---|---|---|
| JP14-CONT | pestaña arriba | abierto |  |  |
| JP14-CONT | pestaña arriba | cerrado |  |  |
| JP16-BRIDGE | pestaña arriba | desconectado |  |  |
| JP16-PRES | pestaña arriba | grupo retirado/insertado |  |  |
| JP16-WORK | pestaña arriba | fuera/en trabajo |  |  |
| LOAD-BU-R | rojo–azul | frío |  |  |
| LOAD-VALVE-R | terminales bobina | frío |  |  |
| LOAD-GRINDER-R | blanco–negro | frío |  |  |
