CFLAGS=-Wall -Wextra -Wpedantic
#COPT=-Og -ggdb
COPT=-O2
CC=gcc
CCSTD=-std=gnu99
CLNK=-lgclib -lgclibo

OUT=build
SRC=$(wildcard src/*.c)

.PHONY: all
all: gclib

.PHONY: gclib
gclib: $(OUT)
	$(CC) $(CCSTD) $(CFLAGS) $(COPT) $(SRC) $(CLNK) -o $(OUT)/rio_init

.PHONY: nogclib
nogclib: $(OUT)
	$(CC) $(CCSTD) $(CFLAGS) $(COPT) $(SRC) -o $(OUT)/rio_init

$(OUT):
	mkdir -p $(OUT)

.PHONY: clean
clean:
	rm -r $(OUT)
