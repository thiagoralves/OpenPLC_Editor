BEREMIZ_OBJS = $(BEREMIZSRC:.c=.o)

all: warn some_binary
	@echo "*** all done ***"

warn:
	@echo "*** Sample Makefile, does nothing ***"

some_binary: $(BEREMIZ_OBJS)
	@echo "* Would link $^ -> $@"

%.o: %.c
	@echo "* Would compile $< -> $@"
