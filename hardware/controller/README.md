# Controladora principal

[Diseño de la principal en KiCad](core-design.md): STM32G431RBT6 y
ESP32-S3-WROOM-1U-N8R8 con antena externa U.FL, reset, depuración, UART y USB-C
de servicio. La fuente Mean Well IRM-30-24 va en la propia placa; de sus 24 V
salen el buck de 12 V y, tras él, el de 3,3 V y el corte del frontal. Incluye el
acondicionamiento de NTC, caudalímetro, nivel de agua y tres contactos; un
DRV8876 para el motor del grupo y una etapa low-side para la válvula, cada uno
con su fusible; y las etapas de triac de calentador, bomba y molinillo detrás de
un relé general K701. Un TPS3828 supervisa el STM32 y las puertas AND U602–U604
anulan todas las órdenes de carga y el armado del relé mientras hay reset.

198 posiciones: 193 con MPN y código LCSC; J115 y J117 (LEOCO, que JLCPCB no
tiene) con MPN y sin código; RV701 con valor provisional y sin pieza; J111 y
J121, puentes de soldadura. Los tres fusibles de red son Littelfuse 215 de
1500 A a 250 VAC (F702 en pinzas 01110501Z; F701, de 12 A, soldado). J105, J106 y J113 (JP13, JP5 y JP3)
son HR A2506WV, JP8 y JP24 LEOCO 3941P03*000 y 5001P020013, JP17 y JP19 TE RAST 5
1971845-3 y -4 y JP1/JP9 lengüetas TE 63824-1, todas identificadas por el
propietario o casadas con sus fotos. J107–J109 (JP14, JP16 y JP22) siguen con
cabeceras JST candidatas que la revisión con nonio no confirma.

La PCB es de cuatro capas, JLC04161H-7628, con planos de GND y 3,3 V solo en el
lado SELV, y está [colocada y ruteada](layout.md) en las posiciones de la placa
original: DRC con todas las severidades sin infracciones ni conexiones abiertas.
La barrera red/SELV de 8 mm es una regla del DRC. Detalle del proyecto en
[kicad-workflow.md](../kicad-workflow.md); reglas y apilado en
[manufacturing.md](manufacturing.md); arquitectura de potencia en
[power-architecture.md](../power/power-architecture.md); suministro en
[assembly](../assembly/README.md).

El [contrato del frontal](front-panel-interface.md) fija J104 y los GPIO del
ESP32 para pantalla, botones, UART y USB. Dos divisores permiten leer por ADC los
rails de 12 V y 24 V, y J114 facilita su medida directa durante las pruebas.

**No es fabricable.** Falta comprobar la placa impresa 1:1 contra la original y
los mazos, identificar JP14, JP16 y JP22, cerrar RV701, el valor de F702 y el filtro EMI,
medir las cargas y pasar una revisión independiente de aislamiento. Nada está
ensayado. No trasladar pines de una placa de desarrollo al arnés sin verificación.
