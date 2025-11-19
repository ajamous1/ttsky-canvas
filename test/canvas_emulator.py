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
        
        # Canvas state (256x256 grid, each cell stores 3-bit color)
        self.grid_size = 256
        self.canvas = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Cursor position (start at bottom-left)
        self.cursor_x = 0
        self.cursor_y = 0
        
        # For handling button press timing
        self.last_move_time = 0
        self.move_delay = 150  # milliseconds between moves
        
        # I2C communication state
        self.i2c_buffer = []  # Buffer for incoming I2C bytes
        self.i2c_x = 0
        self.i2c_y = 0
        self.i2c_status = 0
        self.i2c_enabled = True  # I2C is always active
        self.i2c_last_state = None  # Track last state to detect changes
        
        # External I2C command file
        self.i2c_command_file = "i2c_commands.txt"
        self.i2c_file_position = 0  # Track where we are in the file
        self.external_commands_received = 0  # Count of external commands
        self.last_external_command_time = 0  # Time of last external command
        
        # Keyboard input mode
        self.keyboard_input_mode = False
        self.keyboard_input_buffer = ""
        self.last_keyboard_command = ""
        self.keyboard_command_status = ""  # Success/error message
        
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
        """
        Emulates the status output matching hardware pinout.
        Status Byte [7:0]:
          [7] = Up button
          [6] = Down button
          [5] = Left button
          [4] = Right button
          [3] = Brush/Eraser (1=Brush, 0=Eraser)
          [2] = Red
          [1] = Green
          [0] = Blue
        """
        status = 0
        status |= (1 if self.btn_up else 0) << 7
        status |= (1 if self.btn_down else 0) << 6
        status |= (1 if self.btn_left else 0) << 5
        status |= (1 if self.btn_right else 0) << 4
        status |= (1 if self.sw_brush else 0) << 3
        status |= (1 if self.sw_red else 0) << 2
        status |= (1 if self.sw_green else 0) << 1
        status |= (1 if self.sw_blue else 0) << 0
        return status
    
    def update_cursor(self, current_time):
        """Update cursor position based on button presses."""
        if current_time - self.last_move_time < self.move_delay:
            return
        
        moved = False
        if self.btn_up and self.cursor_y < self.grid_size - 1:
            self.cursor_y += 1  # UP increases Y (moves up on screen)
            moved = True
        elif self.btn_down and self.cursor_y > 0:
            self.cursor_y -= 1  # DOWN decreases Y (moves down on screen)
            moved = True
        elif self.btn_left and self.cursor_x > 0:
            self.cursor_x -= 1
            moved = True
        elif self.btn_right and self.cursor_x < self.grid_size - 1:
            self.cursor_x += 1
            moved = True
        
        if moved:
            self.last_move_time = current_time
    
    def auto_send_i2c_if_changed(self):
        """
        Automatically send I2C command when state changes.
        This simulates hardware continuously monitoring and transmitting state over I2C.
        In real hardware, whenever cursor position or color changes, it would automatically
        send the new state over I2C to update the display.
        """
        # Get current state (position + color/status)
        current_state = (self.cursor_x, self.cursor_y, self.get_status())
        
        # If state changed, send I2C command
        if current_state != self.i2c_last_state:
            self.i2c_last_state = current_state
            
            # Send 3-byte I2C command automatically
            x, y, status = current_state
            self.i2c_receive_byte(x)
            self.i2c_receive_byte(y)
            self.i2c_receive_byte(status)
    
    def get_canvas_y(self, user_y):
        """
        Convert user Y coordinate to canvas array index.
        User coordinate system: (0,0) at bottom-left
        Canvas array: canvas[y][x] where canvas[0] is displayed at bottom
        The draw_grid function handles the Y-flip for display, so we don't flip here.
        """
        return user_y
    
    def clear_canvas(self):
        """Clear the entire canvas."""
        self.canvas = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Reset external I2C tracking so new commands work after clear
        import os
        if os.path.exists(self.i2c_command_file):
            # Option 1: Remove the file completely
            os.remove(self.i2c_command_file)
            self.i2c_file_position = 0
        else:
            # Option 2: Just reset position
            self.i2c_file_position = 0
    
    def i2c_receive_byte(self, byte_val):
        """
        Simulate I2C byte reception.
        Accepts 3 bytes at a time:
        - Byte 1: X coordinate (0-255)
        - Byte 2: Y coordinate (0-255) - in user coordinates (0=bottom)
        - Byte 3: Status byte (RGB color in bits [2:0])
        """
        self.i2c_buffer.append(byte_val)
        
        # When we have 3 bytes, process the command
        if len(self.i2c_buffer) >= 3:
            self.i2c_x = self.i2c_buffer[0]
            self.i2c_y = self.i2c_buffer[1]
            self.i2c_status = self.i2c_buffer[2]
            
            # Extract color from status byte (bits [2:0] = RGB)
            color_mix = self.i2c_status & 0b111
            
            # Paint at the specified position (convert Y to canvas coordinates)
            if 0 <= self.i2c_x < self.grid_size and 0 <= self.i2c_y < self.grid_size:
                canvas_y = self.get_canvas_y(self.i2c_y)
                self.canvas[canvas_y][self.i2c_x] = color_mix
            
            # Clear buffer for next command
            self.i2c_buffer = []
    
    def read_external_i2c_commands(self):
        """
        Read I2C commands from external file.
        This allows other scripts (like testbenches) to send commands to the emulator.
        
        File format: Each line is "x,y,status"
        Example: "100,100,64" (x=100, y=100, status=0x40 for red)
        """
        import os
        import time
        
        # Check if command file exists
        if not os.path.exists(self.i2c_command_file):
            # Reset position if file doesn't exist
            if self.i2c_file_position != 0:
                self.i2c_file_position = 0
            return 0  # No commands processed
        
        commands_processed = 0
        
        try:
            # Check if file has been truncated/cleared (size is less than our position)
            file_size = os.path.getsize(self.i2c_command_file)
            if file_size < self.i2c_file_position:
                # File was cleared, reset position
                self.i2c_file_position = 0
            
            with open(self.i2c_command_file, 'r') as f:
                # Seek to last read position
                f.seek(self.i2c_file_position)
                
                # Read new lines
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        # Parse command: x,y,status
                        parts = line.split(',')
                        if len(parts) == 3:
                            x = int(parts[0])
                            y = int(parts[1])
                            status = int(parts[2])
                            
                            # Send the 3 bytes
                            self.i2c_receive_byte(x)
                            self.i2c_receive_byte(y)
                            self.i2c_receive_byte(status)
                            
                            # Track activity
                            commands_processed += 1
                            self.external_commands_received += 1
                            self.last_external_command_time = time.time()
                            
                    except ValueError:
                        pass  # Skip malformed lines
                
                # Update file position
                self.i2c_file_position = f.tell()
                
        except Exception:
            pass  # Silently handle file errors
        
        return commands_processed


