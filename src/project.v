`default_nettype none

module tt_um_canvas (
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


    //color mixing logic when brush is active


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

  
    //directional + color status output
    

    assign status = { color_mix, buttons }; 
    // You could drive io_out[7:0] = status in your top file

endmodule
