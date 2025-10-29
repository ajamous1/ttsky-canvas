`default_nettype none

module tt_um_ahmadjamous_canvas_top (
    input  wire [7:0] io_in,     // from Pico (pushbuttons, RGB toggles)
    output wire [7:0] io_out,    // (unused or status/debug)
    input  wire [7:0] uio_in,    // bidirectional bus in (I2C)
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,    // output enable (active-high)
    input  wire       ena,       // always 1 when your design is active
    input  wire       clk,       // shared clock
    input  wire       rst_n      // active-low reset
);

    // I2C signals
    wire sda = uio_in[0];
    wire scl = uio_in[1];

    // Input signals (buttons and toggles)
    wire [7:0] buttons = io_in;

    // Unused outputs for now
    assign io_out = 8'b0;
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Instantiate your main logic
    project u_project (
        .buttons(buttons),
        .sda(sda),
        .scl(scl),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule
