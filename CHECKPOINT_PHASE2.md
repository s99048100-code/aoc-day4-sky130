# CHECKPOINT_PHASE2 — Phase 2 + 3 完成

## 已完成
- [x] RTL、golden model、cocotb、baseline PnR
- [x] ppa_report.md（baseline 50 MHz）
- [x] aggressive run（100 MHz）— partial PnR，數字已記錄
- [x] ppa_compare.md — 完成
- [x] KLayout 截圖（docs/klayout_layout.png、docs/klayout_caravel_context.png）
- [x] docs/design_notes.md
- [x] docs/golden_model_output.txt（1464/8409 verified）
- [x] docs/cocotb_log.txt（TESTS=1 PASS=1 FAIL=0）
- [x] README.md 完整版（含 FSM Mermaid、PPA、verification、layout 截圖）
- [x] .gitignore 完整版（含 puzzle_input.txt）
- [x] LICENSE（Apache-2.0）
- [x] git init + author s99048100-code
- [x] 初始 commit（1 commit，no Claude author）

## 關鍵檔案路徑
- RTL：D:/aoc_day4/src/project.v
- baseline metrics：D:/aoc_day4/runs/baseline/final/metrics.json
- GDS：D:/aoc_day4/runs/baseline/final/klayout_gds/tt_um_day4_forklift.klayout.gds
- ppa_report：D:/aoc_day4/ppa_report.md
- ppa_compare：D:/aoc_day4/ppa_compare.md
- golden model：D:/aoc_day4/day4_golden_model.py

## 正確答案
- Part 1: 1464 ✓
- Part 2: 8409 ✓

## 下一步
在 GitHub 建立 repo `aoc-day4-backend`（public），建好後告訴我 username
再執行 remote add + push。
