// =============================================================================
// tt_um_day4_forklift  —  PIPELINED variant (Phase 3 / M5)
//
// Same external interface as src/project.v.  The combinational COMB_MARK sweep
// is split across two cycles by registering the per-cell `mark` between the
// neighbour-count + comparator stage and the peel + popcount stage.
//
//   Baseline path :  grid -> nbr_count adder tree -> <4 cmp -> AND -> grid_n
//                    (~30 logic levels, SS WNS = -13 ns @ 50 MHz)
//
//   Pipelined path:  grid -> nbr_count + cmp -> mark_q     (Stage 1)
//                    mark_q -> popcount + AND -> grid_n     (Stage 2)
//                    (~half the logic depth per cycle, +64 FF)
//
//   Cost          :  one extra cycle per peel iteration; throughput halved,
//                    fmax doubled.
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
    // FSM state — two new states (COUNT + PEEL) replace the single COMPUTE.
    // -------------------------------------------------------------------------
    localparam [2:0] S_IDLE  = 3'd0,
                     S_RX    = 3'd1,
                     S_COUNT = 3'd2,
                     S_PEEL  = 3'd3,
                     S_TX_P1 = 3'd4,
                     S_TX_P2 = 3'd5;

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
    reg  [7:0] grid   [0:7];
    reg  [7:0] mark_q [0:7];      // Stage-1 -> Stage-2 pipeline register
    reg  [2:0] rx_idx;
    reg  [7:0] part1_q, part2_q;
    reg        first_iter;
    reg  [6:0] iter_cnt;

    // -------------------------------------------------------------------------
    // Stage 1 — combinational mark from current grid (NO popcount here).
    // -------------------------------------------------------------------------
    function automatic [3:0] nbr_count;
        input integer r;
        input integer c;
        integer dr, dc, rr, cc;
        reg     [3:0] sum;
        begin
            sum = 4'd0;
            for (dr = -1; dr <= 1; dr = dr + 1)
                for (dc = -1; dc <= 1; dc = dc + 1)
                    if (!(dr == 0 && dc == 0)) begin
                        rr = r + dr;
                        cc = c + dc;
                        if (rr >= 0 && rr < 8 && cc >= 0 && cc < 8)
                            sum = sum + {3'b0, grid[rr][cc]};
                    end
            nbr_count = sum;
        end
    endfunction

    reg [7:0] mark_d [0:7];
    integer ir, ic;
    always @* begin : COMB_MARK_STAGE1
        for (ir = 0; ir < 8; ir = ir + 1)
            mark_d[ir] = 8'h00;
        for (ir = 0; ir < 8; ir = ir + 1)
            for (ic = 0; ic < 8; ic = ic + 1)
                if (grid[ir][ic] && (nbr_count(ir, ic) < 4'd4))
                    mark_d[ir][ic] = 1'b1;
    end

    // -------------------------------------------------------------------------
    // Stage 2 — popcount of registered mark_q.
    // -------------------------------------------------------------------------
    reg [7:0] mark_count;
    integer pi, pj;
    always @* begin
        mark_count = 8'd0;
        for (pi = 0; pi < 8; pi = pi + 1)
            for (pj = 0; pj < 8; pj = pj + 1)
                mark_count = mark_count + {7'b0, mark_q[pi][pj]};
    end

    // -------------------------------------------------------------------------
    // FSM next-state
    // -------------------------------------------------------------------------
    always @* begin
        state_n = state;
        case (state)
            S_IDLE  : if (s_tvalid) state_n = S_RX;
            S_RX    : if (s_tvalid && (rx_idx == 3'd7)) state_n = S_COUNT;
            S_COUNT : state_n = S_PEEL;
            S_PEEL  : begin
                if (mark_count == 8'd0 || iter_cnt == 7'd64) state_n = S_TX_P1;
                else                                         state_n = S_COUNT;
            end
            S_TX_P1 : if (m_tready) state_n = S_TX_P2;
            S_TX_P2 : if (m_tready) state_n = S_IDLE;
            default : state_n = S_IDLE;
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
            for (k = 0; k < 8; k = k + 1) begin
                grid[k]   <= 8'h00;
                mark_q[k] <= 8'h00;
            end
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

                // Stage 1: latch new combinational mark.  Grid is unchanged.
                S_COUNT: begin
                    for (k = 0; k < 8; k = k + 1)
                        mark_q[k] <= mark_d[k];
                end

                // Stage 2: popcount + accumulate + peel.  mark_count is
                // combinational from mark_q (post-latch).
                S_PEEL: begin
                    if (first_iter) begin
                        part1_q    <= mark_count;
                        first_iter <= 1'b0;
                    end
                    if (mark_count != 8'd0 && iter_cnt != 7'd64) begin
                        part2_q  <= part2_q + mark_count;
                        iter_cnt <= iter_cnt + 7'd1;
                        for (k = 0; k < 8; k = k + 1)
                            grid[k] <= grid[k] & ~mark_q[k];
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
    assign uio_out[1:0] = 2'b00;
    assign uio_out[2]   = s_tready;
    assign uio_out[3]   = m_tvalid;
    assign uio_out[6:4] = state;
    assign uio_out[7]   = first_iter;
    assign uio_oe       = 8'b1111_1100;

    wire _unused = &{ena, 1'b0};

endmodule

`default_nettype wire
