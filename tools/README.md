# Herramientas de diseño

Estos scripts generaron el esquemático y las PCB de rev D a partir de la netlist: acomodo automático, ruteo, planos, serigrafía, logo, verificación y exportación. Sirven para hacer la siguiente revisión con el mismo proceso.

## Requisitos
- **KiCad 7** con su módulo de Python (`pcbnew`) y `kicad-cli`. Están probados con KiCad 7.0.11 en Linux.
- **Python 3** con `shapely`, `cairosvg`, `Pillow` y `numpy`.
- **Java 17 o más** y **Freerouting 2.1.0**. Descarga el `.jar` de la [release v2.1.0](https://github.com/freerouting/freerouting/releases/tag/v2.1.0) y guárdalo como `tools/fr.jar`; no se versiona.
- **Para que el DRC compare las huellas contra la librería:** exporta `KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints`. También necesitas `fp-lib-table` en la configuración de KiCad.

## Estructura
| Ruta | Qué hace |
|---|---|
| `sch/gen.py`, `sexp.py` | Genera el esquemático cableado (`.kicad_sch`). Parte los cables en las uniones en T y pone símbolos de alimentación. |
| `sch/verify.py` | Compara la netlist del esquemático contra el mapa de redes esperado, pin por pin. |
| `revd/netmap_sch.json` | Redes, valores, huellas y UUID de símbolo de cada pieza SMT. Se extrae del esquemático y es la entrada de todo lo demás. |
| `tht/netmap_tht.json` | Lo mismo para la versión THT: U2 → J3, LDR1 → J4, huellas THT, Q1–Q3 con orden E-B-C. |
| `*/geom.py`, `geom2.py` | Calcula el courtyard, los pads y los posibles lugares para la etiqueta de cada huella en sus cuatro rotaciones. |
| `revd/anneal2.py`, `tht/anneal.py` | Acomodo por recocido simulado: longitud de conexiones, sin traslapes, etiquetas legibles, franja libre en el borde y conectores en la orilla (THT). |
| `revd/labL_24.json`, `tht/bL_14.json` | Acomodos finales de rev D. |
| `revd/build_revd.py`, `tht/build.py` | Arma el `.kicad_pcb` desde la netlist y el acomodo: reglas, clases de red, contorno y plano de GND. |
| `revd/route_revd.py`, `tht/route.py` | Exporta a DSN con zonas prohibidas en el borde, rutea con Freerouting, importa la sesión y rellena los planos. |
| `stitch.py`, `revd/addvias.py`, `clearvias.py`, `gndvia.py` | Vías de cosido en islas de GND, vías extra, liberar una zona de vías y conectar un pad de GND aislado. |
| `labels.py`, `refine.py`, `fixlabels.py`, `revd/labfix.py`, `tht/labfix.py` | Acomodo y corrección de referencias en la serigrafía. |
| `logo.py`, `tht/logo.py`, `logo_polys.pkl` | Coloca el logo en la serigrafía inferior, del mayor tamaño posible sin pads ni vías. |
| `revd/drc_revd.py` | DRC con `pcbnew.WriteDRCReport` (`kicad-cli` 7 no trae DRC). |
| `revd/verify_pcb.py`, `tht/verify.py` | Compara la PCB contra la netlist: redes por pad, valores, huellas y enlace a símbolos. |
| `revd/export_revd.py` | Exporta el paquete SMT: Gerbers, taladros, BOM, CPL, vistas, mapa de ensamble y DRC. |
| `render.py`, `revd/asmmap.py`, `revd/silkview.py`, `*/map.py` | Imágenes: vista inferior con logo, mapa de ensamble, revisión de serigrafía y mapa del acomodo. |

## Flujo (SMT)
```bash
cd tools/revd
python3 geom.py && python3 geom2.py                      # si cambian las huellas
python3 anneal2.py seed=24 init=labL_24.json out=nuevo.json   # acomodo
python3 route_revd.py nuevo.json X 40                    # → r_X/routed.kicad_pcb
python3 ../stitch.py r_X/routed.kicad_pcb
python3 drc_revd.py r_X/routed.kicad_pcb
python3 verify_pcb.py r_X/routed.kicad_pcb
```
Para THT, el flujo es el mismo con los scripts de `tools/tht`.

Los scripts se escribieron para una sesión concreta y algunos valores están fijos en el código: tamaño de placa, piezas ancladas y pares de desacoplo. Revísalos antes de reutilizarlos.
