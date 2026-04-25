# tt_um_day4_forklift — FSM

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {
    'background':'#000000',
    'primaryColor':'#1a2540',
    'primaryBorderColor':'#3b6fb5',
    'primaryTextColor':'#e6edf3',
    'lineColor':'#7da3d4',
    'secondaryColor':'#222a36',
    'tertiaryColor':'#0f1521'
}}}%%
stateDiagram-v2
    [*] --> S_IDLE

    S_IDLE: S_IDLE\nclear part1/part2\nrx_idx=0, first_iter=1
    S_RX: S_RX\ngrid[rx_idx] <= ui_in\nrx_idx++ on handshake
    S_COMPUTE: S_COMPUTE\nmark = grid AND (nbr_count<4)\nfirst_iter -> latch part1\nelse -> part2 += popcount(mark)\ngrid &= ~mark\niter_cnt++
    S_TX_P1: S_TX_P1\nm_tdata = part1\nm_tvalid = 1
    S_TX_P2: S_TX_P2\nm_tdata = part2\nm_tvalid = 1

    S_IDLE  --> S_RX        : s_tvalid
    S_RX    --> S_RX        : handshake & rx_idx<7
    S_RX    --> S_COMPUTE   : handshake & rx_idx==7
    S_COMPUTE --> S_COMPUTE : mark_count!=0 & iter<64
    S_COMPUTE --> S_TX_P1   : mark_count==0 OR iter==64
    S_TX_P1 --> S_TX_P2     : m_tready
    S_TX_P2 --> S_IDLE      : m_tready
```

## Cycle budget

| Phase     | Cycles                              | Notes |
|-----------|-------------------------------------|-------|
| S_RX      | 8 (one per AXI handshake)           | one byte per cycle when master keeps `s_tvalid=1` |
| S_COMPUTE | iter+1 (max 65)                     | combinational mark; up to 64 peel iterations + 1 stable check |
| S_TX_P1   | 1+ (waits for `m_tready`)           | back-pressure aware |
| S_TX_P2   | 1+ (waits for `m_tready`)           | returns to IDLE |

Worst case at 50 MHz: ~75 cycles ≈ 1.5 µs per 8x8 grid.
