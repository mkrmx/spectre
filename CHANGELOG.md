# Changelog

Historial de todas las versiones de SPECTRE, de la más nueva a la más vieja.

Solo las versiones rev D y la THT rev E tienen archivos y etiqueta en este repositorio. Las versiones anteriores quedan documentadas aquí, pero sus archivos no están incluidos.

## [tht-rev-e] — 2026-10-28 — THT rev E
- **Apagado automático:** U4 CD4541 apaga la tira unos 10 minutos después de abrir la cajuela.
  - Q5 invierte HALL_OUT para manejar MR: el contador se queda en reset mientras la cajuela está cerrada.
  - En modo de ciclo único, TOUT se queda retenido en alto. Q6 lleva ARM a GND y la tira se apaga con fade.
  - Cerrar la cajuela reinicia el conteo, así que cada apertura empieza de cero.
  - Oscilador: R22 82 kΩ, C8 100 nF de película, R23 180 kΩ. Da T ≈ 618 s.
  - J5 (jumper de prueba) pone A en 0, unos 10 s.
- **Fade simétrico:** D5 + R6 39 kΩ forman el camino de apagado, separado del de encendido (D3 + R14 68 kΩ).
- **Consumo en reposo:** baja de unos 14 mA a unos 5 mA.
  - U1 LM7805 → LP2950-5.0 TO-92, con C2 de 0.1 µF → 10 µF.
  - Q3 NPN → PNP 2N3906, y R5 1 kΩ a +5 V → 4.7 kΩ a GND.
- **Placa:** 64 x 50 mm (antes 46 x 40) con esquinas redondeadas, sin barrenos y con franja libre de 1 mm.
  - Acomodo por bloques funcionales.
  - Sin vías.
  - DRC sin errores.
  - Gerbers en `tht/fab/spectre-tht-gerbers.zip`.
- **Esquemático propio de la versión THT:** `tht/spectre-tht.kicad_sch`.
- Probada en protoboard antes de subirla.

## [tht-rev-d] — 2026-10-16 — THT rev D
Versión through-hole del circuito rev D, para soldar a mano.
- **Medidas:** 46 x 40 mm (antes 70 x 50), sin barrenos y con franja libre de 1 mm en el borde para los rieles de la caja.
- **Montaje:** resistencias y diodos de señal de pie (paso 2.54 mm).
- **Retardo de armado:** el mismo de la SMT rev D (U3B, R15–R18, D4), con C6 de 22 µF electrolítico.
- **Sensores:** Hall y LDR por cable (J3, J4). C5 queda junto a J3 como desacoplo.
- **Conectores:** J1 y J2 pasan de bornera a JST VH (B2P-VH).
- **Piezas:** LM7805, IRLZ44N, LM393 DIP-8, 2N2222A, 1N4007 y 1N4148.
- **Sin logo:** la cara inferior no tiene espacio libre de pads.

## [smt-rev-d] — 2026-10-15 / 2026-10-16 — SMT rev D
- **Nuevo retardo de armado:** al abrir de día, el latch se armaba antes de que la LDR leyera la luz real.
  - R15 100 kΩ y C6 llevan HALL_OUT a DELAY.
  - D4 descarga C6 al cerrar.
  - R16 y R17 forman el umbral VTH de 2.5 V.
  - U3B (la mitad libre del LM393) compara DELAY contra VTH. Su salida ARM, con pull-up R18 de 10 kΩ, alimenta a R1 en lugar de HALL_OUT.
- **C6:** subió de 10 µF a 22 µF (≈ 1.5 s) después de probarlo en protoboard; con 10 µF el armado todavía le ganaba a la apertura.
- **Montaje:** se quitaron los barrenos; la caja sostiene la placa por los costados. Hay franja libre de 1 mm en todo el borde.
  - J2 se movió 0.4 mm, U2 0.3 mm y R9 0.5 mm para respetar la franja.
- **Nuevo esquemático cableado** (KiCad 7), enlazado a la PCB.
- **PCB re-ruteada:**
  - Referencias legibles junto a cada pieza.
  - Logo de 34.4 x 5.5 mm en la cara inferior.
  - DRC sin errores.
- **BOM:** C3 = Panasonic EEE-1CA470WR y C4 = EEE-1CA220WR.

## SMT ensamblada — 2026-10-09
Versión para que la fábrica la entregue con los componentes soldados.
- **R14:** 10 kΩ → 68 kΩ.
- **Hall en la placa:** U2 DRV5033FA (SOT-23), con C5 de 0.1 µF de desacoplo. Sustituye al A3144 remoto.
- **LDR en la placa:** LDR1 GL5528 (THT).
- **Conectores:** J1 y J2 pasan a JST B2P-VH. Se eliminaron J3 y J4.
- **Fabricación:** BOM con números de parte y CPL que incluye las piezas THT.

## SMT compacta
- **Medidas:** placa SMT reorganizada en 42 x 32 mm, aprovechando las dos capas.
- **Motivo:** la versión SMT anterior pasó las pruebas, pero era muy grande.

## SMT
- **Conversión a SMT:** primera versión SMT del circuito rev C, con Gerbers y archivos para montaje SMT.

## THT rev C — 2026-10-08
- **Fade al encender y apagar:**
  - C4 de 22 µF del gate a GND.
  - R6 sube a 100 kΩ (apagado lento).
  - D3 1N4148 + R14 10 kΩ en paralelo con R6 (encendido rápido).
  - R7 sube a 1 MΩ.
- **Logo MKr SPECTRE** en la serigrafía inferior, sin texto de revisión. Se reacomodaron D1, U1, Q4, J1, J2, C1 y C4 para hacerle espacio.
- **Primer esquemático en KiCad.**

## THT rev B
- **Mejoras en la lectura de la LDR:**
  - Histéresis en el comparador con R13.
  - Filtro con C3 de 47 µF.

## THT rev A
- **Primera placa:** 70 x 50 mm, 2 capas, todo through-hole.
- **Sensores remotos:** Hall A3144 y LDR GL5528.
- **Lógica:**
  - Comparador LM393 con umbral ajustable (R9).
  - Compuerta Y con dos NPN.
  - MOSFET IRLZ44N para la tira de 12 V.
  - Regulador LM7805.
