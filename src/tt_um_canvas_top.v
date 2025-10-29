// SPDX-License-Identifier: Apache-2.0
`default_nettype none

module tt_um_canvas_top (
    // TT user IOs
    input  wire [7:0] io_in,     // in[7:0]  from MCU
    output wire [7:0] io_out,    // out[7:0] to baseboard (unused -> 0)

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

    //   io_in[6:3] = pushbuttons (active-low, momentary)
    //   io_in[2:0] = RGB switches (level)
    //   io_in[7]   = Brush/Eraser switch (level)
    // Buttons (invert because active-low)
    wire btn_up    = ~io_in[6];
    wire btn_down  = ~io_in[5];
    wire btn_right = ~io_in[4];
    wire btn_left  = ~io_in[3];

    // switches
    wire sw_red    = io_in[2];
    wire sw_green  = io_in[1];
    wire sw_blue   = io_in[0];
    wire sw_brush  = io_in[7];

    //aliasing 
    //buttons[3] = btn_up, buttons[2] = btn_down, ...
    wire [3:0] buttons = {btn_up, btn_down, btn_right, btn_left};
    wire [2:0] rgb_sel = {sw_red, sw_green, sw_blue};

    // -----------------------------
    // Tie off unused TT outputs/bidirs
    // -----------------------------
    wire [7:0] status_w;
    assign io_out  = status_w;   // or expose debug/status if desired
    assign uio_out = 8'b0;   // we never drive the bidir bus
    assign uio_oe  = 8'b0;   // keep as inputs (open-drain bus handled externally)

     tt_um_canvas u_project (
        .clk     (clk),
        .rst_n   (rst_n),
        // controls
        .buttons (buttons),   // [3]=up, [2]=down, [1]=right, [0]=left 
        .rgb_sel (rgb_sel),   // {R,G,B}
        .brush   (sw_brush),
        // I2C slave pins
        .scl     (scl),
        .sda     (sda),
        //outputs
        .status  (status_w)
    );

endmodule
