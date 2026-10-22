# SPECTRE THT — rev D (46 x 40 mm)

Es el mismo circuito que la rev D SMT, incluido el retardo de armado con C6 de 22 µF, pero con piezas through-hole. El Hall y la LDR van fuera de la placa, conectados por cable a J3 y J4.

## Placa
- **Medidas:** 46 x 40 mm, 2 capas, FR-4 1.6 mm, cobre 1 oz. Sin barrenos de montaje.
- **Franja libre de 1 mm en todo el contorno** para los rieles de la caja: no hay cobre ni componentes a menos de 1 mm del borde.
- **Resistencias y diodos de señal van de pie:** paso de 2.54 mm, con el cuerpo parado sobre el pad que tiene el círculo de serigrafía. Así es como la placa queda tan compacta.
- **Pistas:** las de potencia (+12 V y LED−) son de 1.2 mm y las de señal de 0.4 mm. GND va por planos en ambas caras.
- **Verificación:**
  - DRC: 0 errores y 0 conexiones pendientes.
  - Netlist comparada pin por pin contra la rev D: 38 componentes, 21 redes, 0 diferencias.
- **Sin logo:** con piezas THT la cara inferior queda llena de pads y el logo solo cabría de unos 2.6 mm de alto, ilegible. Se dejó fuera.

## Archivos
- `fab/spectre-tht-gerbers.zip`: Gerbers (cobre, máscara, serigrafía, contorno) y taladros. Es lo que se sube a la fábrica.
- `img/mapa-ensamble.png`: dónde va cada pieza. En rojo, las del retardo.

- `spectre-tht.kicad_pcb` / `spectre-tht.kicad_pro`: PCB en KiCad 7 (sin esquemático propio: usa el de `../docs`, con U2 y LDR1 sustituidos por J3 y J4).
- `fab/drc.rpt`: DRC sin errores.

![Vista superior](img/vista-superior.png)

## Lista de componentes
| Ref | Valor | Tipo / encapsulado |
|---|---|---|
| R1, R2, R3, R4, R8, R10, R11, R12, R18 | 10 kΩ (x9) | Resistencia 1/4 W, montaje vertical |
| R6, R13, R15, R16, R17 | 100 kΩ (x5) | Resistencia 1/4 W, montaje vertical |
| R14 | 68 kΩ | Resistencia 1/4 W, montaje vertical |
| R5 | 1 kΩ | Resistencia 1/4 W, montaje vertical |
| R7 | 1 MΩ | Resistencia 1/4 W, montaje vertical |
| R9 | 10 kΩ | Trimpot multivuelta Bourns 3296W (vertical) |
| C1 | 0.33 µF 50 V | Cerámico (disco o multicapa), paso 2.5 mm |
| C2, C5 | 0.1 µF 50 V (x2) | Cerámico (disco o multicapa), paso 2.5 mm |
| C3 | 47 µF 16 V | Electrolítico radial 5 mm, paso 2 mm |
| C4, C6 | 22 µF 16 V (x2) | Electrolítico radial 5 mm, paso 2 mm |
| D1 | 1N4007 | Rectificador DO-41, vertical, paso 5.08 mm |
| D2, D3, D4 | 1N4148 (x3) | Diodo de señal DO-35, vertical |
| Q1, Q2, Q3 | 2N2222A / PN2222A (x3) | NPN TO-92 (E-B-C) |
| Q4 | IRLZ44N | MOSFET N nivel lógico TO-220 |
| U1 | LM7805 | Regulador 5 V TO-220 |
| U3 | LM393 | Comparador dual DIP-8 (zócalo opcional) |
| J1, J2 | JST B2P-VH | Header VH 2 pines vertical; carcasa VHR-2N del lado del cable |
| J3 | Header 1x3, 2.54 mm | Cable al sensor Hall |
| J4 | Header 1x2, 2.54 mm | Cable a la LDR |

**Fuera de la placa:**
- Sensor Hall: DRV5033FAQLPG (TO-92, omnipolar) o A3144, más un imán de neodimio.
- LDR GL5528.
- Conectores hembra Dupont de 3 y 2 pines.
- Fusible de 2 A en la línea de 12 V.

## Conectores
- J1: 1 = +12 V del auto, 2 = GND.
- J2: 1 = LED+ (+12 V), 2 = LED−.
- J3 (Hall): 1 = +5 V, 2 = GND, 3 = salida del Hall.
- J4 (LDR): 1 = LDR_DIV, 2 = GND.

El pin 1 de cada conector es el pad cuadrado. C5 queda junto a J3 como desacoplo del Hall. Si el cable al sensor mide más de unos 50 cm, suelda otro 0.1 µF directo en las patas del sensor.

## Orientación al soldar
- **Electrolíticos (C3, C4, C6):** la pata larga (+) va al pad marcado "+". La mitad sombreada del círculo es el lado negativo.
- **Diodos (D1–D4):** la banda del cátodo va al pad cuadrado (marcado "K" en D1–D3).
- **Q1–Q3:** pad cuadrado = emisor, luego base y colector (PN2222A/2N2222A de plástico). La cara plana va según el dibujo de la serigrafía.
- **Q4 y U1:** la pestaña metálica va hacia la franja angosta del rectángulo de serigrafía (la que está dividida en tres). Q4 = G-D-S; U1 = IN-GND-OUT.
- **U3:** el pin 1 es el pad cuadrado, del lado de la muesca.

## Ajuste y retardo
- **R9:** de noche, con la cajuela abierta, tapa la LDR y gira hasta que encienda. Para repetir, acerca y aleja el imán y espera ~2 s.
- **Retardo de armado:** con C6 de 22 µF y R15 de 100 kΩ arma unos 1.5 s después de abrir (±20 % por la tolerancia del electrolítico).
- **Puntos de medición en U3:** pin 6 ≈ 2.5 V; el pin 5 sube lento al abrir; el pin 7 pasa de 0 a 5 V cuando arma.
