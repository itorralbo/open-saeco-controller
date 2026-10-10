# Auditoría de colocación JLCPCB

Fecha: 2026-10-10. **Candidatos para revisión, no liberados para fabricar.**

Se comprueba cada referencia de ambas BOM, incluidas las excluidas del montaje. Para cada código LCSC se contrasta la huella pública enlazada por JLCPCB con los pads numerados de la PCB. Los alias eléctricos están documentados; no se aplica una corrección por el mero nombre del encapsulado.

Fuente: [JLCEDA/EasyEDA Official Library](https://easyeda.com), [JLCEDA](https://lceda.cn/), a través del visor de las fichas de JLCPCB. Los SVG originales quedan en caché local; el JSON registra URL, UUID y SHA-256. No se redistribuyen las bibliotecas originales.

La comparación comprueba orientación y centro, no tolerancias de fabricación, soldabilidad ni aprobación de la previsualización de un pedido concreto. El umbral de 0,30 mm es un filtro para diferencias entre land patterns, no una tolerancia admisible de colocación de la máquina.

Se usa el enfoque de [Bouni](https://github.com/Bouni/kicad-jlcpcb-tools/blob/b2ff3a08173e04d77ba35019bc1670a9c3f1317d/fabrication.py) para ángulos/cara inferior, con reglas exactas por pieza verificadas contra pads. La tabla genérica da resultados distintos para varios SOT/TSOT. El centro se obtiene alineando los extremos de los pads numerados: incluir un tetón NPTH como hace el bounding box genérico desplaza J116/J118.

## Pendientes de las posiciones montadas

- **controller F306 / C2838912:** NO MODEL: public API has no PCB footprint. Nonpolarized 1206 fuse; retained original CPL, pending vendor preview.
- **controller J118 / C5169636:** REVIEW: paired tails differ by 2.5 mm with contact order preserved. Check TE drawing, locating post and harness pin 1; do not rotate to conceal a contact reversal.
- **controller F701 / C142789:** REVIEW: model lead pitch 25.50 mm versus PCB 27.50 mm; axial leads need forming. Confirm the assembly operation with JLCPCB.
- **controller F702 / C142716:** BLOCKED: BOM orders a leadless 0215002.MXP fuse, but PCB footprint is a pair of Littelfuse 111 clips. Clips are not separate BOM items. Resolve assembly BOM/mechanics.
- **controller C314 / C49326334:** NO MODEL: public API has no PCB footprint. Nonpolarized 0603 capacitor; retained original CPL, pending vendor preview.
- **controller K701 / C397236:** BLOCKED: K701 holes span 20 mm; Omron G5RL-1A-E-HR requires 25 mm (20+5). Fix footprint/routing, not CPL. Source: https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5rl.pdf page 5.
- **controller F703 / C178840:** REVIEW: model is horizontal at 28 mm pitch, PCB is vertical at 5.08 mm. Requires lead forming/manual assembly; rotating a horizontal model cannot validate it.

## Resultado por componente

ΔX/ΔY son desplazamientos en ejes del CPL (X derecha, Y arriba), después de considerar el giro y la cara de la placa. Δθ es la corrección local; la columna final incluye también la convención de cara inferior. Los pendientes conservan los valores originales en el archivo de revisión.

| Placa | Ref | LCSC | Montaje | Estado | Δθ | ΔX mm | ΔY mm | Giro final | Error máximo pads mm |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| controller | U101 | [C431633](https://jlcpcb.com/partdetail/C431633) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.02483 |
| controller | U201 | [C2980300](https://jlcpcb.com/partdetail/C2980300) | sí | geometry_match | 0 | 0.0000 | -0.6200 | 0.0 | 0.0154 |
| controller | J101 | [C158012](https://jlcpcb.com/partdetail/C158012) | sí | geometry_match | 180 | 1.2500 | 0.0000 | 180.0 | 0.00032 |
| controller | J102 | [C52016393](https://jlcpcb.com/partdetail/C52016393) | sí | geometry_match | 270 | 6.3500 | 0.0000 | 0.0 | 0.0 |
| controller | J103 | [C52016393](https://jlcpcb.com/partdetail/C52016393) | sí | geometry_match | 270 | 6.3500 | 0.0000 | 0.0 | 0.0 |
| controller | J104 | [C19103863](https://jlcpcb.com/partdetail/C19103863) | excluido | no_model | — | 0.0000 | 0.0000 | 180.0 | — |
| controller | R101 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C101 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | R102 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R201 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | C201 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | R202 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R211 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R212 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R213 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R214 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R215 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R216 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R217 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R218 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | C102 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | C103 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C104 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | C105 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | C106 | [C19666](https://jlcpcb.com/partdetail/C19666) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | C107 | [C57112](https://jlcpcb.com/partdetail/C57112) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | C108 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C109 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C110 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C111 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C202 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | C203 | [C96446](https://jlcpcb.com/partdetail/C96446) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | F301 | [C2838907](https://jlcpcb.com/partdetail/C2838907) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.04526 |
| controller | D301 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00025 |
| controller | F305 | [C2838907](https://jlcpcb.com/partdetail/C2838907) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.04526 |
| controller | D307 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00025 |
| controller | D302 | [C148216](https://jlcpcb.com/partdetail/C148216) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.19964 |
| controller | C301 | [C15850](https://jlcpcb.com/partdetail/C15850) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.05076 |
| controller | C302 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | C315 | [C89632](https://jlcpcb.com/partdetail/C89632) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.11758 |
| controller | U301 | [C780769](https://jlcpcb.com/partdetail/C780769) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.06138 |
| controller | C303 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | L301 | [C19947652](https://jlcpcb.com/partdetail/C19947652) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.09956 |
| controller | C304 | [C380338](https://jlcpcb.com/partdetail/C380338) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.05076 |
| controller | C305 | [C380338](https://jlcpcb.com/partdetail/C380338) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.05076 |
| controller | C306 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | U302 | [C55266](https://jlcpcb.com/partdetail/C55266) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 270.0 | 0.21251 |
| controller | R301 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R304 | [C23184](https://jlcpcb.com/partdetail/C23184) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R305 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | C308 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | C309 | [C96446](https://jlcpcb.com/partdetail/C96446) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | J110 | [C2689964](https://jlcpcb.com/partdetail/C2689964) | sí | geometry_match | 0 | 0.0013 | 0.0000 | 0.0 | 0.01545 |
| controller | U203 | [C7519](https://jlcpcb.com/partdetail/C7519) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 90.0 | 0.01058 |
| controller | R221 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R222 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R223 | [C23186](https://jlcpcb.com/partdetail/C23186) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R224 | [C23186](https://jlcpcb.com/partdetail/C23186) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R225 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R226 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | C204 | [C57112](https://jlcpcb.com/partdetail/C57112) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | C205 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | F302 | [C163512](https://jlcpcb.com/partdetail/C163512) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.04526 |
| controller | J111 | — | excluido | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | D303 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00025 |
| controller | J105 | [C382532](https://jlcpcb.com/partdetail/C382532) | sí | geometry_match | 180 | -1.2500 | 0.0000 | 0.0 | 0.00032 |
| controller | R401 | [C23162](https://jlcpcb.com/partdetail/C23162) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R402 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | C401 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | R413 | [C2086379](https://jlcpcb.com/partdetail/C2086379) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.01578 |
| controller | C408 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | J106 | [C382533](https://jlcpcb.com/partdetail/C382533) | excluido | geometry_match | 180 | 2.5000 | 0.0000 | 180.0 | 0.00064 |
| controller | R403 | [C23162](https://jlcpcb.com/partdetail/C23162) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R404 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | C402 | [C57112](https://jlcpcb.com/partdetail/C57112) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | J107 | [C382532](https://jlcpcb.com/partdetail/C382532) | sí | geometry_match | 180 | 0.0000 | -1.2500 | 90.0 | 0.00032 |
| controller | R405 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R406 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | C403 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | J108 | [C476906](https://jlcpcb.com/partdetail/C476906) | excluido | geometry_match | 180 | 0.0000 | 8.7500 | 270.0 | 0.0016 |
| controller | R407 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R408 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | C404 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | R409 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R410 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | C405 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | U304 | [C55266](https://jlcpcb.com/partdetail/C55266) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.21251 |
| controller | R306 | [C22952](https://jlcpcb.com/partdetail/C22952) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C409 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | C410 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | J109 | [C158001](https://jlcpcb.com/partdetail/C158001) | sí | geometry_match | 0 | 1.5000 | 0.0000 | 0.0 | 0.0014 |
| controller | R411 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R415 | [C25803](https://jlcpcb.com/partdetail/C25803) | excluido | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R416 | [C25803](https://jlcpcb.com/partdetail/C25803) | excluido | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C406 | [C57112](https://jlcpcb.com/partdetail/C57112) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| controller | R412 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C407 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | J112 | [C158012](https://jlcpcb.com/partdetail/C158012) | sí | geometry_match | 180 | 1.2500 | 0.0000 | 180.0 | 0.00032 |
| controller | F306 | [C2838912](https://jlcpcb.com/partdetail/C2838912) | sí | no_model | — | 0.0000 | 0.0000 | -90.0 | — |
| controller | D308 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.00025 |
| controller | F303 | [C2838907](https://jlcpcb.com/partdetail/C2838907) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.04526 |
| controller | D304 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00025 |
| controller | C501 | [C176683](https://jlcpcb.com/partdetail/C176683) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 90.0 | 0.14476 |
| controller | C502 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | U501 | [C575551](https://jlcpcb.com/partdetail/C575551) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 180.0 | 0.00241 |
| controller | C503 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C504 | [C77571](https://jlcpcb.com/partdetail/C77571) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | R501 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R502 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R503 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R504 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R505 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R506 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R507 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R508 | [C25810](https://jlcpcb.com/partdetail/C25810) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R509 | [C23184](https://jlcpcb.com/partdetail/C23184) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C505 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | R510 | [C22940](https://jlcpcb.com/partdetail/C22940) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C506 | [C57112](https://jlcpcb.com/partdetail/C57112) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | J113 | [C382535](https://jlcpcb.com/partdetail/C382535) | sí | geometry_match | 180 | -5.0000 | 0.0000 | 0.0 | 0.00127 |
| controller | F304 | [C2838907](https://jlcpcb.com/partdetail/C2838907) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.04526 |
| controller | D305 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00025 |
| controller | D306 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00025 |
| controller | U502 | [C99395](https://jlcpcb.com/partdetail/C99395) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.16298 |
| controller | Q501 | [C347491](https://jlcpcb.com/partdetail/C347491) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.06326 |
| controller | R511 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R512 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R513 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R514 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C507 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | C508 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | U601 | [C20032](https://jlcpcb.com/partdetail/C20032) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.16298 |
| controller | U602 | [C352973](https://jlcpcb.com/partdetail/C352973) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.20119 |
| controller | R601 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R602 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R603 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R604 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C601 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | C602 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | U605 | [C7836](https://jlcpcb.com/partdetail/C7836) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.16298 |
| controller | C605 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | U606 | [C403723](https://jlcpcb.com/partdetail/C403723) | sí | geometry_match | 270 | 0.0045 | 0.0000 | 270.0 | 0.01566 |
| controller | C606 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | R701 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R702 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R703 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C701 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | R704 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R705 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R706 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | C702 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | R723 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | R724 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R725 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| controller | J114 | [C52016393](https://jlcpcb.com/partdetail/C52016393) | sí | geometry_match | 270 | 6.3500 | 0.0000 | 0.0 | 0.0 |
| controller | RT701 | [C13564](https://jlcpcb.com/partdetail/C13564) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R726 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | C704 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07396 |
| controller | J115 | — | excluido | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | C708 | — | excluido | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | J116 | [C2149727](https://jlcpcb.com/partdetail/C2149727) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.00115 |
| controller | J117 | — | excluido | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | J118 | [C5169636](https://jlcpcb.com/partdetail/C5169636) | sí | review_geometry | — | 0.0000 | 0.0000 | 0.0 | 2.50032 |
| controller | J119 | [C575074](https://jlcpcb.com/partdetail/C575074) | sí | geometry_match | 90 | 0.0000 | 0.0000 | 90.0 | 0.0 |
| controller | J120 | [C575074](https://jlcpcb.com/partdetail/C575074) | sí | geometry_match | 90 | 0.0000 | 0.0000 | 90.0 | 0.0 |
| controller | F701 | [C142789](https://jlcpcb.com/partdetail/C142789) | sí | review_geometry | — | 0.0000 | 0.0000 | 180.0 | 0.9992 |
| controller | RV701 | [C7502584](https://jlcpcb.com/partdetail/C7502584) | sí | geometry_match | 0 | 3.7500 | -1.1000 | 0.0 | 0.2491 |
| controller | C707 | [C161105](https://jlcpcb.com/partdetail/C161105) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.29988 |
| controller | F702 | [C142716](https://jlcpcb.com/partdetail/C142716) | sí | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | PS701 | [C6280124](https://jlcpcb.com/partdetail/C6280124) | sí | geometry_match | 0 | -10.5000 | 0.0000 | 90.0 | 0.00102 |
| controller | J121 | — | excluido | no_model | — | 0.0000 | 0.0000 | 180.0 | — |
| controller | U303 | [C2158003](https://jlcpcb.com/partdetail/C2158003) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.06265 |
| controller | L302 | [C2687402](https://jlcpcb.com/partdetail/C2687402) | sí | datasheet_checked | 180 | 0.0000 | 0.0000 | 180.0 | 0.55414 |
| controller | C310 | [C138687](https://jlcpcb.com/partdetail/C138687) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.04138 |
| controller | C316 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | C311 | [C49118556](https://jlcpcb.com/partdetail/C49118556) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.04138 |
| controller | C312 | [C49118556](https://jlcpcb.com/partdetail/C49118556) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.04138 |
| controller | C313 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | R302 | [C23137](https://jlcpcb.com/partdetail/C23137) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R303 | [C23352](https://jlcpcb.com/partdetail/C23352) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | C314 | [C49326334](https://jlcpcb.com/partdetail/C49326334) | sí | no_model | — | 0.0000 | 0.0000 | 0.0 | — |
| controller | U603 | [C352973](https://jlcpcb.com/partdetail/C352973) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 90.0 | 0.20119 |
| controller | Q701 | [C82045](https://jlcpcb.com/partdetail/C82045) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.29694 |
| controller | C603 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| controller | R722 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R801 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R802 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | D701 | [C2909963](https://jlcpcb.com/partdetail/C2909963) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.00025 |
| controller | K701 | [C397236](https://jlcpcb.com/partdetail/C397236) | sí | review_geometry | — | 0.0000 | 0.0000 | 180.0 | 2.50061 |
| controller | R711 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | R707 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R708 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | Q705 | [C82045](https://jlcpcb.com/partdetail/C82045) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.29694 |
| controller | R709 | [C2653986](https://jlcpcb.com/partdetail/C2653986) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | U701 | [C10797](https://jlcpcb.com/partdetail/C10797) | sí | geometry_match | 270 | 3.8100 | -2.5400 | 270.0 | 0.0 |
| controller | R710 | [C2086379](https://jlcpcb.com/partdetail/C2086379) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.01578 |
| controller | Q703 | [C15293](https://jlcpcb.com/partdetail/C15293) | sí | geometry_match | 0 | 2.5400 | 0.0000 | 0.0 | 0.00508 |
| controller | R713 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | U604 | [C352973](https://jlcpcb.com/partdetail/C352973) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.20119 |
| controller | C604 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| controller | R714 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | R715 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| controller | Q706 | [C82045](https://jlcpcb.com/partdetail/C82045) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.29694 |
| controller | R716 | [C2653986](https://jlcpcb.com/partdetail/C2653986) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | U702 | [C10797](https://jlcpcb.com/partdetail/C10797) | sí | geometry_match | 270 | 3.8100 | -2.5400 | 270.0 | 0.0 |
| controller | R712 | [C2086379](https://jlcpcb.com/partdetail/C2086379) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.01578 |
| controller | Q704 | [C15293](https://jlcpcb.com/partdetail/C15293) | sí | geometry_match | 0 | 2.5400 | 0.0000 | 0.0 | 0.00508 |
| controller | C705 | — | excluido | no_model | — | 0.0000 | 0.0000 | 90.0 | — |
| controller | R727 | — | excluido | no_model | — | 0.0000 | 0.0000 | -90.0 | — |
| controller | R717 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R718 | [C23140](https://jlcpcb.com/partdetail/C23140) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| controller | R719 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | Q707 | [C82045](https://jlcpcb.com/partdetail/C82045) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 180.0 | 0.29694 |
| controller | R720 | [C2653986](https://jlcpcb.com/partdetail/C2653986) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| controller | U703 | [C10797](https://jlcpcb.com/partdetail/C10797) | sí | geometry_match | 270 | 3.8100 | -2.5400 | 270.0 | 0.0 |
| controller | R721 | [C2086379](https://jlcpcb.com/partdetail/C2086379) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.01578 |
| controller | Q708 | [C15293](https://jlcpcb.com/partdetail/C15293) | sí | geometry_match | 0 | 2.5400 | 0.0000 | 0.0 | 0.00508 |
| controller | F703 | [C178840](https://jlcpcb.com/partdetail/C178840) | sí | review_geometry | — | 0.0000 | 0.0000 | 0.0 | 11.46048 |
| controller | BR701 | [C840747](https://jlcpcb.com/partdetail/C840747) | sí | geometry_match | 0 | 5.7750 | 0.0000 | 0.0 | 0.06 |
| controller | C706 | — | excluido | no_model | — | 0.0000 | 0.0000 | 90.0 | — |
| controller | R728 | — | excluido | no_model | — | 0.0000 | 0.0000 | -90.0 | — |
| controller | U704 | [C36873216](https://jlcpcb.com/partdetail/C36873216) | sí | geometry_match | 270 | -0.0200 | 0.0000 | 90.0 | 0.14298 |
| controller | C703 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| front-panel | J1 | [C19103863](https://jlcpcb.com/partdetail/C19103863) | excluido | no_model | — | 0.0000 | 0.0000 | 180.0 | — |
| front-panel | U1 | [C783615](https://jlcpcb.com/partdetail/C783615) | sí | geometry_match | 270 | 0.0000 | 0.0000 | 270.0 | 0.00275 |
| front-panel | C1 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| front-panel | C2 | [C15849](https://jlcpcb.com/partdetail/C15849) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07396 |
| front-panel | J2 | [C157974](https://jlcpcb.com/partdetail/C157974) | sí | geometry_match | 180 | -7.0000 | 0.0000 | 0.0 | 0.00128 |
| front-panel | R1 | [C23162](https://jlcpcb.com/partdetail/C23162) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | R2 | [C23162](https://jlcpcb.com/partdetail/C23162) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | R3 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | R4 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| front-panel | R5 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07062 |
| front-panel | R6 | [C25803](https://jlcpcb.com/partdetail/C25803) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | C3 | [C96446](https://jlcpcb.com/partdetail/C96446) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 90.0 | 0.07396 |
| front-panel | R11 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R21 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | SW1 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00046 |
| front-panel | C11 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R12 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R22 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | SW2 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00046 |
| front-panel | C12 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R13 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R23 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | SW3 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.00046 |
| front-panel | C13 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R14 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R24 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 180.0 | 0.07062 |
| front-panel | SW4 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.00046 |
| front-panel | C14 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R15 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R25 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| front-panel | SW5 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00046 |
| front-panel | C15 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R16 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R26 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| front-panel | SW6 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00046 |
| front-panel | C16 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R17 | [C25804](https://jlcpcb.com/partdetail/C25804) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07062 |
| front-panel | R27 | [C21190](https://jlcpcb.com/partdetail/C21190) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| front-panel | SW7 | [C83916](https://jlcpcb.com/partdetail/C83916) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.00046 |
| front-panel | C17 | [C14663](https://jlcpcb.com/partdetail/C14663) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 270.0 | 0.07396 |
| front-panel | R7 | [C23179](https://jlcpcb.com/partdetail/C23179) | sí | geometry_match | 0 | 0.0000 | 0.0000 | 0.0 | 0.07062 |
| front-panel | D1 | [C2286](https://jlcpcb.com/partdetail/C2286) | sí | geometry_match | 180 | 0.0000 | 0.0000 | 0.0 | 0.03693 |

## Notas por código LCSC

- **C397236:** BLOCKED: K701 holes span 20 mm; Omron G5RL-1A-E-HR requires 25 mm (20+5). Fix footprint/routing, not CPL. Source: https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5rl.pdf page 5.
- **C5169636:** REVIEW: paired tails differ by 2.5 mm with contact order preserved. Check TE drawing, locating post and harness pin 1; do not rotate to conceal a contact reversal.
- **C142716:** BLOCKED: BOM orders a leadless 0215002.MXP fuse, but PCB footprint is a pair of Littelfuse 111 clips. Clips are not separate BOM items. Resolve assembly BOM/mechanics.
- **C142789:** REVIEW: model lead pitch 25.50 mm versus PCB 27.50 mm; axial leads need forming. Confirm the assembly operation with JLCPCB.
- **C178840:** REVIEW: model is horizontal at 28 mm pitch, PCB is vertical at 5.08 mm. Requires lead forming/manual assembly; rotating a horizontal model cannot validate it.
- **C2687402:** DATASHEET CHECKED: KiCad pads 2.95 x 3.5 mm at +/-2.725 mm give 8.4 mm outer span and 2.5 mm gap, exactly the Bourns recommended layout. The public model uses different pad extensions. Center is unchanged; +180 degrees matches numbered pads (electrically equivalent for this inductor). Source: https://www.bourns.com/data/global/pdfs/SRP7028A.pdf page 1.
- **C2838912:** NO MODEL: public API has no PCB footprint. Nonpolarized 1206 fuse; retained original CPL, pending vendor preview.
- **C49326334:** NO MODEL: public API has no PCB footprint. Nonpolarized 0603 capacitor; retained original CPL, pending vendor preview.
- **C6280124:** Aliases verified by EasyEDA symbol (+V=3,-V=4) and Mean Well IRM-30-SPEC drawing 2026-04-03 page 4; local symbol uses +V=4,-V=3. Pad-envelope center is 10.5 mm from body origin.
- **C83916:** Switch has four physical tails but two electrical contacts; EasyEDA 1/2 map to local 1, 3/4 to local 2.
- **C575074:** Both tails belong to the same conductive FASTON tab. 90 and 270 degrees are electrically/geometrically equivalent; using 90.
- **C2149727:** Two tails per RAST contact: model 1/2->1,3/4->2,5/6->3,7/8->4. NPTH locating post must not shift the electrical pad center.
- **C2689964:** USB shell pad name EP in the vendor model corresponds to SH in KiCad.
