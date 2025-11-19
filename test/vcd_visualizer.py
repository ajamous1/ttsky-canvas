#!/usr/bin/env python3
"""
VCD Visualizer for Tiny Canvas
================================
Reads the VCD waveform file and displays a visual representation
of how your Verilog color mixing logic works over time.
"""

import re
import sys

# Color definitions
COLORS = {
    '000': 'Black',
    '100': 'Red',
    '010': 'Green',
    '001': 'Blue',
    '110': 'Yellow',
    '101': 'Magenta',
    '011': 'Cyan',
    '111': 'White',
}

ANSI_COLORS = {
    'Black': '\033[90m',
    'Red': '\033[91m',
    'Green': '\033[92m',
    'Blue': '\033[94m',
    'Yellow': '\033[93m',
    'Magenta': '\033[95m',
    'Cyan': '\033[96m',
    'White': '\033[97m',
}
RESET = '\033[0m'


def parse_vcd(filename):
    """Parse VCD file and extract color_mix changes."""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find the color_mix variable identifier
    color_mix_id = None
    for line in content.split('\n'):
        if 'color_mix' in line and '$var reg 3' in line:
            # Extract the identifier (e.g., '9')
            match = re.search(r'\$var reg 3 (\S+) color_mix', line)
            if match:
                color_mix_id = match.group(1)
                break
    
    if not color_mix_id:
        print("Error: Could not find color_mix in VCD file")
        return []
    
    # Parse value changes
    events = []
    current_time = 0
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Time marker
        if line.startswith('#'):
            try:
                current_time = int(line[1:])
            except:
                pass
        
        # Color_mix value change (format: b<value> <id>)
        if line.startswith('b') and color_mix_id in line:
            match = re.search(r'b(\d+)', line)
            if match:
                value = match.group(1)
                # Pad to 3 bits
                value = value.zfill(3)
                events.append((current_time, value))
    
    return events


def visualize_vcd(filename):
    """Visualize the VCD color changes."""
    print("=" * 70)
    print("  TINY CANVAS - VCD WAVEFORM VISUALIZATION")
    print("=" * 70)
    print(f"\nReading: {filename}\n")
    
    events = parse_vcd(filename)
    
    if not events:
        print("No color_mix events found in VCD file.")
        return
    
    print(f"Found {len(events)} color change events\n")
    print("-" * 70)
    print(f"{'Time (ps)':<12} {'Color Mix':<12} {'Color':<12} {'Visual'}")
    print("-" * 70)
    
    for time, color_value in events:
        color_name = COLORS.get(color_value, 'Unknown')
        ansi_color = ANSI_COLORS.get(color_name, '')
        
        # Visual block
        visual = ansi_color + '█' * 10 + RESET
        
        print(f"{time:<12} {color_value:<12} {color_name:<12} {visual}")
    
    print("-" * 70)
    
    # Summary
    print("\n" + "=" * 70)
    print("  COLOR MIXING SUMMARY")
    print("=" * 70)
    
    color_counts = {}
    for _, color_value in events:
        color_name = COLORS.get(color_value, 'Unknown')
        color_counts[color_name] = color_counts.get(color_name, 0) + 1
    
    for color_name, count in sorted(color_counts.items(), key=lambda x: -x[1]):
        ansi_color = ANSI_COLORS.get(color_name, '')
        bar = ansi_color + '█' * (count * 2) + RESET
        print(f"  {color_name:<12} {bar} ({count} events)")
    
    print("=" * 70)


def main():
    vcd_file = 'tt_um_canvas.vcd'
    
    if len(sys.argv) > 1:
        vcd_file = sys.argv[1]
    
    try:
        visualize_vcd(vcd_file)
    except FileNotFoundError:
        print(f"Error: VCD file not found: {vcd_file}")
        print(f"\nUsage: python vcd_visualizer.py [vcd_file]")
        print(f"Default: python vcd_visualizer.py tt_um_canvas.vcd")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


