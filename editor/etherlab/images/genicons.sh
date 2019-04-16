#!/bin/bash

INKSCAPE=inkscape

for i in `cat icons.svg |grep -o -e '%%[^%]*%%'|sed 's/%//g'` 
do
 if [ $i.png -nt icons.svg ]; then
 	echo "Skip $i"
 else
	rm  -f $i.png
	echo "$INKSCAPE" icons.svg -z -e $i.png -i $i
	"$INKSCAPE" icons.svg -z -e $i.png -i $i
 fi
done

