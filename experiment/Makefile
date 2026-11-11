SDK ?= $(HOME)/steamaudio/sdk
CC ?= gcc
CFLAGS ?= -O2 -Wall -I$(SDK)/include
LDFLAGS ?= -L$(SDK)/lib -Wl,-rpath,$(SDK)/lib -lphonon -lm

wall_experiment: wall_experiment.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f wall_experiment
