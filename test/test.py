"""
cocotb testbench for tt_um_day4_forklift.

Drives the AXI-Stream-like protocol, compares (part1, part2) returned by the DUT
against the Python golden model.
"""

import os
import sys
from collections import Counter

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Make golden model importable
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from day4_golden_model import REGRESSION_CASES, random_grid, run_case  # noqa: E402


CLOCK_PERIOD_NS = 20  # 50 MHz


async def reset(dut):
    dut.rst_n.value = 0
    dut.ena.value   = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0     # s_tvalid=0, m_tready=0
    for _ in range(5):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


def set_master_in(dut, s_tvalid: int, m_tready: int, tdata: int = 0):
    """uio_in[0]=s_tvalid, uio_in[1]=m_tready."""
    dut.uio_in.value = (m_tready << 1) | (s_tvalid & 1)
    dut.ui_in.value  = tdata & 0xFF


async def send_grid(dut, grid_bytes):
    """Send 8 bytes via AXI-Stream handshake."""
    for byte in grid_bytes:
        # Drive valid + data, wait for ready
        set_master_in(dut, s_tvalid=1, m_tready=0, tdata=byte)
        # wait until DUT asserts s_tready (uio_out[2]) on a rising edge
        while True:
            await RisingEdge(dut.clk)
            tready = (int(dut.uio_out.value) >> 2) & 1
            if tready:
                break
        # one cycle handshake done; deassert valid briefly
        set_master_in(dut, s_tvalid=0, m_tready=0, tdata=0)
        await RisingEdge(dut.clk)


async def recv_byte(dut, timeout=2000) -> int:
    """Wait for m_tvalid, capture tdata, pulse m_tready."""
    # Assert tready
    set_master_in(dut, s_tvalid=0, m_tready=1)
    for _ in range(timeout):
        await RisingEdge(dut.clk)
        mvalid = (int(dut.uio_out.value) >> 3) & 1
        if mvalid:
            data = int(dut.uo_out.value) & 0xFF
            # one-cycle handshake
            set_master_in(dut, s_tvalid=0, m_tready=0)
            await RisingEdge(dut.clk)
            return data
    raise TimeoutError("m_tvalid never asserted")


@cocotb.test()
async def test_regression(dut):
    """Run every regression case from the golden model."""
    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_NS, units="ns").start())
    await reset(dut)

    fails = 0
    for name, gbytes, _expect in REGRESSION_CASES:
        gold = run_case(gbytes)
        dut._log.info(f"=== Case {name}: golden p1={gold['part1']} p2={gold['part2']} iter={gold['iterations']}")

        await send_grid(dut, gbytes)
        b0 = await recv_byte(dut)
        b1 = await recv_byte(dut)

        ok_p1 = (b0 == gold["part1"])
        ok_p2 = (b1 == gold["part2"])
        status = "PASS" if (ok_p1 and ok_p2) else "FAIL"
        dut._log.info(f"    DUT p1={b0} p2={b1}  [{status}]")
        if not (ok_p1 and ok_p2):
            fails += 1
            dut._log.error(f"    MISMATCH on {name}: dut=({b0},{b1}) gold=({gold['part1']},{gold['part2']})")

        # Idle a few cycles between cases
        set_master_in(dut, s_tvalid=0, m_tready=0)
        for _ in range(4):
            await RisingEdge(dut.clk)

    assert fails == 0, f"{fails} regression case(s) failed"


@cocotb.test()
async def test_random_vectors(dut):
    """1024 random 8x8 grids vs golden model."""
    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_NS, units="ns").start())
    await reset(dut)

    n_vectors = int(os.environ.get("RANDOM_N", "1024"))
    base_seed = int(os.environ.get("COCOTB_RANDOM_SEED", "0xC0DECAFE"), 0) \
                if isinstance(os.environ.get("COCOTB_RANDOM_SEED", "0xC0DECAFE"), str) \
                else 0xC0DECAFE
    fails = 0
    iter_hist = Counter()

    for i in range(n_vectors):
        gbytes = random_grid(base_seed + i)
        gold = run_case(gbytes)

        await send_grid(dut, gbytes)
        b0 = await recv_byte(dut)
        b1 = await recv_byte(dut)

        ok = (b0 == gold["part1"]) and (b1 == gold["part2"])
        iter_hist[gold["iterations"]] += 1
        if not ok:
            fails += 1
            dut._log.error(
                f"  random[{i}] seed={base_seed+i} bytes={gbytes} "
                f"dut=({b0},{b1}) gold=({gold['part1']},{gold['part2']})"
            )
            if fails >= 5:
                break

        # idle between vectors
        set_master_in(dut, 0, 0)
        for _ in range(2):
            await RisingEdge(dut.clk)

    dut._log.info(f"random regression: {n_vectors - fails}/{n_vectors} PASS")
    dut._log.info(f"iteration histogram (iterations -> count):")
    for it in sorted(iter_hist):
        dut._log.info(f"    iter={it:>2}: {iter_hist[it]:>5}  ({100*iter_hist[it]/n_vectors:5.1f}%)")
    assert fails == 0, f"{fails} random vector(s) failed"
