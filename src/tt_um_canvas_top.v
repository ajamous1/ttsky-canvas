`default_nettype none

module tt_um_canvas_top (
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
    wire sda = uio_in[2];
    wire scl = uio_in[3];

    // Input signals (buttons and toggles)
    // Pushbuttons (momentary, active-low)
    wire btn_up    = ~io_in[3];
    wire btn_down  = ~io_in[2];
    wire btn_left  = ~io_in[1];
    wire btn_right = ~io_in[0];
    
    // Switches (persistent mode selectors)
    wire sw_red    = io_in[6];
    wire sw_green  = io_in[5];
    wire sw_blue   = io_in[4];
    wire sw_brush  = io_in[7];

    // Instantiate your main logic
    project u_project (
        .buttons(buttons),
        .sda(sda),
        .scl(scl),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule
