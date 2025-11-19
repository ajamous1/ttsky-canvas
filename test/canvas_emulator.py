#!/usr/bin/env python3
"""
Tiny Canvas Emulator
====================
A pygame-based visualization of the Tiny Canvas MS Paint-style project.
This emulator shows how the 16x16 grid canvas works with the color mixing
and movement logic implemented in the Verilog design.

Controls:
- Arrow Keys: Move cursor (Up/Down/Left/Right)
- R: Toggle Red
- G: Toggle Green  
- B: Toggle Blue
- SPACE: Toggle Brush/Eraser mode
- C: Clear canvas
- ESC/Q: Quit
"""

import pygame
import sys

# Color definitions (RGB tuples)
COLORS = {
    0b000: (0, 0, 0),         # Black/None
    0b100: (255, 0, 0),       # Red
    0b010: (0, 255, 0),       # Green
    0b001: (0, 0, 255),       # Blue
    0b110: (255, 255, 0),     # Yellow (R+G)
    0b101: (255, 0, 255),     # Magenta (R+B)
    0b011: (0, 255, 255),     # Cyan (G+B)
    0b111: (255, 255, 255),   # White (R+G+B)
}

class TinyCanvas:
    """Emulates the Tiny Canvas hardware logic."""
    
    def __init__(self):
        # Hardware state
        self.btn_up = False
        self.btn_down = False
        self.btn_right = False
        self.btn_left = False
        self.sw_red = False
        self.sw_green = False
        self.sw_blue = False
        self.sw_brush = True  # Start in brush mode
        
        # Canvas state (16x16 grid, each cell stores 3-bit color)
        self.grid_size = 256
        self.canvas = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Cursor position
        self.cursor_x = 7
        self.cursor_y = 7
        
        # For handling button press timing
        self.last_move_time = 0
        self.move_delay = 150  # milliseconds between moves
        
    def get_color_mix(self):
        """Implements the color mixing logic from canvas_core module."""
        if self.sw_brush:
            rgb_sel = (self.sw_red << 2) | (self.sw_green << 1) | self.sw_blue
            return rgb_sel
        else:
            # Eraser mode = no color
            return 0b000
    
    def get_buttons(self):
        """Returns button state as 4-bit value."""
        return (self.btn_up << 3) | (self.btn_down << 2) | (self.btn_right << 1) | self.btn_left
    
    def get_status(self):
        """Emulates the status output: {color_mix[2:0], buttons[3:0]}."""
        color_mix = self.get_color_mix()
        buttons = self.get_buttons()
        return (color_mix << 4) | buttons
    
    def update_cursor(self, current_time):
        """Update cursor position based on button presses."""
        if current_time - self.last_move_time < self.move_delay:
            return
        
        moved = False
        if self.btn_up and self.cursor_y > 0:
            self.cursor_y -= 1
            moved = True
        elif self.btn_down and self.cursor_y < self.grid_size - 1:
            self.cursor_y += 1
            moved = True
        elif self.btn_left and self.cursor_x > 0:
            self.cursor_x -= 1
            moved = True
        elif self.btn_right and self.cursor_x < self.grid_size - 1:
            self.cursor_x += 1
            moved = True
        
        if moved:
            self.last_move_time = current_time
            # Paint/erase when moving
            self.paint_at_cursor()
    
    def paint_at_cursor(self):
        """Paint or erase at current cursor position."""
        color = self.get_color_mix()
        self.canvas[self.cursor_y][self.cursor_x] = color
    
    def clear_canvas(self):
        """Clear the entire canvas."""
        self.canvas = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]


