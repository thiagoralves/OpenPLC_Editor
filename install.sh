#!/bin/bash
echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"
sudo apt-get -y -qq update
sudo apt-get -y -qq install build-essential pkg-config bison flex autoconf automake libtool make git libssl-dev python2.7 python-pip python-wxgtk3.0
pip2 install future zeroconf==0.19.1 numpy matplotlib==2.0.2 lxml pyro sslpsk
echo ""
echo "[COMPILING MATIEC]"
cd matiec
autoreconf -i
./configure
make -s
echo ""
echo "[FINALIZING]"
cd ..
WORKING_DIR=$(pwd)
echo -e "#!/bin/bash\n\
cd \"$WORKING_DIR/editor\"\n\
python2.7 Beremiz.py" > openplc_editor.sh
chmod +x ./openplc_editor.sh
cd ~/.local/share/applications
echo -e "[Desktop Entry]\n\
Name=OpenPLC Editor v1.0\n\
Exec=\"$WORKING_DIR/openplc_editor.sh\"\n\
Icon=\"$WORKING_DIR/editor/images/brz.ico\"\n\
Type=Application\n\
Terminal=false" > OpenPLC_Editor.desktop
