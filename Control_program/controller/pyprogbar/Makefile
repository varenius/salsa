CFLAGS=-std=c89 -O3 -Wall -Wextra
IPY=/usr/include/python2.7
OUT=build

compile: $(OUT)
	swig -python progressbar.i
	gcc -c -fpic $(CFLAGS) progressbar.c -I$(IPY) -o $(OUT)/progressbar.o
	gcc -c -fpic $(CFLAGS) ansi_ctrl.c -I$(IPY) -o $(OUT)/ansi_ctrl.o
	gcc -c -fpic $(CFLAGS) progressbar_wrap.c -I$(IPY) -o $(OUT)/progressbar_wrap.o
	gcc -shared $(CFLAGS) $(OUT)/progressbar.o $(OUT)/ansi_ctrl.o $(OUT)/progressbar_wrap.o -o _progressbar.so

$(OUT):
	mkdir -p $(OUT)

clean:
	bash -c "rm -r $(OUT) progressbar_wrap.c _progressbar.so progressbar.py *.pyc > /dev/null 2>&1"
