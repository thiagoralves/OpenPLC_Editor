#!/bin/bash

OPENPLC_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$OPENPLC_DIR/.venv"

cd "$OPENPLC_DIR"
git submodule update --init --recursive "$OPENPLC_DIR"

echo "Installing OpenPLC Editor"
echo "Please be patient. This may take a couple minutes..."
echo ""
echo "[INSTALLING DEPENDENCIES]"


if [ -x /bin/yum ]; then
    yum clean expire-cache
    yum check-update
    sudo yum -q -y install make automake gcc gcc-c++ bison flex autoconf git python3.9 python3-devel libxml2-devel libxslt-devel gtk3-devel
#Installing dependencies for Ubuntu/Mint/Debian
elif [ -x /usr/bin/apt-get ]; then
    sudo apt-get -qq update
    #Add deadsnakes PPA for Python3.9 support on newer distros
    sudo apt-get install software-properties-common -y
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get -qq update
    sudo apt-get install -y build-essential bison flex autoconf \
                          automake make git libgtk-3-dev\
                          python3.9 python3.9-venv python3.9-dev
#Installing dependencies for opensuse tumbleweed
elif [ -x /usr/bin/zypper ]; then
    sudo zypper ref
    sudo zypper in -y make automake gcc gcc-c++ bison flex autoconf
    sudo zypper in -y python python-xml python3.9 python3-pip
# some linux distros also use pkg, so check against the uname
elif [ -x /usr/sbin/pkg ] && [ $(uname) == "FreeBSD" ]; then
    sudo pkg install -y python autoconf-2.72 automake bison \
        py39-Jinja2 py39-lxml py39-matplotlib py39-future \
        py39-pyserial py39-wxPython42 py39-wheel
#Installing dependencies for Arch Linux
elif [ -x /usr/bin/pacman ]; then
    sudo pacman -Syu --noconfirm
    sudo pacman -S --noconfirm --needed base-devel gtk3 python-pip \
        autoconf automake bison flex git

    # Check if an AUR helper is available
    if command -v yay >/dev/null 2>&1; then
        AUR_HELPER="yay"
    elif command -v paru >/dev/null 2>&1; then
        AUR_HELPER="paru"
    else
        echo "Installing yay AUR helper..."
        cd /tmp
        git clone https://aur.archlinux.org/yay.git
        cd yay
        makepkg -si --noconfirm
        cd "$OPENPLC_DIR"
        AUR_HELPER="yay"
    fi
    # Installing python3.9 from AUR using the detected/installed AUR helper
    $AUR_HELPER -S --noconfirm python39
else
    echo "Unsupported linux distro."
    exit 1
fi

#Installing Python dependencies
if [ $(uname) == "FreeBSD" ]; then
    # use system packages on FreeBSD
    python3.9 -m venv --system-site-packages "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install zeroconf pypubsub pyro5 attrdict3
else
    python3.9 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install wheel jinja2 lxml==4.6.2 future matplotlib zeroconf pyserial pypubsub pyro5 attrdict3
    "$VENV_DIR/bin/python" -m pip install wxPython==4.2.0
fi


echo ""
echo "[COMPILING MATIEC]"
cd "$OPENPLC_DIR/matiec"
autoreconf -i

# clang treats this as an error while gcc treats it as a warning
if [ $(uname) == "FreeBSD" ]; then
    CXXFLAGS="-Wno-error=reserved-user-defined-literal" ./configure
else
    ./configure
fi

make -s
cp ./iec2c ../editor/arduino/bin/
echo ""
echo "[FINALIZING]"
cd "$OPENPLC_DIR"

echo -e "#!/bin/bash\n\
cd \"$OPENPLC_DIR\"\n\
if [ -d \"./new_editor\" ]\n\
then\n\
    rm -Rf editor\n\
    rm -Rf ./matiec/lib\n\
    mv ./new_editor ./editor\n\
    mv ./new_lib ./matiec/lib\n\
fi\n\
source \"$VENV_DIR/bin/activate\"\n\
export GDK_BACKEND=x11\n\
./.venv/bin/python3 ./editor/Beremiz.py" > openplc_editor.sh
chmod +x ./openplc_editor.sh

mkdir -p ~/.local/share/applications
cd ~/.local/share/applications || exit
echo -e "[Desktop Entry]\n\
Name=OpenPLC Editor\n\
Categories=Development;\n\
Exec=\"$OPENPLC_DIR/openplc_editor.sh\"\n\
Icon=$OPENPLC_DIR/editor/images/brz.png\n\
Type=Application\n\
Terminal=false" > OpenPLC_Editor.desktop
