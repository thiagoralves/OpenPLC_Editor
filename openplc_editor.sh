#!/bin/bash
cd "/home/pi/Documents/GitHub/OpenPLC_Editor"
if [ -d "./new_editor" ]
then
    rm -Rf editor
    rm -Rf ./matiec/lib
    mv ./new_editor ./editor
    mv ./new_lib ./matiec/lib
fi
python2.7 ./editor/Beremiz.py
