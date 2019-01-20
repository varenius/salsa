CFLAGS=-Wall -Wextra -Wpedantic
#COPT=-Og -ggdb
COPT=-O2
CC=gcc
CCSTD=-std=gnu99
CLNK=-lpthread -lm

OUT=build
SRC=$(wildcard src/*.c)

.PHONY: all
all: server

.PHONY: server
server: $(OUT)
	$(CC) $(CCSTD) $(CFLAGS) $(COPT) $(SRC) $(CLNK) -o $(OUT)/rio_server

$(OUT):
	mkdir -p $(OUT)

.PHONY: clean
clean:
	rm -r $(OUT)
