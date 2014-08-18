
PROGFILES=tattletale32

all: $(PROGFILES)


clean:

mydir = /ictf/services/tattletale
install: all
	mkdir -p $(DESTDIR)$(mydir)
	install $(PROGFILES) start.sh stop.sh $(DESTDIR)$(mydir)

.PHONY: all clean install

