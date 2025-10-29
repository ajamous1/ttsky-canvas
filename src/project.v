/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_canvas (
    input  wire        clk,
    input  wire        rst_n,

    // Packed controls from the top wrapper
    input  wire [3:0]  buttons,   // [3]=up, [2]=down, [1]=right, [0]=left  (active-high *after* inversion in top)
    input  wire [2:0]  rgb_sel,   // {R,G,B}  level
    input  wire        brush,     // 1=brush, 0=eraser  (level)

    // I2C pins (currently *inputs only* in your top)
    input  wire        scl,
    input  wire        sda,

    // Optional: status you can drive to io_out[7:0] from the top if desired
    output wire [7:0]  status
);

    //not done, will implement logic later
  // All output pins must be assigned. If not used, assign to 0.
  assign uo_out  = ui_in + uio_in;  // Example: ou_out is the sum of ui_in and uio_in
  assign uio_out = 0;
  assign uio_oe  = 0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, clk, rst_n, 1'b0};

endmodule
