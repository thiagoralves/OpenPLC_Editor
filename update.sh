#!/bin/bash
if [ -d "./new_editor" ]
then
    rm -Rf new_editor
fi
if [ -d "./OpenPLC_Editor" ]
then
    rm -Rf OpenPLC_Editor
fi
git clone https://github.com/thiagoralves/OpenPLC_Editor
if [ -d "./OpenPLC_Editor/editor" ]
then
    mv "./OpenPLC_Editor/editor" ./new_editor
    cp ./OpenPLC_Editor/revision ./
    rm -Rf OpenPLC_Editor
    echo "Update applied successfully"
else
    echo "Error cloning from repository!"
fi
