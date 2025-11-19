![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Tiny Canvas - Mini MS Paint for TinyTapeout

A 256×256 pixel canvas with 8-color mixing and I2C communication, designed for TinyTapeout.

## 🎨 What is Tiny Canvas?

Tiny Canvas is a simplified MS Paint-style drawing system implemented in Verilog for TinyTapeout. It features:

- **256×256 pixel canvas** - High resolution drawing surface
- **8-color mixing** - RGB color combinations (Red, Green, Blue, Yellow, Magenta, Cyan, White, Black)
- **I2C communication** - 3-byte protocol for hardware control
- **Interactive emulator** - Fullscreen pygame visualization tool
- **Coordinate system** - (0,0) at top-left, (255,255) at bottom-right

## 🖥️ Canvas Emulator

**Features a resizable windowed display (starts at 75% of your screen) that automatically scales!**

### Installation

```bash
pip install pygame
```

### Usage

```bash
python test/canvas_emulator.py
```

The emulator opens in a **resizable windowed mode** at 75% of your screen size. The canvas automatically scales to fit when you resize the window. Press **ESC** or **Q** to quit.

### Features
- 🔄 **Resizable window** - Drag corners/edges to resize, canvas scales automatically
- 📊 **Real-time I2C monitoring** - Live visualization of external commands
- 🎨 **256×256 pixel canvas** - Full color mixing support
- ⚡ **Fast external control** - Perfect for testbench integration

### How I2C Communication Works

The emulator simulates **real hardware I2C behavior** - I2C communication is **automatic and continuous**:

#### Automatic I2C Flow:
1. **State Change Detection**: Hardware monitors cursor position and color
2. **Automatic Transmission**: When state changes, automatically sends 3 bytes over I2C:
   - Byte 1: X coordinate (0-255)
   - Byte 2: Y coordinate (0-255)
   - Byte 3: Status byte (color in bits [6:4])
3. **Buffer Reception**: Bytes accumulate in I2C buffer (watch it fill: 0/3 → 1/3 → 2/3 → 3/3)
4. **Canvas Update**: When 3 bytes received, pixel is painted at (X, Y) with specified color

#### Why Automatic?
In real hardware, you don't manually trigger I2C. The hardware continuously:
- Monitors its state (position, color, brush mode)
- Detects changes
- Automatically transmits over I2C
- Receiving device processes the data

This emulator replicates that behavior! Just move the cursor or change colors, and watch the I2C buffer in the sidebar update automatically.

### Controls

| Key | Action | I2C Triggered? |
|-----|--------|----------------|
| Arrow Keys | Move cursor around 256×256 grid | ✅ Yes (auto) |
| R | Toggle Red | ✅ Yes (auto) |
| G | Toggle Green | ✅ Yes (auto) |
| B | Toggle Blue | ✅ Yes (auto) |
| Space | Toggle Brush/Eraser mode | ✅ Yes (auto) |
| C | Clear canvas | ❌ No |
| ESC/Q | Quit | ❌ No |

## 🔌 External I2C Control

The emulator can also receive I2C commands from external scripts, allowing you to programmatically control the canvas!

### Sending Commands Manually

Use the `send_i2c.py` script to send individual commands:

```bash
# Send a single command (while emulator is running)
python test/send_i2c.py 100 100 0x40  # Paint red at (100, 100)

# Or run interactively
python test/send_i2c.py
> 100 100 0x40
> 50 75 0x60
```

### Drawing Patterns Programmatically

Use the example script to draw patterns:

```bash
# Run the example drawer (emulator must be running)
python test/example_draw.py
```

This demonstrates:
- Drawing lines
- Drawing boxes
- Creating rainbow patterns
- Drawing a smiley face

### Creating Your Own Scripts

Write your own scripts to control the canvas:

```python
# your_script.py
def send_command(x, y, color):
    with open("i2c_commands.txt", 'a') as f:
        f.write(f"{x},{y},{color}\n")

# Draw a red horizontal line
for x in range(50, 100):
    send_command(x, 100, 0x40)  # 0x40 = Red
```

The emulator continuously monitors `i2c_commands.txt` and processes new commands in real-time!

### Testbench Integration

Perfect for hardware verification! The emulator provides **real-time visualization** of testbench activity:

```bash
# Terminal 1: Start emulator
python test/canvas_emulator.py

# Terminal 2: Run testbench
python test/testbench_example.py
```

**Testbench Features:**
- ✅ Real-time visualization of pixel writes as they happen
- ✅ Live activity indicator (● green dot when receiving commands)
- ✅ Command counter showing total commands received
- ✅ Zero latency - commands displayed immediately
- ✅ Perfect for verifying hardware logic and timing

**Create Your Own Testbench:**
```python
class MyTestbench:
    def send_i2c(self, x, y, status):
        with open("i2c_commands.txt", 'a') as f:
            f.write(f"{x},{y},{status}\n")
    
    def test_my_pattern(self):
        # Your test code here
        for i in range(100):
            self.send_i2c(i, 100, 0x40)  # Red line
            time.sleep(0.01)  # Watch it draw in real-time!
```

Watch the emulator's sidebar for:
- **External I2C: ACTIVE** (green) - Currently receiving commands
- **External I2C: Listening** (yellow) - Ready for commands
- **Commands: N** - Total external commands received

## I2C Protocol

The emulator simulates I2C communication with a 3-byte protocol:

- **Byte 1**: X coordinate (0-255)
- **Byte 2**: Y coordinate (0-255)  
- **Byte 3**: Status byte (color in bits [6:4])

### Example Usage

**Basic Drawing:**
1. Press **R** and **G** to select Yellow (110)
2. Press **RIGHT arrow** to move cursor right
3. Watch what happens:
   - Cursor moves from (128, 128) to (129, 128)
   - I2C automatically sends: [0x81, 0x80, 0x60]
   - Buffer fills: 0/3 → 1/3 → 2/3 → 3/3
   - Yellow pixel painted at (129, 128)!

**Change Color Mid-Draw:**
1. Already at position (129, 128)
2. Press **B** to add Blue (now Yellow+Blue = White)
3. I2C automatically sends: [0x81, 0x80, 0x70]
4. White pixel painted at same position!

**Watch the Sidebar:**
- I2C Communication section shows buffer status
- Last I2C command displays actual hex bytes:
  - **Byte 1 (X)**: `0x64` = 100
  - **Byte 2 (Y)**: `0x64` = 100  
  - **Byte 3 (Status)**: `0x60` with decoded color
- See exactly what's being transmitted in hex!

## Colors

The emulator demonstrates the 8-color mixing logic:

| RGB | Binary | Color |
|-----|--------|-------|
| 000 | `3'b000` | Black |
| 100 | `3'b100` | Red |
| 010 | `3'b010` | Green |
| 001 | `3'b001` | Blue |
| 110 | `3'b110` | Yellow (R+G) |
| 101 | `3'b101` | Magenta (R+B) |
| 011 | `3'b011` | Cyan (G+B) |
| 111 | `3'b111` | White (R+G+B) |

## 🔧 Hardware Design

The Verilog design is located in `src/project.v` and implements:

- **Color mixing logic** - Combinational logic for RGB mixing
- **I2C interface** - Slave interface on bidirectional pins
- **Button inputs** - Active-low momentary pushbuttons
- **Switch inputs** - Level-sensitive RGB and brush/eraser controls
- **Status output** - 8-bit bus containing color and button state

### Pin Mapping

**Inputs (`ui_in[7:0]`):**
- `ui_in[7]` - Brush/Eraser switch
- `ui_in[6:3]` - Buttons (Up, Down, Right, Left) - active-low
- `ui_in[2:0]` - RGB switches (Red, Green, Blue)

**Outputs (`uo_out[7:0]`):**
- `uo_out[6:4]` - Color mix (RGB)
- `uo_out[3:0]` - Button states

**Bidirectional (`uio[7:0]`):**
- `uio[3]` - I2C SCL
- `uio[2]` - I2C SDA

## 🧪 Testing

Run the cocotb tests:

```bash
cd test
make
```

## 📚 What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

## 🎯 Project Structure

```
ttsky-canvas/
├── src/
│   ├── project.v               # Main Verilog design
│   └── config.json             # Configuration
├── test/
│   ├── canvas_emulator.py      # Pygame emulator (resizable window)
│   ├── send_i2c.py            # Manual I2C command sender
│   ├── example_draw.py         # Pattern drawing examples
│   ├── testbench_example.py    # Testbench integration example
│   ├── test_external_i2c.py    # Test external I2C
│   ├── EXTERNAL_I2C_GUIDE.txt  # External I2C reference
│   ├── test.py                # Cocotb tests
│   └── Makefile               # Test runner
├── info.yaml                  # Project metadata
└── README.md                  # This file
```

## 🚀 Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)

## 👥 Authors

Ahmad Jamous & Armita Bhatti

## 📝 License

Apache-2.0

---

**Enjoy your Tiny Canvas! 🎨✨**
