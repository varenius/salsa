# use pyuic4 in UI and compile pyprogbar written in C
SUBDIRS= UI controller/pyprogbar

.PHONY: subdirs $(SUBDIRS)
subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@


.PHONY: clean

clean:
	cd UI && make clean
	cd controller/pyprogbar && make clean
