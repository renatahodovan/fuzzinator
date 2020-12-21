# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

PROG = crashme
PROG_DEBUG = $(PROG)-debug
SRCS = crashme.cpp

ASAN_TESTS = \
	container-overflow \
	double-free \
	heap-buffer-overflow \
	heap-use-after-free \
	null-pointer-dereference \
	stack-overflow \
	stack-use-after-scope

UBSAN_ASAN_TESTS = \
	division-by-zero \
	global-buffer-overflow \
	stack-buffer-overflow \
	null-deref-read \
	null-deref-write

UBSAN_TESTS = \
	shifts \
	signed-integer-overflow

TXTS := \
	$(patsubst %,asan_%.txt,$(subst -,_,$(ASAN_TESTS))) \
	$(patsubst %,ubsan_asan_%.txt,$(subst -,_,$(UBSAN_ASAN_TESTS))) \
	$(patsubst %,ubsan_%.txt,$(subst -,_,$(UBSAN_TESTS)))

TXTS_DEBUG := $(patsubst %.txt,%_debug.txt,$(TXTS))

# CXX = clang++
# CXXFLAGS = -fsanitize=address,undefined,float-divide-by-zero,float-cast-overflow,unsigned-integer-overflow,implicit-conversion,integer
CXX = g++
CXXFLAGS = -fsanitize=address,undefined,float-divide-by-zero,float-cast-overflow,signed-integer-overflow
CXXFLAGS_DEBUG = $(CXXFLAGS) -g

all: $(PROG) $(PROG_DEBUG) $(TXTS) $(TXTS_DEBUG)

$(PROG): $(SRCS)
	$(CXX) $(CXXFLAGS) $^ -o $@

$(PROG_DEBUG): $(SRCS)
	$(CXX) $(CXXFLAGS_DEBUG) $^ -o $@

# FIXME(unnecessary?)
# export ASAN_OPTIONS=detect_stack_use_after_return=1

$(TXTS): $(PROG)
	-./$(PROG) $(subst _,-,$(subst .txt,,$(subst ubsan_,,$(subst asan_,,$@)))) 2>&1 | sed -e 's|$(PWD)/||' >$@

$(TXTS_DEBUG): $(PROG_DEBUG)
	-./$(PROG_DEBUG) $(subst _,-,$(subst _debug.txt,,$(subst ubsan_,,$(subst asan_,,$@)))) 2>&1 | sed -e 's|$(PWD)/||' >$@

clean:
	rm -rf $(PROG)

.PHONY: all clean
