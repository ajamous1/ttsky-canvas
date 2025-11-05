# SPDX-License-Identifier: Apache-2.0
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


def make_ui_in(brush, r, g, b):
    """
    Build ui_in[7:0] with only brush + RGB switches (no buttons pressed).
    """
    ui = 0
    if brush:
        ui |= (1 << 7)  # brush
    ui |= (1 if r else 0) << 2
    ui |= (1 if g else 0) << 1
    ui |= (1 if b else 0) << 0
    # all buttons released (active-low, so set bits [6:3] = 1)
    ui |= 0b01111000
    return ui


def expected_color_mix(r, g, b):
    """Compute expected 3-bit color mix value."""
    return ((1 if r else 0) << 2) | ((1 if g else 0) << 1) | (1 if b else 0)


@cocotb.test()
async def test_rgb_combinations(dut):
    """Test that all RGB combinations output correct color mix."""
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Initialize + reset
    dut.ena.value = 1
    dut.uio_in.value = 0
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # RGB combinations to test: (R,G,B)
    combos = [
        (1, 0, 0),  # Red
        (0, 1, 0),  # Green
        (0, 0, 1),  # Blue
        (1, 1, 0),  # Yellow
        (1, 0, 1),  # Magenta
        (0, 1, 1),  # Cyan
        (1, 1, 1),  # White
    ]

    for (r, g, b) in combos:
        ui_val = make_ui_in(brush=True, r=r, g=g, b=b)
        dut.ui_in.value = ui_val
        await ClockCycles(dut.clk, 1)

        color_mix = expected_color_mix(r, g, b)
        # buttons all released => buttons = 0b0000
        expected_status = (color_mix << 4)
        actual = int(dut.uo_out.value)

        dut._log.info(
            f"Brush=1 RGB={r}{g}{b} → Expected status {expected_status:02X}, got {actual:02X}"
        )
        assert actual == expected_status, (
            f"RGB={r}{g}{b}: expected 0x{expected_status:02X}, got 0x{actual:02X}"
        )

    
