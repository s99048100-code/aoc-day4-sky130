// =============================================================================
// tt_um_day4_forklift
//   AoC 2025 Day 4 - 8x8 forklift cellular automaton (Sky130A / Tiny Tapeout)
//
// Rule: a scroll is "accessible" iff (#scroll-neighbors in Moore 8-nbhd) < 4.
//   Part 1 = accessible count on initial grid.
//   Part 2 = total removed when iteratively peeling all accessible scrolls
//            until the grid is stable (max 64 iters as a hard guard).
//
// AXI-Stream-like protocol over Tiny Tapeout pins:
//   ui_in [7:0]   = s_tdata  (row byte, bit j = column j)
//   uo_out[7:0]   = m_tdata
//   uio_in [0]    = s_tvalid           (input  from master)
//   uio_in [1]    = m_tready           (input  from master)
//   uio_out[2]    = s_tready           (output to master)
//   uio_out[3]    = m_tvalid           (output to master)
//   uio_out[6:4]  = state[2:0]         (debug)
//   uio_out[7]    = first_iter         (debug)
//   uio_oe        = 8'b1111_1100       (bits 7..2 = outputs, bits 1..0 = inputs)
//
// Sequence:
//   IDLE  : wait for s_tvalid
//   RX    : sample 8 row bytes (one per handshake)
//   COMPUTE: each cycle compute mark = grid & (nbr_count<4); accumulate part2;
//            on first iter latch part1; stop when mark_count == 0 (or guard).
//   TX_P1 : drive m_tdata = part1, m_tvalid = 1, advance on m_tready
//   TX_P2 : drive m_tdata = part2, m_tvalid = 1, advance on m_tready -> IDLE
// =============================================================================

