#!/usr/bin/env python3
"""
Testbench Example for Tiny Canvas Emulator
===========================================
This demonstrates how to send I2C commands from a testbench script
for real-time visualization in the emulator.

Usage:
    1. Start the emulator: python test/canvas_emulator.py
    2. Run this testbench: python test/testbench_example.py
    3. Watch the emulator display the test patterns in real-time!
"""

import time
import os

class CanvasTestbench:
    """
    A testbench class that sends I2C commands to the canvas emulator.
    Simulates hardware testbench behavior.
    """
    
    def __init__(self, command_file="i2c_commands.txt"):
        self.command_file = command_file
        self.clear_commands()
    
    def clear_commands(self):
        """Clear previous commands."""
        if os.path.exists(self.command_file):
            os.remove(self.command_file)
    
    def send_i2c(self, x, y, status, delay=0.0):
        """
        Send an I2C command (3 bytes).
        
        Args:
            x: X coordinate (0-255)
            y: Y coordinate (0-255)
            status: Status byte (color in bits [6:4])
            delay: Optional delay after sending (seconds)
        """
        with open(self.command_file, 'a') as f:
            f.write(f"{x},{y},{status}\n")
        
        if delay > 0:
            time.sleep(delay)
    
    def test_pixel_write(self):
        """Test: Write individual pixels."""
        print("TEST 1: Individual pixel writes")
        colors = [
            (0x0C, "Red"),      # Brush + Red
            (0x0A, "Green"),    # Brush + Green
            (0x09, "Blue"),     # Brush + Blue
            (0x0E, "Yellow"),   # Brush + Yellow
            (0x0D, "Magenta"),  # Brush + Magenta
            (0x0B, "Cyan"),     # Brush + Cyan
            (0x0F, "White"),    # Brush + White
        ]
        
        for i, (color, name) in enumerate(colors):
            x, y = 100 + i * 2, 100
            print(f"  Writing {name} pixel at ({x}, {y})")
            self.send_i2c(x, y, color, delay=0.2)
    
    def test_line_scan(self):
        """Test: Scan a horizontal line."""
        print("\nTEST 2: Horizontal line scan (Red)")
        y = 110
        for x in range(90, 120):
            self.send_i2c(x, y, 0x0C, delay=0.02)  # Red pixels (Brush + Red)
            if x % 10 == 0:
                print(f"  Scanning x={x}")
    
    def test_vertical_scan(self):
        """Test: Scan a vertical line."""
        print("\nTEST 3: Vertical line scan (Green)")
        x = 130
        for y in range(90, 120):
            self.send_i2c(x, y, 0x0A, delay=0.02)  # Green pixels (Brush + Green)
            if y % 10 == 0:
                print(f"  Scanning y={y}")
    
    def test_box_fill(self):
        """Test: Fill a box area."""
        print("\nTEST 4: Box fill (Blue)")
        start_x, start_y = 140, 100
        width, height = 10, 10
        
        for y in range(start_y, start_y + height):
            for x in range(start_x, start_x + width):
                self.send_i2c(x, y, 0x09, delay=0.01)  # Blue pixels (Brush + Blue)
            print(f"  Filled row y={y}")
    
    def test_pattern_animation(self):
        """Test: Animated pattern."""
        print("\nTEST 5: Animated diagonal sweep")
        
        # Sweep diagonally
        for offset in range(20):
            for i in range(10):
                x = 160 + i
                y = 100 + offset + i
                if y < 256:
                    # Alternate colors (Yellow and Magenta)
                    color = 0x0E if (i + offset) % 2 == 0 else 0x0D
                    self.send_i2c(x, y, color, delay=0.005)
            print(f"  Sweep offset={offset}")
    
    def test_rapid_updates(self):
        """Test: Rapid position updates (simulates cursor movement)."""
        print("\nTEST 6: Rapid cursor simulation (circle at center)")
        
        # Move cursor in a circle at center of canvas
        import math
        center_x, center_y = 128, 128
        radius = 15
        
        for angle in range(0, 360, 5):
            rad = math.radians(angle)
            x = int(center_x + radius * math.cos(rad))
            y = int(center_y + radius * math.sin(rad))
            self.send_i2c(x, y, 0x0F, delay=0.01)  # White trail (Brush + White)
            if angle % 45 == 0:
                print(f"  Cursor at angle={angle}°, pos=({x},{y})")
    
    def run_all_tests(self):
        """Run all testbench tests."""
        print("=" * 60)
        print("Canvas Emulator Testbench")
        print("=" * 60)
        print("\nMake sure the emulator is running!")
        print("  python test/canvas_emulator.py")
        print()
        input("Press Enter to start tests...")
        
        print("\nClearing previous commands and starting tests...\n")
        self.clear_commands()  # Clear before starting
        time.sleep(0.1)  # Brief pause to let emulator detect
        
        self.test_pixel_write()
        time.sleep(0.5)
        
        self.test_line_scan()
        time.sleep(0.5)
        
        self.test_vertical_scan()
        time.sleep(0.5)
        
        self.test_box_fill()
        time.sleep(0.5)
        
        self.test_pattern_animation()
        time.sleep(0.5)
        
        self.test_rapid_updates()
        
        print("\n" + "=" * 60)
        print("All tests complete!")
        print("Check the emulator window for results.")
        print("=" * 60)


def main():
    tb = CanvasTestbench()
    tb.run_all_tests()


if __name__ == "__main__":
    main()

