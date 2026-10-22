"""Top-side label check: mask openings, silkscreen and courtyards rendered by kicad-cli, black background."""
import sys, subprocess, cairosvg, os
f, out = sys.argv[1], sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
svg = out + ".svg"
subprocess.run(["kicad-cli", "pcb", "export", "svg", "--layers", sys.argv[4] if len(sys.argv) > 4 else "F.Mask,F.SilkS,F.CrtYd,Edge.Cuts",
                "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", svg, f], capture_output=True)
cairosvg.svg2png(url=svg, write_to=out, output_width=w, background_color="black"); os.remove(svg)
