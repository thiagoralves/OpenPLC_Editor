#!/bin/bash

OPENPLC_DIR="$PWD"
VENV_DIR="$OPENPLC_DIR/.venv"

echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"


if [ -x /bin/yum ]; then
    yum clean expire-cache
    yum check-update
    sudo yum -q -y install make automake gcc gcc-c++ bison flex autoconf git python3.8 python3-devel libxml2-devel libxslt-devel gtk3-devel
#Installing dependencies for Ubuntu/Mint/Debian
elif [ -x /usr/bin/apt-get ]; then
    sudo apt-get -qq update
    sudo apt-get install -y build-essential bison flex autoconf \
                          automake make git libgtk-3-dev\
                          python3.8 python3-venv
#Installing dependencies for opensuse tumbleweed
elif [ -x /usr/bin/zypper ]; then
    sudo zypper ref
    sudo zypper in -y make automake gcc gcc-c++ bison flex autoconf
    sudo zypper in -y python python-xml python3.8 python3-pip
else
    echo "Unsupported linux distro."
    exit 1
fi

#Installing Python dependencies
python3.8 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install wheel jinja2 lxml==4.6.2 future matplotlib zeroconf pyserial pypubsub pyro5 attrdict3
"$VENV_DIR/bin/python" -m pip install wxPython==4.2.1 


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
./.venv/bin/python3 ./editor/Beremiz.py" > openplc_editor.sh
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
