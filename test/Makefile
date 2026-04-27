# cocotb Makefile for tt_um_day4_forklift
SIM            ?= icarus
TOPLEVEL_LANG  ?= verilog
TOPLEVEL       := tt_um_day4_forklift
MODULE         := test

VARIANT        ?= baseline
ifeq ($(VARIANT),pipelined)
    VERILOG_SOURCES := $(PWD)/../src/project_pipelined.v
else
    VERILOG_SOURCES := $(PWD)/../src/project.v
endif

# Icarus needs SystemVerilog-ish features for `default_nettype etc.
COMPILE_ARGS   += -g2012

include $(shell cocotb-config --makefiles)/Makefile.sim
