# use pyuic4 in UI and compile pyprogbar and pathfinding
SUBDIRS= UI controller/pyprogbar controller/path/pathfinding

.PHONY: subdirs $(SUBDIRS)
subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@


.PHONY: clean

clean:
	cd UI && make clean
	cd controller/pyprogbar && make clean
	cd controller/path/pathfinding && make clean
