#!/bin/bash

OPENPLC_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$OPENPLC_DIR/.venv"

echo ""

# Check for Gentoo
if ! command -v equery &> /dev/null; then
    echo "This script is intended for Gentoo Linux and relies there on 'app-portage/gentoolkit'."
    echo "Could not find the tool 'equery'. Exiting."
    exit 1
fi

# Function to check if a package is installed
check_package() {
    if ! equery -q list "$1"; then
        return 1
    fi
    return 0
}

# List of required system packages
system_packages=(
    "sys-devel/gcc" "dev-build/make" "dev-build/automake" "dev-build/autoconf"
    "sys-devel/bison" "sys-devel/flex" "dev-vcs/git" "x11-libs/gtk+:3"
    "dev-libs/libxml2" "dev-libs/libxslt" "dev-lang/python" "dev-python/pip"
    "dev-python/wheel" "dev-python/jinja" "dev-python/lxml" "dev-python/requests-futures"
    "dev-python/matplotlib" "dev-python/pyserial"
    "dev-python/Pyro5" "dev-python/wxpython:4.0"
)

echo "Checking dependencies for OpenPLC Editor installation on Gentoo"
echo ""
echo "Found packages:"
# Check for missing system packages
missing_packages=()
for package in "${system_packages[@]}"; do
    if ! check_package "$package"; then
        missing_packages+=("$package")
    fi
done

echo ""

# Report missing system packages
if [ ${#missing_packages[@]} -eq 0 ]; then
    echo "All required system packages are installed."
else
    echo "The following packages need to be installed:"
    printf '%s\n' "${missing_packages[@]}"
    echo ""
    echo "Please install these packages before continuing."
    echo "You can install the missing Gentoo packages using:"
    echo "  'emerge -av --noreplace ${missing_packages[@]}'"
    exit 1
fi

echo ""
echo "All system dependencies are satisfied. Proceeding with installation..."

echo "[SETTING UP VIRTUAL ENVIRONMENT]"
if ! python -m venv "$VENV_DIR" --system-site-packages; then
    echo "Failed to create virtual environment."
    exit 2
fi

if ! source "$VENV_DIR/bin/activate"; then
    echo "Failed to activate virtual environment."
    exit 3
fi

echo "[INSTALLING PYTHON DEPENDENCIES]"
# List of Python packages to be installed in VENV
venv_packages=("zeroconf" "attrdict3")

# Function to check if a Python package is installed
is_python_package_installed() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Install only the necessary packages
for package in "${venv_packages[@]}"; do
    package_name=$(echo "$package" | cut -d= -f1)
    if ! is_python_package_installed "$package_name"; then
        if ! pip install "$package"; then
            echo "Failed to install $package"
            exit 4
        fi
    else
        echo "$package_name is already installed, skipping."
    fi
done

echo "[COMPILING MATIEC]"
cd "$OPENPLC_DIR/matiec" || exit 5
if ! autoreconf -i; then
    echo "Failed to run autoreconf."
    exit 6
fi

if ! ./configure; then
    echo "Failed to run configure script."
    exit 7
fi

if ! make -j $(nproc) -s; then
    echo "Failed to compile MATIEC."
    exit 8
fi

if ! cp ./iec2c ../editor/arduino/bin/; then
    echo "Failed to copy iec2c to the destination directory."
    exit 9
fi

cd "$OPENPLC_DIR" || exit 10

echo ""
echo "[FINALIZING]"

# Create launcher script
if ! echo -e "#!/bin/bash\n\
cd \"$OPENPLC_DIR\"\n\
source \"$VENV_DIR/bin/activate\"\n\
python ./editor/Beremiz.py" > openplc_editor.sh; then
    echo "Failed to create launcher script."
    exit 11
fi

if ! chmod +x ./openplc_editor.sh; then
    echo "Failed to make launcher script executable."
    exit 12
fi

# Create desktop entry
if ! mkdir -p ~/.local/share/applications; then
    echo "Failed to create applications directory."
    exit 13
fi

if ! cat > ~/.local/share/applications/OpenPLC_Editor.desktop << EOF
[Desktop Entry]
Name=OpenPLC Editor
Categories=Development;
Exec="$OPENPLC_DIR/openplc_editor.sh"
Icon=$OPENPLC_DIR/editor/images/brz.png
Type=Application
Terminal=false
EOF
then
    echo "Failed to create desktop entry."
    exit 14
fi

echo "Installation completed successfully!"
echo "You can now run OpenPLC Editor using the desktop shortcut or by executing '$OPENPLC_DIR/openplc_editor.sh'"
