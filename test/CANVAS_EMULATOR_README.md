# Canvas Emulator

A pygame-based visualization tool for the Tiny Canvas project.

## Installation

```bash
pip install pygame
```

## Usage

```bash
python test/canvas_emulator.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move cursor around 16×16 grid |
| R | Toggle Red |
| G | Toggle Green |
| B | Toggle Blue |
| Space | Toggle Brush/Eraser mode |
| C | Clear canvas |
| ESC/Q | Quit |

## Colors

The emulator demonstrates the 8-color mixing logic:

- Black (000), Red (100), Green (010), Blue (001)
- Yellow (110), Magenta (101), Cyan (011), White (111)

## Waveform Visualization

View VCD waveform data from your Verilog simulation:

```bash
python test/vcd_visualizer.py test/tt_um_canvas.vcd
```

This shows the actual color_mix output from your Verilog design over time.


