// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// ---------------------------------------------------------------------
// Core canvas module: takes decoded controls + I2C + clock/reset
// and outputs an 8-bit status bus.
// ---------------------------------------------------------------------
module canvas_core (
    input  wire        clk,
    input  wire        rst_n,

    // Control signals from top
    input  wire [3:0]  buttons,   // {Up, Down, Right, Left}
    input  wire [2:0]  rgb_sel,   // {R, G, B}
    input  wire        brush,     // 1 = brush, 0 = eraser

    // I2C inputs
    input  wire        scl,
    input  wire        sda,

    // Outputs
    output wire [7:0]  status
);

    // Color mixing logic when brush is active
    reg [2:0] color_mix;

    always @(*) begin
        if (brush) begin
            case (rgb_sel)
                3'b000: color_mix = 3'b000; // None
                3'b100: color_mix = 3'b100; // Red
                3'b010: color_mix = 3'b010; // Green
                3'b001: color_mix = 3'b001; // Blue
                3'b110: color_mix = 3'b110; // Yellow (R+G)
                3'b101: color_mix = 3'b101; // Magenta (R+B)
                3'b011: color_mix = 3'b011; // Cyan (G+B)
                3'b111: color_mix = 3'b111; // White (R+G+B)
                default: color_mix = 3'b000;
            endcase
        end else begin
            // Eraser mode = no color
            color_mix = 3'b000;
        end
    end

    // Directional + color status output
    assign status = { color_mix, buttons }; 

endmodule


// ---------------------------------------------------------------------
// TinyTapeout wrapper: this is the REQUIRED top-level for tt + tb.v
// ---------------------------------------------------------------------
module tt_um_canvas (
    // Optional power pins for gate-level sims
`ifdef GL_TEST
    input  wire       VPWR,
    input  wire       VGND,
`endif

    // TT user IOs
    input  wire [7:0] ui_in,     // in[7:0]  from MCU
    output wire [7:0] uo_out,    // out[7:0] to baseboard

    // TT user bidir IOs (we use as inputs only for I2C slave)
    input  wire [7:0] uio_in,    // uio[7:0] inputs
    output wire [7:0] uio_out,   // uio[7:0] outputs (unused -> 0)
    output wire [7:0] uio_oe,    // uio[7:0] output enables (1=drive)

    // housekeeping
    input  wire       ena,       // high when your design is active
    input  wire       clk,       // shared clock
    input  wire       rst_n      // async, active-low reset from harness
);

    // I2C (slave) on BIDIR pins
    // uio_in[3] = SCL, uio_in[2] = SDA   (inputs only)
    wire scl = uio_in[3];
    wire sda = uio_in[2];

    // ui_in mapping:
    //   ui_in[6:3] = pushbuttons (active-low, momentary)
    //   ui_in[2:0] = RGB switches (level)
    //   ui_in[7]   = Brush/Eraser switch (level)

    // Buttons (invert because active-low)
    wire btn_up    = ~ui_in[6];
    wire btn_down  = ~ui_in[5];
    wire btn_right = ~ui_in[4];
    wire btn_left  = ~ui_in[3];

    // Switches
    wire sw_red    = ui_in[2];
    wire sw_green  = ui_in[1];
    wire sw_blue   = ui_in[0];
    wire sw_brush  = ui_in[7];

    // Aliasing:
    // buttons[3] = up, [2] = down, [1] = right, [0] = left
    wire [3:0] buttons = {btn_up, btn_down, btn_right, btn_left};
    wire [2:0] rgb_sel = {sw_red, sw_green, sw_blue};

    wire [7:0] status_w;

    // For good TinyTapeout hygiene, gate outputs with ena
    assign uo_out  = ena ? status_w : 8'h00;
    assign uio_out = 8'b0;       // we never drive the bidir bus
    assign uio_oe  = 8'b0;       // keep as inputs (open-drain bus handled externally)

    // Core canvas instance
    canvas_core u_core (
        .clk     (clk),
        .rst_n   (rst_n),

        // controls
        .buttons (buttons),   // [3]=up, [2]=down, [1]=right, [0]=left 
        .rgb_sel (rgb_sel),   // {R,G,B}
        .brush   (sw_brush),

        // I2C slave pins
        .scl     (scl),
        .sda     (sda),

        // outputs
        .status  (status_w)
    );

endmodule
