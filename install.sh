#!/bin/bash

echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"

sudo apt -y -qq update

sudo apt -y -qq install python3
sudo apt -y -qq install python3-pip
sudo apt -y -qq install python3-wxgtk4.0
sudo apt -y -qq install build-essential bison flex autoconf

if [ $? -ne 0 ]; then
    #Manual install
    echo "Manually installing python3-wxgtk4.0..."
    sudo dpkg -i ./wxpython/python3-wxgtk4.0_4.0.7+dfsg-10_amd64.deb
fi

pip3 install lxml matplotlib zeroconf pyserial gnosis simplejson nevow jinja2

echo ""
echo "[COMPILING MATIEC]"
cd matiec
autoreconf -i
./configure
make -s
cp ./iec2c ../editor/arduino/bin/
echo ""
echo "[FINALIZING]"
cd ..

WORKING_DIR=$(pwd)
echo -e "#!/bin/bash\n\
cd \"$WORKING_DIR\"\n\
python3 ./editor/Beremiz.py" > openplc_editor.sh
chmod +x ./openplc_editor.sh

mkdir -p ~/.local/share/applications
cd ~/.local/share/applications || exit
echo -e "[Desktop Entry]\n\
Name=OpenPLC Editor\n\
Categories=Development;\n\
Exec=\"$WORKING_DIR/openplc_editor.sh\"\n\
Icon=$WORKING_DIR/editor/images/brz.png\n\
Type=Application\n\
Terminal=false" > OpenPLC_Editor.desktop
