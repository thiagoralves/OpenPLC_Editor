#!/bin/bash
echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"
sudo apt-get -y -qq update
#Main packages
sudo apt-get -y -qq install curl build-essential pkg-config bison flex autoconf automake libtool make git libssl-dev
#Python 2. Some distros call it python2, some others call it python2.7. Try instaling both
sudo apt-get -y -qq install python2
sudo apt-get -y -qq install python2.7
#Trying to install python-wxgtk3.0. If it fails, summon manual install
sudo apt-get -y -qq install python-wxgtk3.0
if [ $? -ne 0 ]
then
  #Manual install
  echo "Manually installing python-wxgtk3.0..."
  sudo apt-get -y -qq install python libwxbase3.0-0v5 libwxgtk3.0-gtk3-0v5
  sudo dpkg -i ./wxpython/python-wxversion_3.0.2.0+dfsg-8_all.deb
  sudo dpkg -i ./wxpython/python-wxgtk3.0_3.0.2.0+dfsg-8_amd64.deb
fi
#For Python sslpsk
sudo apt-get -y -qq install libssl-dev
#For Python lxml
sudo apt-get -y -qq install libxml2-dev libxslt1-dev
#Fixes python.h include issues
sudo apt-get -y -qq install python2-dev
sudo apt-get -y -qq install python2.7-dev
#Get pip manually
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2.7 get-pip.py
#Fix for Debian Buster
sudo apt-get -y -qq install libpng libpng-dev libfreetype6-dev
pip2 install future zeroconf==0.19.1 numpy==1.16.5 matplotlib==2.0.2 lxml pyro sslpsk pyserial
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
if [ -d \"./new_editor\" ]\n\
then\n\
    rm -Rf editor\n\
    mv ./new_editor ./editor\n\
fi\n\
python2.7 ./editor/Beremiz.py" > openplc_editor.sh
chmod +x ./openplc_editor.sh
cd ~/.local/share/applications
echo -e "[Desktop Entry]\n\
Name=OpenPLC Editor\n\
Categories=Development;\n\
Exec=\"$WORKING_DIR/openplc_editor.sh\"\n\
Icon=$WORKING_DIR/editor/images/brz.png\n\
Type=Application\n\
Terminal=false" > OpenPLC_Editor.desktop
