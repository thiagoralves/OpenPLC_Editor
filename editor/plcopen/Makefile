#! gmake

yml := ../../yml2
ysl2files := $(wildcard *.ysl2)
xsltfiles := $(patsubst %.ysl2, %.xslt, $(ysl2files))

all:$(xsltfiles)

%.xslt: %.ysl2 yslt_noindent.yml2
	$(yml)/yml2c -I $(yml) $< -o $@.tmp
	xmlstarlet fo $@.tmp > $@
	rm $@.tmp
	
clean:
	rm -f $(xsltfiles)