`default_nettype none

module tt_um_day4_forklift (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // -------------------------------------------------------------------------
    // FSM state
    // -------------------------------------------------------------------------
    localparam [2:0] S_IDLE    = 3'd0,
                     S_RX      = 3'd1,
                     S_COMPUTE = 3'd2,
                     S_TX_P1   = 3'd3,
                     S_TX_P2   = 3'd4;

    reg  [2:0] state, state_n;

    // -------------------------------------------------------------------------
    // Handshake wiring
    // -------------------------------------------------------------------------
    wire       s_tvalid = uio_in[0];
    wire       m_tready = uio_in[1];
    reg        s_tready;
    reg        m_tvalid;
    reg  [7:0] m_tdata;

    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------
    reg  [7:0] grid [0:7];
    reg  [2:0] rx_idx;
    reg  [7:0] part1_q, part2_q;
    reg        first_iter;
    reg  [6:0] iter_cnt;       // 0..64

    // -------------------------------------------------------------------------
    // Combinational neighbor count + mark for every cell (8x8 = 64)
    // -------------------------------------------------------------------------
    function automatic [3:0] nbr_count;
        input integer r;
        input integer c;
        integer dr, dc, rr, cc;
        reg     [3:0] sum;
        begin
            sum = 4'd0;
            for (dr = -1; dr <= 1; dr = dr + 1) begin
                for (dc = -1; dc <= 1; dc = dc + 1) begin
                    if (!(dr == 0 && dc == 0)) begin
                        rr = r + dr;
                        cc = c + dc;
                        if (rr >= 0 && rr < 8 && cc >= 0 && cc < 8)
                            sum = sum + {3'b0, grid[rr][cc]};
                    end
                end
            end
            nbr_count = sum;
        end
    endfunction

    reg [7:0] mark [0:7];
    reg [7:0] mark_count;

    integer ir, ic;
    reg [7:0] mc_acc;
    always @* begin : COMB_MARK
        for (ir = 0; ir < 8; ir = ir + 1)
            mark[ir] = 8'h00;
        mc_acc = 8'd0;
        for (ir = 0; ir < 8; ir = ir + 1) begin
            for (ic = 0; ic < 8; ic = ic + 1) begin
                if (grid[ir][ic] && (nbr_count(ir, ic) < 4'd4)) begin
                    mark[ir][ic] = 1'b1;
                    mc_acc = mc_acc + 8'd1;
                end
            end
        end
        mark_count = mc_acc;
    end

    // -------------------------------------------------------------------------
    // FSM next-state
    // -------------------------------------------------------------------------
    always @* begin
        state_n = state;
        case (state)
            S_IDLE   : if (s_tvalid) state_n = S_RX;
            S_RX     : if (s_tvalid && (rx_idx == 3'd7)) state_n = S_COMPUTE;
            S_COMPUTE: if (mark_count == 8'd0 || iter_cnt == 7'd64) state_n = S_TX_P1;
            S_TX_P1  : if (m_tready) state_n = S_TX_P2;
            S_TX_P2  : if (m_tready) state_n = S_IDLE;
            default  : state_n = S_IDLE;
        endcase
    end

    // -------------------------------------------------------------------------
    // Sequential
    // -------------------------------------------------------------------------
    integer k;
    always @(posedge clk) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            rx_idx     <= 3'd0;
            part1_q    <= 8'd0;
            part2_q    <= 8'd0;
            first_iter <= 1'b1;
            iter_cnt   <= 7'd0;
            for (k = 0; k < 8; k = k + 1) grid[k] <= 8'h00;
        end else begin
            state <= state_n;

            case (state)
                S_IDLE: begin
                    rx_idx     <= 3'd0;
                    part1_q    <= 8'd0;
                    part2_q    <= 8'd0;
                    first_iter <= 1'b1;
                    iter_cnt   <= 7'd0;
                end

                S_RX: begin
                    if (s_tvalid) begin
                        grid[rx_idx] <= ui_in;
                        rx_idx       <= rx_idx + 3'd1;
                    end
                end

                S_COMPUTE: begin
                    if (first_iter) begin
                        part1_q    <= mark_count;
                        first_iter <= 1'b0;
                    end
                    if (mark_count != 8'd0 && iter_cnt != 7'd64) begin
                        part2_q  <= part2_q + mark_count;
                        iter_cnt <= iter_cnt + 7'd1;
                        for (k = 0; k < 8; k = k + 1)
                            grid[k] <= grid[k] & ~mark[k];
                    end
                end

                default: ;
            endcase
        end
    end

    // -------------------------------------------------------------------------
    // Handshake / output drive
    // -------------------------------------------------------------------------
    always @* begin
        s_tready = (state == S_RX);
        m_tvalid = (state == S_TX_P1) || (state == S_TX_P2);
        m_tdata  = (state == S_TX_P1) ? part1_q : part2_q;
    end

    assign uo_out       = m_tdata;
    assign uio_out[1:0] = 2'b00;          // bits 1..0 are inputs (driven by master)
    assign uio_out[2]   = s_tready;
    assign uio_out[3]   = m_tvalid;
    assign uio_out[6:4] = state;
    assign uio_out[7]   = first_iter;
    assign uio_oe       = 8'b1111_1100;

    // unused
    wire _unused = &{ena, 1'b0};

`ifdef FORMAL
    // -------------------------------------------------------------------------
    // Safety + bound assertions (proven by yosys sat -prove-asserts).
    // -------------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n) begin
            // P1: iteration counter is bounded by the FSM guard.
            assert (iter_cnt <= 7'd64);
            // P2: FSM state stays in the declared encoding (0..4).
            assert (state <= 3'd4);
            // P3: Part-1 fits inside 7 bits (max 64 accessible cells).
            assert (part1_q <= 8'd64);
            // P4: Part-2 (cumulative removed) is bounded by total cells.
            assert (part2_q <= 8'd64);
            // P5: rx_idx never advances past row 7.
            assert (rx_idx <= 3'd7);
            // P6: TX states drive the matching result on m_tdata.
            if (state == S_TX_P1) assert (m_tdata == part1_q);
            if (state == S_TX_P2) assert (m_tdata == part2_q);
            // P7: s_tready high iff state == RX.
            assert ((state == S_RX) == s_tready);
        end
    end
`endif

endmodule

`default_nettype wire