class CanvasEmulator:
    """Pygame-based GUI for the Tiny Canvas emulator."""
    
    def __init__(self):
        pygame.init()
        
        # Get screen info
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        
        # Use 75% of screen size
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        
        # Create resizable windowed mode
        self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Tiny Canvas Emulator - 256×256")
        
        # Calculate optimal cell size and layout based on window size
        self.grid_size = 256
        
        # Reserve space for sidebar (30% of width or 400px max)
        self.sidebar_width = min(400, int(window_width * 0.3))
        
        # Use remaining space for canvas
        available_width = window_width - self.sidebar_width - 60  # 60px margins
        available_height = window_height - 100  # 100px for header and margins
        
        # Calculate cell size to fit the window
        max_cell_size_width = available_width // self.grid_size
        max_cell_size_height = available_height // self.grid_size
        self.cell_size = min(max_cell_size_width, max_cell_size_height)
        
        # Ensure minimum cell size
        self.cell_size = max(self.cell_size, 2)
        
        self.canvas_width = self.cell_size * self.grid_size
        self.canvas_height = self.cell_size * self.grid_size
        
        # Center the canvas in window
        self.canvas_offset_x = (window_width - self.sidebar_width - self.canvas_width) // 2
        self.canvas_offset_y = (window_height - self.canvas_height) // 2 + 30  # Offset for header
        
        # Colors for UI
        self.bg_color = (40, 40, 40)
        self.grid_color = (80, 80, 80)
        self.cursor_color = (255, 255, 0)
        self.text_color = (220, 220, 220)
        
        # Screen dimensions
        self.window_width = window_width
        self.window_height = window_height
        
        # Font
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        
        # Canvas logic
        self.canvas = TinyCanvas()
        
        # Clock
        self.clock = pygame.time.Clock()
        self.fps = 60
    
    def recalculate_layout(self, window_width, window_height):
        """Recalculate layout when window is resized."""
        self.window_width = window_width
        self.window_height = window_height
        
        # Recalculate sidebar width
        self.sidebar_width = min(400, int(window_width * 0.3))
        
        # Recalculate available space
        available_width = window_width - self.sidebar_width - 60
        available_height = window_height - 100
        
        # Recalculate cell size
        max_cell_size_width = available_width // self.grid_size
        max_cell_size_height = available_height // self.grid_size
        self.cell_size = min(max_cell_size_width, max_cell_size_height)
        self.cell_size = max(self.cell_size, 1)  # Minimum 1 pixel per cell
        
        # Recalculate canvas dimensions
        self.canvas_width = self.cell_size * self.grid_size
        self.canvas_height = self.cell_size * self.grid_size
        
        # Recalculate canvas position (centered)
        self.canvas_offset_x = (window_width - self.sidebar_width - self.canvas_width) // 2
        self.canvas_offset_y = (window_height - self.canvas_height) // 2 + 30
        
    def handle_events(self):
        """Handle keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:
                # Handle window resize
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.recalculate_layout(event.w, event.h)
            
            if event.type == pygame.KEYDOWN:
                # Check if in keyboard input mode
                if self.canvas.keyboard_input_mode:
                    if event.key == pygame.K_RETURN:
                        # Process the command
                        self.process_keyboard_command()
                    elif event.key == pygame.K_ESCAPE:
                        # Exit input mode
                        self.canvas.keyboard_input_mode = False
                        self.canvas.keyboard_input_buffer = ""
                        self.canvas.keyboard_command_status = ""
                    elif event.key == pygame.K_BACKSPACE:
                        # Delete last character
                        self.canvas.keyboard_input_buffer = self.canvas.keyboard_input_buffer[:-1]
                    else:
                        # Add character to buffer
                        if event.unicode and (event.unicode.isprintable() or event.unicode == ' '):
                            self.canvas.keyboard_input_buffer += event.unicode
                else:
                    # Normal mode - handle regular controls
                    if event.key == pygame.K_i:
                        # Enter keyboard input mode
                        self.canvas.keyboard_input_mode = True
                        self.canvas.keyboard_input_buffer = ""
                        self.canvas.keyboard_command_status = "Type: 8-bit STATUS byte (e.g. 0x8C or 140)"
                    elif event.key == pygame.K_r:
                        self.canvas.sw_red = not self.canvas.sw_red
                    elif event.key == pygame.K_g:
                        self.canvas.sw_green = not self.canvas.sw_green
                    elif event.key == pygame.K_b:
                        self.canvas.sw_blue = not self.canvas.sw_blue
                    elif event.key == pygame.K_SPACE:
                        self.canvas.sw_brush = not self.canvas.sw_brush
                    elif event.key == pygame.K_c:
                        self.canvas.clear_canvas()
                        print("Canvas cleared! External I2C reset - ready for new commands.")
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return False
        
        # Handle arrow keys (held down) - only in normal mode
        if not self.canvas.keyboard_input_mode:
            keys = pygame.key.get_pressed()
            self.canvas.btn_up = keys[pygame.K_UP]
            self.canvas.btn_down = keys[pygame.K_DOWN]
            self.canvas.btn_left = keys[pygame.K_LEFT]
            self.canvas.btn_right = keys[pygame.K_RIGHT]
        else:
            # Disable buttons in input mode
            self.canvas.btn_up = False
            self.canvas.btn_down = False
            self.canvas.btn_left = False
            self.canvas.btn_right = False
        
        return True
    
    def process_keyboard_command(self):
        """Parse and execute a keyboard command: single 8-bit status byte"""
        try:
            # Parse the input (single byte)
            input_str = self.canvas.keyboard_input_buffer.strip()
            
            # Handle hex (0x0C) or decimal (12)
            if input_str.startswith('0x') or input_str.startswith('0X'):
                status = int(input_str, 16)
            else:
                status = int(input_str)
            
            # Validate range
            if not (0 <= status <= 255):
                self.canvas.keyboard_command_status = "❌ Error: Value must be 0-255 (0x00-0xFF)"
                return
            
            # Decode the status byte
            btn_up = (status >> 7) & 1
            btn_down = (status >> 6) & 1
            btn_left = (status >> 5) & 1
            btn_right = (status >> 4) & 1
            brush = (status >> 3) & 1
            color = status & 0b111
            
            # Update canvas state
            self.canvas.btn_up = bool(btn_up)
            self.canvas.btn_down = bool(btn_down)
            self.canvas.btn_left = bool(btn_left)
            self.canvas.btn_right = bool(btn_right)
            self.canvas.sw_brush = bool(brush)
            self.canvas.sw_red = bool((color >> 2) & 1)
            self.canvas.sw_green = bool((color >> 1) & 1)
            self.canvas.sw_blue = bool(color & 1)
            
            # Move cursor based on button states
            import pygame
            current_time = pygame.time.get_ticks()
            if btn_up and self.canvas.cursor_y < self.canvas.grid_size - 1:
                self.canvas.cursor_y += 1
            elif btn_down and self.canvas.cursor_y > 0:
                self.canvas.cursor_y -= 1
            elif btn_left and self.canvas.cursor_x > 0:
                self.canvas.cursor_x -= 1
            elif btn_right and self.canvas.cursor_x < self.canvas.grid_size - 1:
                self.canvas.cursor_x += 1
            
            # Paint at current position
            canvas_y = self.canvas.get_canvas_y(self.canvas.cursor_y)
            self.canvas.canvas[canvas_y][self.canvas.cursor_x] = self.canvas.get_color_mix()
            
            # Build status message
            color_names = {
                0b000: "Black", 0b100: "Red", 0b010: "Green", 0b001: "Blue",
                0b110: "Yellow", 0b101: "Magenta", 0b011: "Cyan", 0b111: "White",
            }
            color_name = color_names.get(color, "Unknown")
            
            buttons = []
            if btn_up: buttons.append("Up")
            if btn_down: buttons.append("Down")
            if btn_left: buttons.append("Left")
            if btn_right: buttons.append("Right")
            btn_str = "+".join(buttons) if buttons else "None"
            
            mode = "Brush" if brush else "Eraser"
            
            self.canvas.keyboard_command_status = f"✅ 0x{status:02X}: {btn_str} | {mode} | {color_name} @ ({self.canvas.cursor_x},{self.canvas.cursor_y})"
            
            # Store last command
            self.canvas.last_keyboard_command = self.canvas.keyboard_input_buffer
            
            # Clear buffer for next command
            self.canvas.keyboard_input_buffer = ""
            
            print(f"Keyboard input: 0x{status:02X} [{btn_str}] [{mode}] [{color_name}] @ ({self.canvas.cursor_x},{self.canvas.cursor_y})")
            
        except ValueError as e:
            self.canvas.keyboard_command_status = f"❌ Error: Invalid number format"
        except Exception as e:
            self.canvas.keyboard_command_status = f"❌ Error: {str(e)}"
    
    def draw_header(self):
        """Draw header with title and info."""
        # Main title
        title = self.font_large.render("TINY CANVAS - 256×256 Pixel Emulator", True, (100, 200, 255))
        title_rect = title.get_rect(center=(self.window_width // 2, 20))
        self.screen.blit(title, title_rect)
        
        # Controls hint
        if not self.canvas.keyboard_input_mode:
            hint = self.font_small.render("Arrow Keys: Move | R/G/B: Colors | I: Input Mode | Space: Brush/Eraser | C: Clear | ESC: Quit", True, (150, 150, 150))
        else:
            hint = self.font_small.render("KEYBOARD INPUT MODE - Type: 8-bit STATUS (0x00-0xFF) | Enter: Apply | ESC: Cancel", True, (255, 200, 100))
        hint_rect = hint.get_rect(center=(self.window_width // 2, 45))
        self.screen.blit(hint, hint_rect)
    
    def draw_grid(self):
        """Draw the 256x256 canvas grid."""
        # Draw cells (no grid lines for 256x256 as it would be too dense)
        # Note: Canvas array is [y][x] with [0][0] at top-left
        # We display it so visual (0,0) is at bottom-left
        for canvas_y in range(self.grid_size):
            for x in range(self.grid_size):
                # Calculate screen Y position (flip for display)
                # canvas_y=0 should appear at bottom of screen
                screen_y = self.grid_size - 1 - canvas_y
                
                rect = pygame.Rect(
                    self.canvas_offset_x + x * self.cell_size,
                    self.canvas_offset_y + screen_y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                # Fill with cell color
                color_value = self.canvas.canvas[canvas_y][x]
                color = COLORS[color_value]
                pygame.draw.rect(self.screen, color, rect)
        
        # Draw border around canvas
        border_rect = pygame.Rect(
            self.canvas_offset_x - 2,
            self.canvas_offset_y - 2,
            self.canvas_width + 4,
            self.canvas_height + 4
        )
        pygame.draw.rect(self.screen, (100, 100, 100), border_rect, 2)
        
        # Draw cursor (centered on the pixel being painted)
        # Cursor position is in user coordinates (0,0 = bottom-left)
        cursor_size = max(self.cell_size * 4, 8)  # At least 8 pixels
        
        # Convert cursor Y to screen Y (flip it)
        cursor_screen_y = self.grid_size - 1 - self.canvas.cursor_y
        
        # Calculate center of the current pixel
        pixel_center_x = self.canvas_offset_x + self.canvas.cursor_x * self.cell_size + self.cell_size // 2
        pixel_center_y = self.canvas_offset_y + cursor_screen_y * self.cell_size + self.cell_size // 2
        
        # Draw cursor centered on that pixel
        cursor_rect = pygame.Rect(
            pixel_center_x - cursor_size // 2,
            pixel_center_y - cursor_size // 2,
            cursor_size,
            cursor_size
        )
        pygame.draw.rect(self.screen, self.cursor_color, cursor_rect, 2)
    
    def draw_sidebar(self):
        """Draw the control panel sidebar."""
        # Position sidebar on the right side of the screen
        sidebar_x = self.window_width - self.sidebar_width + 20
        y_offset = 50
        
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
        y_offset += 30
        
        # I2C Mode explanation
        modes_header = self.font_small.render("I2C: Automatic", True, (100, 255, 100))
        self.screen.blit(modes_header, (sidebar_x, y_offset))
        y_offset += 22
        
        mode1_text = self.font_small.render("State change -> I2C send", True, (180, 180, 180))
        self.screen.blit(mode1_text, (sidebar_x, y_offset))
        y_offset += 20
        
        mode2_text = self.font_small.render("I2C receive -> Paint pixel", True, (180, 180, 180))
        self.screen.blit(mode2_text, (sidebar_x, y_offset))
        y_offset += 20
        
        # External I2C indicator with activity status
        import os
        import time
        current_time = time.time()
        time_since_last = current_time - self.canvas.last_external_command_time
        
        if os.path.exists(self.canvas.i2c_command_file) and time_since_last < 1.0:
            # Recently received external command (within 1 second)
            ext_text = self.font_small.render("External I2C: ACTIVE", True, (100, 255, 100))
            ext_indicator = "●"  # Active indicator
        elif os.path.exists(self.canvas.i2c_command_file):
            ext_text = self.font_small.render("External I2C: Listening", True, (255, 255, 100))
            ext_indicator = "○"  # Waiting indicator
        else:
            ext_text = self.font_small.render("External I2C: Ready", True, (150, 150, 150))
            ext_indicator = "○"
        
        indicator_text = self.font_medium.render(ext_indicator, True, (100, 255, 100) if time_since_last < 1.0 else (150, 150, 150))
        self.screen.blit(indicator_text, (sidebar_x - 20, y_offset - 2))
        self.screen.blit(ext_text, (sidebar_x, y_offset))
        y_offset += 20
        
        # Show command count
        if self.canvas.external_commands_received > 0:
            count_text = self.font_small.render(f"  Commands: {self.canvas.external_commands_received}", True, (180, 180, 180))
            self.screen.blit(count_text, (sidebar_x, y_offset))
            y_offset += 25
        else:
            y_offset += 10
        
        # I2C Status
        i2c_header = self.font_small.render("I2C Communication:", True, (100, 200, 255))
        self.screen.blit(i2c_header, (sidebar_x, y_offset))
        y_offset += 22
        
        # I2C buffer
        buffer_status = f"Buffer: {len(self.canvas.i2c_buffer)}/3 bytes"
        buffer_text = self.font_small.render(buffer_status, True, self.text_color)
        self.screen.blit(buffer_text, (sidebar_x, y_offset))
        y_offset += 20
        
        if len(self.canvas.i2c_buffer) > 0:
            buffer_vals = ", ".join([f"0x{b:02X}" for b in self.canvas.i2c_buffer])
            # Split into multiple lines if needed
            buffer_vals_text = self.font_small.render(f"[{buffer_vals}]", True, (180, 180, 180))
            self.screen.blit(buffer_vals_text, (sidebar_x + 10, y_offset))
            y_offset += 20
        
        # Last I2C command - show hex bytes
        if self.canvas.i2c_status != 0:
            last_cmd = f"Last I2C Transmission:"
            last_cmd_text = self.font_small.render(last_cmd, True, self.text_color)
            self.screen.blit(last_cmd_text, (sidebar_x, y_offset))
            y_offset += 20
            
            # Show the actual hex bytes sent
            byte1_text = f"Byte 1 (X):  0x{self.canvas.i2c_x:02X} = {self.canvas.i2c_x}"
            byte1_render = self.font_small.render(byte1_text, True, (255, 200, 100))
            self.screen.blit(byte1_render, (sidebar_x, y_offset))
            y_offset += 20
            
            byte2_text = f"Byte 2 (Y):  0x{self.canvas.i2c_y:02X} = {self.canvas.i2c_y}"
            byte2_render = self.font_small.render(byte2_text, True, (255, 200, 100))
            self.screen.blit(byte2_render, (sidebar_x, y_offset))
            y_offset += 20
            
            byte3_text = f"Byte 3 (St): 0x{self.canvas.i2c_status:02X}"
            byte3_render = self.font_small.render(byte3_text, True, (255, 200, 100))
            self.screen.blit(byte3_render, (sidebar_x, y_offset))
            y_offset += 20
            
            # Show decoded status byte fields
            status_decode = self.font_small.render(f"  [7:4]={self.canvas.i2c_status >> 4:04b} [3]={(self.canvas.i2c_status >> 3) & 1}", True, (180, 180, 180))
            self.screen.blit(status_decode, (sidebar_x, y_offset))
            y_offset += 18
            
            # Show decoded color from status byte (bits [2:0])
            last_color = self.canvas.i2c_status & 0b111
            color_names = {
                0b000: "Black", 0b100: "Red", 0b010: "Green", 0b001: "Blue",
                0b110: "Yellow", 0b101: "Magenta", 0b011: "Cyan", 0b111: "White",
            }
            color_name = color_names.get(last_color, "Unknown")
            color_info_text = self.font_small.render(f"  RGB[2:0]: {color_name} (0b{last_color:03b})", True, (180, 180, 180))
            self.screen.blit(color_info_text, (sidebar_x, y_offset))
            y_offset += 25
        
        # Controls help
        y_offset += 5
        help_lines = [
            ("Controls:", self.text_color),
            ("Arrows: Move cursor", (180, 180, 180)),
            ("R/G/B: Toggle color", (180, 180, 180)),
            ("I: Input mode", (180, 180, 180)),
            ("Space: Brush/Eraser", (180, 180, 180)),
            ("C: Clear canvas", (180, 180, 180)),
            ("ESC/Q: Quit", (180, 180, 180)),
        ]
        for line, color in help_lines:
            help_text = self.font_small.render(line, True, color)
            self.screen.blit(help_text, (sidebar_x, y_offset))
            y_offset += 20
    
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
    
    def draw_keyboard_input(self):
        """Draw the keyboard input box when in input mode."""
        if not self.canvas.keyboard_input_mode and not self.canvas.keyboard_command_status:
            return
        
        # Draw input box at bottom of screen
        box_height = 100
        box_y = self.window_height - box_height - 10
        box_rect = pygame.Rect(10, box_y, self.window_width - 20, box_height)
        
        # Background
        pygame.draw.rect(self.screen, (40, 40, 60), box_rect)
        pygame.draw.rect(self.screen, (100, 200, 255) if self.canvas.keyboard_input_mode else (100, 100, 100), box_rect, 3)
        
        y_offset = box_y + 10
        
        if self.canvas.keyboard_input_mode:
            # Title
            title = self.font_medium.render("Keyboard Input Mode", True, (100, 200, 255))
            self.screen.blit(title, (20, y_offset))
            y_offset += 30
            
            # Input prompt
            prompt = self.font_small.render("Enter command:", True, self.text_color)
            self.screen.blit(prompt, (20, y_offset))
            y_offset += 22
            
            # Input buffer with cursor
            input_text = self.canvas.keyboard_input_buffer + "█"
            input_render = self.font_medium.render(input_text, True, (255, 255, 0))
            self.screen.blit(input_render, (20, y_offset))
        
        # Status message (shown in both modes if present)
        if self.canvas.keyboard_command_status:
            status_y = box_y + box_height - 30
            status_color = (100, 255, 100) if "✅" in self.canvas.keyboard_command_status else (255, 100, 100)
            status_render = self.font_small.render(self.canvas.keyboard_command_status, True, status_color)
            self.screen.blit(status_render, (20, status_y))
    
    def run(self):
        """Main emulator loop."""
        running = True
        
        print("=" * 60)
        print("Tiny Canvas Emulator Started")
        print("=" * 60)
        print("Canvas: 256x256 pixels")
        print(f"Window: {self.window_width}x{self.window_height} @ {self.cell_size}px per cell")
        print("Window: RESIZABLE - drag corners to resize")
        print("Coordinate System: (0,0) = BOTTOM-LEFT, (255,255) = TOP-RIGHT")
        print("Starting Position: (0, 0) - bottom-left corner")
        print("=" * 60)
        print("\nI2C COMMUNICATION (AUTOMATIC):")
        print()
        print("The emulator simulates real hardware I2C behavior:")
        print("  • I2C automatically sends 3 bytes when state changes")
        print("  • Byte 1: X coordinate (0-255)")
        print("  • Byte 2: Y coordinate (0-255)")
        print("  • Byte 3: Status byte [7:0]")
        print("    [7:4] = Buttons (Up/Down/Left/Right)")
        print("    [3]   = Brush/Eraser (1=Brush, 0=Eraser)")
        print("    [2:0] = RGB Color (Red/Green/Blue)")
        print()
        print("When you move the cursor or change colors:")
        print("  1. Hardware detects state change")
        print("  2. Automatically sends I2C bytes")
        print("  3. Canvas receives and processes bytes")
        print("  4. Pixel is painted!")
        print()
        print("Watch the I2C buffer fill in the sidebar!")
        print("=" * 60)
        print("\nEXTERNAL I2C CONTROL:")
        print()
        print("You can also send I2C bytes from external scripts:")
        print("  python test/send_i2c.py <x> <y> <status>")
        print()
        print("Example: python test/send_i2c.py 100 100 0x40")
        print("         (Paints red pixel at position 100, 100)")
        print("=" * 60)
        print("Controls:")
        print("  Arrow Keys: Move cursor (triggers I2C automatically)")
        print("  R/G/B: Toggle Red/Green/Blue (triggers I2C)")
        print("  I: Keyboard Input Mode (type 8-bit status byte)")
        print("  Space: Toggle Brush/Eraser")
        print("  C: Clear canvas")
        print("  ESC/Q: Quit")
        print("=" * 60)
        print("\nKEYBOARD INPUT MODE:")
        print("  Press 'I' to enter input mode")
        print("  Type: 8-bit STATUS byte (0x00-0xFF or 0-255)")
        print("  Press Enter to apply, ESC to cancel")
        print()
        print("  Status Byte Format:")
        print("    Bit [7]:   Up button")
        print("    Bit [6]:   Down button")
        print("    Bit [5]:   Left button")
        print("    Bit [4]:   Right button")
        print("    Bit [3]:   Brush/Eraser (1=Brush)")
        print("    Bits [2:0]: RGB Color")
        print()
        print("  Examples:")
        print("    0x8C (10001100) = Up + Brush + Red")
        print("    0x4A (01001010) = Down + Brush + Green")
        print("    0x0F (00001111) = Brush + White (no movement)")
        print("=" * 60)
        
        while running:
            # Handle input
            running = self.handle_events()
            
            # Update canvas logic
            current_time = pygame.time.get_ticks()
            self.canvas.update_cursor(current_time)
            
            # Automatically send I2C when state changes (simulates hardware behavior)
            self.canvas.auto_send_i2c_if_changed()
            
            # Read external I2C commands from file
            self.canvas.read_external_i2c_commands()
            
            # Draw everything
            self.screen.fill(self.bg_color)
            self.draw_header()
            self.draw_grid()
            self.draw_sidebar()
            self.draw_keyboard_input()
            
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

