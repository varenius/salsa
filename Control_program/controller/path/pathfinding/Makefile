CC=g++
CXX_FLAGS=-std=gnu++14 -O3 -Wall -Wextra -Wpedantic
IPY=/usr/include/python2.7
FNAME=path_finder
BUILD_DIR=build

.PHONY: compile
compile: $(BUILD_DIR)
	if [ ! -d $(BUILD_DIR) ]; then mkdir -p $(BUILD_DIR); fi
	swig -c++ -python -o $(FNAME)_wrap.cpp $(FNAME).i
	$(CC) -c -fpic $(CXX_FLAGS) $(FNAME).cpp -o $(BUILD_DIR)/$(FNAME).o
	$(CC) -c -fpic $(CXX_FLAGS) $(FNAME)_wrap.cpp -I$(IPY) -o $(BUILD_DIR)/$(FNAME)_wrap.o
	$(CC) -shared $(CXX_FLAGS) $(BUILD_DIR)/$(FNAME).o $(BUILD_DIR)/$(FNAME)_wrap.o -o _$(FNAME).so

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

.PHONY: clean
clean:
	bash -c "rm -rf $(BUILD_DIR) $(FNAME)_wrap.cpp _$(FNAME).so $(FNAME).py $(FNAME).pyc > /dev/null 2>&1"
