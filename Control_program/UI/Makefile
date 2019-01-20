SRC=$(wildcard *.ui)
OBJ=$(SRC:.ui=.py)
CC=pyuic4

.PHONY: all
all: $(OBJ)

%.py: %.ui
	$(CC) $< -o $@

.PHONY: clean
clean:
	rm $(OBJ)
