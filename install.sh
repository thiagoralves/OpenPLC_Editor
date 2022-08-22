#!/bin/bash
echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"
#Detecting OS type
INSTALLER=""
OS=$(awk '/NAME=/' /etc/*-release | sed -n '1 p' | cut -d= -f2 | cut -d\" -f2 | cut -d" " -f1)

if [ "$OS" = "Fedora" ]; then
    INSTALLER="yum"
elif [ "$OS" = "CentOS" ]; then
    INSTALLER="yum"
elif [ "$OS" = "Red" ]; then
    INSTALLER="yum"
else
    INSTALLER="apt"
fi

#Installing dependencies for Fedora/CentOS/RHEL
if [ "$INSTALLER" = "yum" ]; then
    yum clean expire-cache
    yum check-update
    sudo yum -q -y install curl make automake gcc gcc-c++ kernel-devel pkg-config bison flex autoconf libtool openssl-devel libpng libpng-devel freetype-devel libxml2 libxslt
    sudo yum -q -y install python2.7 python2-devel
    sudo yum -q -y install python2-wxpython
    if [ $? -ne 0 ]
    then
        echo "Manually installing python-wxgtk3.0..."
        sudo yum localinstall ./wxpython/python2-wxpython-3.0.2.0-26.fc31.x86_64.rpm
    fi
#Installing dependencies for Ubuntu/Mint/Debian
else
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
    #Fix for Debian Buster
    sudo apt-get -y -qq install libpng
    sudo apt-get -y -qq install libpng-dev libfreetype6-dev
fi

#Get pip manually
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2.7 get-pip.py

#Install Python dependencies
pip2 install future zeroconf==0.19.1 numpy==1.16.5 matplotlib==2.0.2 lxml==4.6.2 pyro sslpsk pyserial
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
