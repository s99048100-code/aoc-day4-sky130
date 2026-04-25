# CHECKPOINT_PHASE2 — Phase 2 中斷點

## 已完成
- RTL、golden model、cocotb、baseline PnR
- ppa_report.md（baseline 50 MHz）
- aggressive run（100 MHz）— 成功
- ppa_compare.md — 完成

## 待完成（照順序）
- KLayout 截圖（docs/klayout_layout.png、docs/klayout_caravel_context.png）
- docs/design_notes.md
- README.md 完整版
- docs/golden_model_output.txt（--full-grid 驗算）
- docs/cocotb_log.txt

## 關鍵檔案路徑
- RTL：D:/aoc_day4/src/project.v
- baseline metrics：D:/aoc_day4/runs/baseline/final/metrics.json
- GDS：D:/aoc_day4/runs/baseline/final/klayout_gds/tt_um_day4_forklift.klayout.gds
- ppa_report：D:/aoc_day4/ppa_report.md
- ppa_compare：D:/aoc_day4/ppa_compare.md
- golden model：D:/aoc_day4/day4_golden_model.py
- puzzle input：D:/aoc_day4/puzzle_input.txt（不進 repo）

## 正確答案
- Part 1: 1464
- Part 2: 8409

## 風格要求
- 工程師語氣，不要 AI 腔
- 不用「值得注意的是」「此外」「綜上所述」
- 數字不確定寫「待 STA 確認」，不要編

## 下一步
KLayout 截圖 → design_notes.md → README.md → cocotb log → Phase 3
