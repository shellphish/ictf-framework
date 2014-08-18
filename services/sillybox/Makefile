mydir = /ictf/services/sillybox
CFLAGS = -m32 -D_GNU_SOURCE -std=gnu99 -Wall -s -O3 -DNDEBUG -march=core2 -DMY_PATH=\"$(mydir)\"
LDFLAGS = -lcrypt

include /usr/share/hardening-includes/hardening.make
CFLAGS += $(HARDENING_CFLAGS)
LDFLAGS += $(HARDENING_LDFLAGS)


PROGFILES = sillybox_spawner sillybox_timekiller sillybox
DATAFILES = README

all: $(PROGFILES) $(DATAFILES)
%: %.c sillybox_utils.h Makefile $(DATAFILES)
	$(CC) -o $@ $< $(CFLAGS) $(LDFLAGS)

.PHONY: clean all install
clean:
	-rm -f $(PROGFILES) 2>/dev/null

install: all
	mkdir -p $(DESTDIR)$(mydir)
	install $(PROGFILES) start.sh stop.sh $(DESTDIR)$(mydir)
	install -m 644 $(DATAFILES) $(DESTDIR)$(mydir)
