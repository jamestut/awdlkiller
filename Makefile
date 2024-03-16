CFLAGS ?= -O2 -Wall -Wextra -arch arm64 -arch x86_64

WORKDIRNAME := $(shell basename $(shell pwd))

awdlkiller.zip: awdlkiller misc/jamestut.awdlkiller.plist misc/manager.py misc/installer.py
	cd .. && zip $(WORKDIRNAME)/$@ $(addprefix $(WORKDIRNAME)/,$^)

awdlkiller: awdlkiller.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f awdlkiller

.PHONY: clean
