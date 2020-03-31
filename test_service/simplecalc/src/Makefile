CFLAGS += -Wall
all: simplecalc
clean:
	rm -f simplecalc
simplecalc: simplecalc.c
	gcc -o simplecalc -m32 simplecalc.c -fPIE -pie
.PHONY: all clean
