#!/usr/bin/env python3
"""
Example: Draw patterns using external I2C commands
===================================================
This script demonstrates how to send I2C bytes to the emulator
to draw various patterns.

Make sure the emulator is running before executing this script!
"""

import time
import os

def send_command(x, y, color):
    """Send a single I2C command."""
    with open("i2c_commands.txt", 'a') as f:
        f.write(f"{x},{y},{color}\n")

def clear_commands():
    """Clear the command file."""
    if os.path.exists("i2c_commands.txt"):
        os.remove("i2c_commands.txt")

def draw_horizontal_line(x_start, y, length, color):
    """Draw a horizontal line."""
    for x in range(x_start, x_start + length):
        send_command(x, y, color)
        time.sleep(0.01)  # Small delay for visualization

def draw_vertical_line(x, y_start, length, color):
    """Draw a vertical line."""
    for y in range(y_start, y_start + length):
        send_command(x, y, color)
        time.sleep(0.01)

def draw_box(x, y, width, height, color):
    """Draw a box outline."""
    # Top and bottom
    for i in range(width):
        send_command(x + i, y, color)
        send_command(x + i, y + height - 1, color)
        time.sleep(0.01)
    
    # Left and right
    for i in range(height):
        send_command(x, y + i, color)
        send_command(x + width - 1, y + i, color)
        time.sleep(0.01)

def draw_smiley():
    """Draw a simple smiley face."""
    print("Drawing smiley face...")
    
    # Face outline (yellow)
    center_x, center_y = 128, 128
    radius = 20
    yellow = 0x0E  # RGB: 110 (Brush + Yellow)
    
    # Simple circle approximation
    for angle in range(0, 360, 5):
        import math
        x = int(center_x + radius * math.cos(math.radians(angle)))
        y = int(center_y + radius * math.sin(math.radians(angle)))
        send_command(x, y, yellow)
        time.sleep(0.01)
    
    # Left eye (blue)
    blue = 0x09  # RGB: 001 (Brush + Blue)
    for i in range(3):
        for j in range(3):
            send_command(center_x - 8 + i, center_y - 6 + j, blue)
    
    # Right eye (blue)
    for i in range(3):
        for j in range(3):
            send_command(center_x + 6 + i, center_y - 6 + j, blue)
    
    # Smile (red)
    red = 0x0C  # RGB: 100 (Brush + Red)
    for x in range(-10, 11):
        y = int(abs(x) * 0.3)
        send_command(center_x + x, center_y + 5 + y, red)
        time.sleep(0.01)

def draw_rainbow():
    """Draw vertical rainbow stripes."""
    print("Drawing rainbow...")
    
    colors = [
        (0x0C, "Red"),      # Brush + Red
        (0x0E, "Yellow"),   # Brush + Yellow
        (0x0A, "Green"),    # Brush + Green
        (0x0B, "Cyan"),     # Brush + Cyan
        (0x09, "Blue"),     # Brush + Blue
        (0x0D, "Magenta"),  # Brush + Magenta
    ]
    
    stripe_width = 10
    start_x = 80
    
    for i, (color, name) in enumerate(colors):
        print(f"  Drawing {name} stripe...")
        x = start_x + i * stripe_width
        for dx in range(stripe_width):
            for y in range(100, 156):
                send_command(x + dx, y, color)
                time.sleep(0.001)

def main():
    print("=" * 60)
    print("External I2C Drawing Examples")
    print("=" * 60)
    print("\nMake sure the canvas emulator is running!")
    print("  python test/canvas_emulator.py")
    print()
    
    # Clear previous commands
    print("Clearing previous commands...")
    clear_commands()
    time.sleep(0.1)  # Brief pause to let emulator detect
    
    choice = input("\nChoose pattern:\n  1. Rainbow\n  2. Smiley\n  3. Box\n  4. Lines\n\nChoice (1-4): ")
    
    print("\nDrawing... (watch the emulator)")
    print()
    
    if choice == "1":
        draw_rainbow()
    elif choice == "2":
        draw_smiley()
    elif choice == "3":
        # Draw a colored box
        draw_box(90, 90, 40, 40, 0x0D)  # Magenta box (Brush + Magenta)
        print("Drew magenta box")
    elif choice == "4":
        # Draw some lines
        draw_horizontal_line(80, 100, 50, 0x0C)  # Red line (Brush + Red)
        draw_vertical_line(100, 80, 50, 0x0A)    # Green line (Brush + Green)
        print("Drew red horizontal and green vertical lines")
    else:
        print("Invalid choice")
        return
    
    print("\nDone! Check the emulator window.")
    print("=" * 60)

if __name__ == "__main__":
    main()

