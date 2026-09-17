# Registro mecánico del frontal

Estado: sin medidas; no asignar números a partir de fotos en perspectiva.
Los ocho pulsadores del esquema son capacidad, no posiciones de montaje.

## Convención para el levantamiento

Vista desde la cara de componentes, con una foto adicional desde el lado de
los botones para evitar espejados. Elegir un taladro identificable como origen;
registrar ejes X/Y y espesor Z, en mm. Fotografías perpendiculares de ambas caras,
referencia de PCB, conector y marcaje del display. Cotejar escala con cotas reales.

| Elemento | Datos requeridos | Valor | Evidencia |
|---|---|---|---|
| PCB original | Referencia y revisión | TBD | TBD |
| Contorno | Coordenadas de vértices/arcos y espesor | TBD | TBD |
| Fijaciones | Centros X/Y, diámetros, avellanados y zonas sin componentes | TBD | TBD |
| Pulsadores | Cantidad, centros, carrera y altura de actuación | TBD | TBD |
| Ventana | Ancho/alto útiles, radios y centro respecto al origen | TBD | TBD |
| Hueco interior | Volumen máximo, nervios y distancia al plástico | TBD | TBD |
| Pantalla original | Referencia, dimensiones y modo de fijación | TBD | TBD |
| Óptica | Orientación, máscara, visibilidad y zonas tapadas | TBD | TBD |
| Cable principal | Recorrido, longitud, número de hilos y salida | TBD | TBD |
| Entorno | Condensación, calor, limpieza y puntos de entrada de líquido | TBD | TBD |

## Criterios para cerrar el layout

- Superponer un plano 1:1 sobre la PCB original y comprobar centros y taladros.
- Comprobar conjunto carcasa–actuador–pulsador, incluyendo tolerancias y carrera.
- Presentar pantalla y adaptador en el hueco; verificar imagen visible sin recortes.
- Evitar que tornillos, flex o nervios carguen sobre el vidrio o componentes.
- Confirmar conector polarizado, pin 1 y vista de ambos extremos del nuevo arnés.
- Elegir stack-up, cobre, acabado y protección ambiental después de esta revisión.

La nueva PCB puede repetir la mecánica y contactos de la original sin reutilizar
su electrónica activa. JP21 no se considera compatible con J1: pinout y niveles
del arnés original continúan sin verificar.
