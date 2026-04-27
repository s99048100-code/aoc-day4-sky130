"""
AoC 2025 Day 4 - Printing Department
Golden model for the tt_um_day4_forklift hardware.

Rules:
  - Cell '@' = scroll (1), '.' = empty (0)
  - A scroll is "accessible" iff fewer than 4 of its 8 Moore neighbors are scrolls
  - Part 1: count accessible scrolls in initial grid
  - Part 2: iteratively remove all accessible scrolls until stable, return total removed

Hardware AXI-Stream-like interface (8x8 sub-grid):
  Input : 8 bytes, byte i = row i, bit j = col j (1=scroll)
  Output: 2 bytes, byte 0 = Part1 count, byte 1 = Part2 count
"""

from __future__ import annotations
import argparse
import os
import random
import sys
from typing import List, Tuple


# ---------- Generic (any size) implementation for full puzzle verification ----------

def parse_text_grid(text: str) -> List[List[int]]:
    rows = [r for r in text.splitlines() if r.strip()]
    return [[1 if c == '@' else 0 for c in row] for row in rows]


def count_neighbors(grid: List[List[int]], r: int, c: int) -> int:
    n = 0
    R = len(grid)
    C = len(grid[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < R and 0 <= cc < C:
                n += grid[rr][cc]
    return n


def part1_generic(grid: List[List[int]]) -> int:
    R, C = len(grid), len(grid[0])
    total = 0
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 1 and count_neighbors(grid, r, c) < 4:
                total += 1
    return total


def part2_generic(grid: List[List[int]]) -> int:
    g = [row[:] for row in grid]
    R, C = len(g), len(g[0])
    total_removed = 0
    while True:
        marks = [[0] * C for _ in range(R)]
        cnt = 0
        for r in range(R):
            for c in range(C):
                if g[r][c] == 1 and count_neighbors(g, r, c) < 4:
                    marks[r][c] = 1
                    cnt += 1
        if cnt == 0:
            break
        for r in range(R):
            for c in range(C):
                if marks[r][c]:
                    g[r][c] = 0
        total_removed += cnt
    return total_removed


# ---------- 8x8 hardware-bound implementation (used by RTL testbench) ----------

GRID_N = 8
MAX_ITER = 64


def parse_axi_stream(byte_list: List[int]) -> List[List[int]]:
    """Convert 8 bytes -> 8x8 grid. byte[i] bit j = grid[i][j]."""
    assert len(byte_list) == GRID_N
    g = []
    for b in byte_list:
        row = [(b >> j) & 1 for j in range(GRID_N)]
        g.append(row)
    return g


def grid_to_axi_bytes(grid: List[List[int]]) -> List[int]:
    out = []
    for row in grid:
        b = 0
        for j in range(GRID_N):
            if row[j]:
                b |= (1 << j)
        out.append(b)
    return out


def count_accessible(grid: List[List[int]]) -> int:
    return part1_generic(grid)


def simulate_removal(grid: List[List[int]]) -> Tuple[int, int]:
    """Returns (total_removed, iterations_used)."""
    g = [row[:] for row in grid]
    total = 0
    iters = 0
    while iters < MAX_ITER:
        marks = [[0] * GRID_N for _ in range(GRID_N)]
        cnt = 0
        for r in range(GRID_N):
            for c in range(GRID_N):
                if g[r][c] == 1 and count_neighbors(g, r, c) < 4:
                    marks[r][c] = 1
                    cnt += 1
        if cnt == 0:
            break
        for r in range(GRID_N):
            for c in range(GRID_N):
                if marks[r][c]:
                    g[r][c] = 0
        total += cnt
        iters += 1
    return total, iters


def run_case(grid_bytes: List[int]) -> dict:
    grid = parse_axi_stream(grid_bytes)
    p1 = count_accessible(grid)
    p2, iters = simulate_removal(grid)
    return {
        "bytes": grid_bytes,
        "part1": p1,
        "part2": p2,
        "iterations": iters,
    }


# ---------- Regression suite ----------

def _mk_empty() -> List[int]:
    return [0x00] * 8


def _mk_full() -> List[int]:
    return [0xFF] * 8


def _mk_checker() -> List[int]:
    out = []
    for r in range(8):
        b = 0
        for c in range(8):
            if (r + c) & 1:
                b |= (1 << c)
        out.append(b)
    return out


def _mk_corner() -> List[int]:
    g = [0] * 8
    g[0] = 0x01  # bit 0 of row 0 set
    return g


def _mk_center_surrounded() -> List[int]:
    # grid[3][3]=1, surround with 8 ones (so center has 8 neighbors -> not accessible)
    g = [0] * 8
    for r in range(2, 5):
        for c in range(2, 5):
            g[r] |= (1 << c)
    return g


def _mk_3x3_block() -> List[int]:
    g = [0] * 8
    for r in range(2, 5):
        for c in range(2, 5):
            g[r] |= (1 << c)
    return g  # same as above; block of 9


def _mk_two_clusters() -> List[int]:
    g = [0] * 8
    # cluster A: 2x2 in top-left
    g[0] |= 0b00000011
    g[1] |= 0b00000011
    # cluster B: 2x2 in bottom-right
    g[6] |= 0b11000000
    g[7] |= 0b11000000
    return g


def _mk_from_puzzle(seed: int = 42) -> List[int]:
    """Pick a random 8x8 sub-window from puzzle_input.txt."""
    path = os.path.join(os.path.dirname(__file__), "puzzle_input.txt")
    if not os.path.exists(path):
        return _mk_empty()
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    full = parse_text_grid(text)
    R, C = len(full), len(full[0])
    if R < 8 or C < 8:
        return _mk_empty()
    rng = random.Random(seed)
    r0 = rng.randint(0, R - 8)
    c0 = rng.randint(0, C - 8)
    out = []
    for r in range(r0, r0 + 8):
        b = 0
        for j, c in enumerate(range(c0, c0 + 8)):
            if full[r][c]:
                b |= (1 << j)
        out.append(b)
    return out


def random_grid(seed: int) -> List[int]:
    """Deterministic 8-byte 8x8 grid for cocotb random regression."""
    rng = random.Random(seed)
    return [rng.randint(0, 255) for _ in range(GRID_N)]


REGRESSION_CASES = [
    ("01_empty",                _mk_empty(),              {"part1": 0, "part2": 0}),
    ("02_full",                  _mk_full(),               {"part1": 4}),                # 4 corners have only 3 neighbors -> accessible
    ("03_checker",              _mk_checker(),            None),
    ("04_corner_single",        _mk_corner(),             {"part1": 1, "part2": 1}),
    ("05_center_surrounded",    _mk_center_surrounded(),  None),
    ("06_3x3_block",            _mk_3x3_block(),          None),
    ("07_two_clusters",         _mk_two_clusters(),       None),
    ("08_puzzle_window",        _mk_from_puzzle(),        None),
]


def run_regression() -> bool:
    print("=" * 88)
    print(f"{'case':<24} {'grid_hex':<22} {'p1':>4} {'p2':>4} {'iter':>5}  {'check':<10}")
    print("=" * 88)
    all_pass = True
    for name, gbytes, expect in REGRESSION_CASES:
        result = run_case(gbytes)
        hexs = " ".join(f"{b:02x}" for b in gbytes)
        status = "ok"
        if expect:
            for k, v in expect.items():
                if result[k] != v:
                    status = f"FAIL({k}={result[k]}!={v})"
                    all_pass = False
        print(f"{name:<24} {hexs:<22} {result['part1']:>4} {result['part2']:>4} {result['iterations']:>5}  {status:<10}")
    print("=" * 88)
    return all_pass


def verify_full_puzzle() -> bool:
    path = os.path.join(os.path.dirname(__file__), "puzzle_input.txt")
    if not os.path.exists(path):
        print("[skip] puzzle_input.txt not found")
        return True
    with open(path, "r", encoding="utf-8") as f:
        grid = parse_text_grid(f.read())
    p1 = part1_generic(grid)
    p2 = part2_generic(grid)
    print(f"[full puzzle] dims = {len(grid)} x {len(grid[0])}")
    print(f"[full puzzle] Part 1 = {p1}  (expected 1464)  {'OK' if p1 == 1464 else 'FAIL'}")
    print(f"[full puzzle] Part 2 = {p2}  (expected 8409)  {'OK' if p2 == 8409 else 'FAIL'}")
    return p1 == 1464 and p2 == 8409


def cmd_full_grid(args: argparse.Namespace) -> int:
    """Run the full 136x136 puzzle grid through the generic solver."""
    path = args.input
    if not os.path.exists(path):
        print(f"error: {path} not found", file=sys.stderr)
        return 1

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    grid = parse_text_grid(text)
    R, C = len(grid), len(grid[0])
    print(f"Grid: {R} x {C}  ({sum(cell for row in grid for cell in row)} scrolls total)")

    p1 = part1_generic(grid)
    print(f"Part 1 (initial accessible):      {p1}")

    g_copy = [row[:] for row in grid]
    iters = 0
    removed_per_iter: List[int] = []
    while True:
        marks = [[0] * C for _ in range(R)]
        cnt = 0
        for r in range(R):
            for c in range(C):
                if g_copy[r][c] == 1 and count_neighbors(g_copy, r, c) < 4:
                    marks[r][c] = 1
                    cnt += 1
        if cnt == 0:
            break
        for r in range(R):
            for c in range(C):
                if marks[r][c]:
                    g_copy[r][c] = 0
        removed_per_iter.append(cnt)
        iters += 1

    p2 = sum(removed_per_iter)
    print(f"Part 2 (total removed, stable):   {p2}")
    print(f"Iterations until stable:          {iters}")
    if removed_per_iter:
        print(f"Removed per iteration:            {removed_per_iter}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AoC 2025 Day 4 golden model / HW verification",
    )
    subparsers = parser.add_subparsers(dest="cmd")

    # default: regression + full puzzle verify
    sub_run = subparsers.add_parser("run", help="Run regression + full-puzzle verify (default)")

    # --full-grid: solve the full puzzle with verbose iteration trace
    sub_fg = subparsers.add_parser("full-grid", help="Solve full puzzle grid with iteration trace")
    sub_fg.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "puzzle_input.txt"),
        help="Path to puzzle input (default: puzzle_input.txt next to this script)",
    )

    args = parser.parse_args()

    if args.cmd == "full-grid":
        return cmd_full_grid(args)

    # default: run everything
    ok_full = verify_full_puzzle()
    print()
    ok_reg = run_regression()
    print()
    print(f"FULL PUZZLE: {'PASS' if ok_full else 'FAIL'}")
    print(f"REGRESSION : {'PASS' if ok_reg else 'FAIL'}")
    return 0 if (ok_full and ok_reg) else 1


if __name__ == "__main__":
    raise SystemExit(main())
