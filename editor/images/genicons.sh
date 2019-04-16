#!/bin/sh

INKSCAPE=inkscape

for fname in `ls *.svg`; do
    for i in `cat $fname |grep -o -e '%%[^%]*%%'|sed 's/%//g'` 
    do
        if [ $i.png -nt $fname ]; then
 	    echo "Skip $i"
        else
	    rm  -f $i.png
	    echo "$INKSCAPE" $fname -z -e $i.png -i $i
	    "$INKSCAPE" $fname -z -e $i.png -i $i
        fi
    done
done

cp ico024.png brz.png
convert -compress none ico*.png brz.ico
rm -f ico*.png


convert -compress none poeico*.png poe.ico
rm -f poeico*.png

