CFLAGS ?= -O2 -Wall -Wextra -arch arm64 -arch x86_64

awdlkiller: awdlkiller.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f awdlkiller

.PHONY: clean
