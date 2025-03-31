#  Copyright 2023 Hel Industries, all rights reserved.
#
#  For licensing terms, Please find the licensing terms in the closest
#  LICENSE.txt in this repository file going up the directory tree.
#
# This Makefile is meant to be used to build a binary distribution, it is not meant for inclusion
# inclusion in a project Makefile, but merely for running tests on the contained scripts. This
# also requires the Makefile-based hybrid build system to work properly
#

all: build-python-timestamps | silent
	@

install: | silent
	@

test: test-python | silent
	@

clean: | silent
	@

cfg: cfg-python | silent
	@

.PHONY: all install test clean

PYTHON_FILES := $(wildcard *.py tests/*.py)
PYTHON_FILES_TIMESTAMP := $(PYTHON_FILES:%.py=$(BUILD_DIR)/%.build)

include ../../../Config/BuildSystem.mk
include $(MAKE_INC_PATH)/Python.mk

build-python-timestamps: $(PYTHON_BUILD_TIMESTAMP)
	@

$(PYTHON_BUILD_TIMESTAMP): $(PYTHON_FILES) build-python
	$(V)touch $@

.PHONY: build-python-timestamps