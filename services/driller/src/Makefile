all:
	g++ -S main.cpp GlobalState.cpp Helper.cpp User.cpp Spot.cpp Driller.cpp Menu.cpp -m32 -Wno-write-strings -O3
	python obfuscate.py
	g++ main.s GlobalState.s Helper.s User.s Spot.s Driller.s Menu.s -m32 -Llibs -lcryptopp -lsqlite3 -Wno-write-strings -o driller
	strip driller
	rm *.s

mydir = /ictf/services/driller

install: all
	mkdir -p $(DESTDIR)$(mydir)
	install driller start.sh stop.sh $(DESTDIR)$(mydir)

.PHONY: clean all install
clean:
	-rm -f driller 2 > /dev/null

