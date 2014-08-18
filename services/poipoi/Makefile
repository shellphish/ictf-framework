CC=gcc
CFLAGS=-m32 -fno-stack-protector -Wall
SRC=src
_DEPS=dbhelper.h my_poi.h registration.h screens.h errors.h exit.h help.h util.h
DEPS = $(patsubst %,$(SRC)/%,$(_DEPS))
_OBJ=dbhelper.o my_poi.o registration.o screens.o exit.o help.o util.o
OBJ = $(patsubst %,$(SRC)/%,$(_OBJ))

all: poipoi

$(SRC)/%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

poipoi: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(SRC)/main.c

clean:
	rm -f $(SRC)/*.o poipoi

mydir = /ictf/services/poipoi
install: GM/poipoi
	mkdir -p $(DESTDIR)\$(mydir)
	install GM/poipoi start.sh stop.sh $(DESTDIR)\$(mydir)
