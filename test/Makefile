TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../src/project.v $(PWD)/dump_vcd.v
TOPLEVEL = tt_um_canvas
MODULE = test
SIM = icarus

# Tell iverilog to instantiate our VCD dump module as a top-level
COMPILE_ARGS += -s vcd_dump

# Disable cocotb's wave dumping (we have our own)
WAVES = 0

include $(shell cocotb-config --makefiles)/Makefile.sim