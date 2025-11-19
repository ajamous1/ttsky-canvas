module vcd_dump();
initial begin
    $dumpfile("tt_um_canvas.vcd");
    $dumpvars(0, tt_um_canvas);
end
endmodule

