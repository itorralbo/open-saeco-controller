# Modelos 3D de sustitución

Los genera `tools/make_controller_3d_models.py`; no se editan a mano.

**Alcance:** son cuerpos simplificados (cajas para cuerpo, pines y lengüetas,
sin redondeos, pestillos, marcas ni detalle interior) para los renders y para
juzgar holguras a ojo. No sirven para exportar a CAD mecánico, comprobar el
encaje en la carcasa ni medir distancias de aislamiento. La planta sigue la
huella; las alturas marcadas como estimadas no proceden de un plano.

Las huellas de `OpenSaeco.pretty` llevan el modelo en la biblioteca y en la
placa. Las de la biblioteca de KiCad cuyo modelo falta en KiCad 10.0 lo llevan
solo en la placa: si se vuelven a importar desde la biblioteca, hay que repetir
el script.

| Huella | Placa | Origen de las medidas |
|---|---|---|
| `HR_A2506WV-02P_1x02_P2.50mm_Vertical` | J105 | Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH). |
| `HR_A2506WV-03P_1x03_P2.50mm_Vertical` | J106 | Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH). |
| `HR_A2506WV-05P_1x05_P2.50mm_Vertical` | J113 | Planta del plano HR A2506WV-XP; altura de 6,0 mm estimada (familia XH). |
| `LEOCO_3941P03_1x03_P3.96mm_Vertical` | J115 | Planta del plano LEOCO 394105S; altura de 11 mm y rampa estimadas (familia VH). |
| `LEOCO_5001P02_1x02_P5.00mm_Vertical` | J117 | Planta del plano LEOCO 500101S; altura de 11 mm y rampa estimadas. |
| `TE_RAST5_1971845-3_1x03_P5.00mm_Vertical` | J118 | Carcasa 17,3 x 14,9 x 12,8 mm del plano TE C-1971845; paredes y lengüetas simplificadas. |
| `TE_RAST5_1971845-4_1x04_P5.00mm_Vertical` | J116 | Carcasa 22,3 x 14,9 x 12,8 mm del plano TE C-1971845; paredes y lengüetas simplificadas. |
| `TE_FASTON_63824-1_Tab_6.35mm_Vertical` | J119, J120 | Lengüeta de 6,35 x 0,81 mm del plano TE C-63824; altura de unos 9 mm estimada. |
| `Relay_SPST_Omron_G5RL-1A-E-TV8` | K701 | Planta de 29 x 12,7 mm de la serigrafía; 15,7 mm de alto según la serie G5RL, sin cotejar con el plano. |
| `MeanWell_IRM-30_THT` | PS701 | Caja de 69,5 x 39 x 24 mm del plano Mean Well IRM-30. |
| `USB_C_Receptacle_HRO_TYPE-C-31-D-06_Vertical` | J110 | Carcasa de 8,94 x 3,16 x 6,40 mm del plano HRO; sin contactos internos. |
| `Fuse_2410_JDT_JFC2410` | F703 | Cuerpo de 6,1 x 2,5 mm de la hoja JDT JFC2410; altura de 1,2 mm estimada. |
| `ESP32-S3-WROOM-1U` | U201 | Planta de 18 x 19,2 mm de la huella; 3,2 mm de alto según la hoja Espressif, sin cotejar; blindaje y U.FL simplificados. |
| `L_Bourns-SRN6028` | L301 | Bloque de 6,0 x 6,0 x 2,8 mm según la serie Bourns SRN6028, sin cotejar con el plano. |
| `L_Bourns_SRP7028A_7.3x6.6mm` | L302 | Planta de 7,3 x 6,6 mm de la huella; 2,8 mm de alto según la serie SRP7028A, sin cotejar. |
| `Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal` | F701, F702 | Clips en la planta de la huella con fusible de 5 x 20 mm; altura de 9 mm estimada. |
| `HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm` | U501 | STEP de KiCad del mismo cuerpo 4,4 x 5 mm; solo cambia la pastilla térmica, que no se ve. |
