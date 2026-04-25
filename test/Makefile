# cocotb Makefile for tt_um_day4_forklift
SIM            ?= icarus
TOPLEVEL_LANG  ?= verilog
TOPLEVEL       := tt_um_day4_forklift
MODULE         := test

VERILOG_SOURCES := $(PWD)/../src/project.v

# Icarus needs SystemVerilog-ish features for `default_nettype etc.
COMPILE_ARGS   += -g2012

include $(shell cocotb-config --makefiles)/Makefile.sim
