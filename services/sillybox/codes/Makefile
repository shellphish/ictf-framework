all: simple.code reader.code writer.code writer_and_reader.code reader_of_len.code exploit_simple.code

FILENAME ?= flagidXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
CONTENT ?= "FLG4567890123456"
FIXED_READ_LEN ?= 100

%.code: %.nasm.S Makefile
	$(CPP) $(CPPFLAGS) -DFILENAME=\'$(FILENAME)\' -DCONTENT=\'$(CONTENT)\' -DFIXED_READ_LEN=$(FIXED_READ_LEN) -o $<.preprocessed $<
	nasm -f bin -o $@ $<.preprocessed
	rm -f $<.preprocessed

.PHONY: clean all install
clean:
	-rm -f *.code *.pyc 2>/dev/null