class CanvasEmulator:
    """Pygame-based GUI for the Tiny Canvas emulator."""
    
    def __init__(self):
        pygame.init()
        
        # Display settings
        self.cell_size = 30
        self.grid_size = 16
        self.canvas_width = self.cell_size * self.grid_size
        self.sidebar_width = 250
        self.window_width = self.canvas_width + self.sidebar_width + 40
        self.window_height = self.canvas_width + 40
        
        # Colors for UI
        self.bg_color = (40, 40, 40)
        self.grid_color = (80, 80, 80)
        self.cursor_color = (255, 255, 0)
        self.text_color = (220, 220, 220)
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Tiny Canvas Emulator")
        
        # Font
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        
        # Canvas logic
        self.canvas = TinyCanvas()
        
        # Clock
        self.clock = pygame.time.Clock()
        self.fps = 60
        
    def handle_events(self):
        """Handle keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Toggle switches
                if event.key == pygame.K_r:
                    self.canvas.sw_red = not self.canvas.sw_red
                elif event.key == pygame.K_g:
                    self.canvas.sw_green = not self.canvas.sw_green
                elif event.key == pygame.K_b:
                    self.canvas.sw_blue = not self.canvas.sw_blue
                elif event.key == pygame.K_SPACE:
                    self.canvas.sw_brush = not self.canvas.sw_brush
                elif event.key == pygame.K_c:
                    self.canvas.clear_canvas()
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
        
        # Handle arrow keys (held down)
        keys = pygame.key.get_pressed()
        self.canvas.btn_up = keys[pygame.K_UP]
        self.canvas.btn_down = keys[pygame.K_DOWN]
        self.canvas.btn_left = keys[pygame.K_LEFT]
        self.canvas.btn_right = keys[pygame.K_RIGHT]
        
        return True
    
    def draw_grid(self):
        """Draw the 16x16 canvas grid."""
        offset_x = 20
        offset_y = 20
        
        # Draw cells
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                rect = pygame.Rect(
                    offset_x + x * self.cell_size,
                    offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                # Fill with cell color
                color_value = self.canvas.canvas[y][x]
                color = COLORS[color_value]
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw grid lines
                pygame.draw.rect(self.screen, self.grid_color, rect, 1)
        
        # Draw cursor
        cursor_rect = pygame.Rect(
            offset_x + self.canvas.cursor_x * self.cell_size,
            offset_y + self.canvas.cursor_y * self.cell_size,
            self.cell_size,
            self.cell_size
        )
        pygame.draw.rect(self.screen, self.cursor_color, cursor_rect, 3)
    
    def draw_sidebar(self):
        """Draw the control panel sidebar."""
        sidebar_x = self.canvas_width + 40
        y_offset = 20
        
        # Title
        title = self.font_large.render("Tiny Canvas", True, self.text_color)
        self.screen.blit(title, (sidebar_x, y_offset))
        y_offset += 50
        
        # Current color preview
        color_value = self.canvas.get_color_mix()
        color = COLORS[color_value]
        color_rect = pygame.Rect(sidebar_x, y_offset, 60, 60)
        pygame.draw.rect(self.screen, color, color_rect)
        pygame.draw.rect(self.screen, self.text_color, color_rect, 2)
        
        # Color name
        color_names = {
            0b000: "Black",
            0b100: "Red",
            0b010: "Green",
            0b001: "Blue",
            0b110: "Yellow",
            0b101: "Magenta",
            0b011: "Cyan",
            0b111: "White",
        }
        color_text = self.font_medium.render(color_names[color_value], True, self.text_color)
        self.screen.blit(color_text, (sidebar_x + 70, y_offset + 15))
        y_offset += 80
        
        # Mode
        mode = "BRUSH" if self.canvas.sw_brush else "ERASER"
        mode_color = (0, 255, 0) if self.canvas.sw_brush else (255, 100, 100)
        mode_text = self.font_medium.render(f"Mode: {mode}", True, mode_color)
        self.screen.blit(mode_text, (sidebar_x, y_offset))
        y_offset += 40
        
        # RGB switches
        self.draw_switch_indicator(sidebar_x, y_offset, "R", self.canvas.sw_red, (255, 0, 0))
        y_offset += 30
        self.draw_switch_indicator(sidebar_x, y_offset, "G", self.canvas.sw_green, (0, 255, 0))
        y_offset += 30
        self.draw_switch_indicator(sidebar_x, y_offset, "B", self.canvas.sw_blue, (0, 0, 255))
        y_offset += 50
        
        # Cursor position
        pos_text = self.font_small.render(f"Position: ({self.canvas.cursor_x}, {self.canvas.cursor_y})", True, self.text_color)
        self.screen.blit(pos_text, (sidebar_x, y_offset))
        y_offset += 30
        
        # Status register (hex)
        status = self.canvas.get_status()
        status_text = self.font_small.render(f"Status: 0x{status:02X}", True, self.text_color)
        self.screen.blit(status_text, (sidebar_x, y_offset))
        y_offset += 40
        
        # Controls help
        y_offset += 20
        help_lines = [
            "Controls:",
            "Arrow Keys: Move",
            "R/G/B: Toggle color",
            "Space: Brush/Eraser",
            "C: Clear canvas",
            "ESC/Q: Quit",
        ]
        for line in help_lines:
            help_text = self.font_small.render(line, True, (180, 180, 180))
            self.screen.blit(help_text, (sidebar_x, y_offset))
            y_offset += 22
    
    def draw_switch_indicator(self, x, y, label, state, color):
        """Draw a switch indicator (on/off)."""
        # Label
        label_text = self.font_medium.render(label, True, self.text_color)
        self.screen.blit(label_text, (x, y))
        
        # Switch
        switch_x = x + 30
        switch_rect = pygame.Rect(switch_x, y, 40, 20)
        switch_color = color if state else (60, 60, 60)
        pygame.draw.rect(self.screen, switch_color, switch_rect)
        pygame.draw.rect(self.screen, self.text_color, switch_rect, 1)
        
        # State text
        state_text = "ON" if state else "OFF"
        state_render = self.font_small.render(state_text, True, self.text_color)
        self.screen.blit(state_render, (switch_x + 80, y + 2))
    
    def run(self):
        """Main emulator loop."""
        running = True
        
        print("=" * 50)
        print("Tiny Canvas Emulator Started!")
        print("=" * 50)
        print("Controls:")
        print("  Arrow Keys: Move cursor")
        print("  R/G/B: Toggle Red/Green/Blue")
        print("  Space: Toggle Brush/Eraser")
        print("  C: Clear canvas")
        print("  ESC/Q: Quit")
        print("=" * 50)
        
        while running:
            # Handle input
            running = self.handle_events()
            
            # Update canvas logic
            current_time = pygame.time.get_ticks()
            self.canvas.update_cursor(current_time)
            
            # Draw everything
            self.screen.fill(self.bg_color)
            self.draw_grid()
            self.draw_sidebar()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()
        print("\nEmulator closed. Thanks for using Tiny Canvas!")


def main():
    emulator = CanvasEmulator()
    emulator.run()


if __name__ == "__main__":
    main()

