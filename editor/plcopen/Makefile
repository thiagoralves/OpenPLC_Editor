#! gmake

# Makefile to generate XSLT stylesheets from ysl2 files in the same directory

# This uses YML2. 
#   hg clone https://pep.foundation/dev/repos/yml2/

# It should be just fine if yml2 is cloned just asside beremiz
# otherwise, point yml2path to yml2 source directory
#   make yml2path=path/to/yml/dir

yml2path ?= $(abspath ../../yml2)

ysl2files := $(wildcard *.ysl2)
xsltfiles := $(patsubst %.ysl2, %.xslt, $(ysl2files))

all:$(xsltfiles)

%.xslt: %.ysl2 ../yslt_noindent.yml2
	$(yml2path)/yml2c -I $(yml2path):../ $< -o $@.tmp
	xmlstarlet fo $@.tmp > $@
	rm $@.tmp
	
clean:
	rm -f $(xsltfiles)
