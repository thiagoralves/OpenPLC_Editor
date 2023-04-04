# OpenPLC Editor
OpenPLC Editor - IDE capable of creating programs for the OpenPLC Runtime
This is a dev branch aiming to update the codebase to Python3 and wxPython Phoenix.
Runs on: windows, linux, macos

## Install

### Linux

#### before

Check there is python3.6 (with pip) or later in your system package manager.
Install wxPython 4.1.1. This can be tricky on some systems. For Ubuntu:

```
pip3 install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/ wxPython==4.1.1
sudo apt install libsdl2-2.0-0


You can change the https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/ URL if you're not on Ubuntu 20.04. There are other pre-built wxPython packages for other Linux distros. Check https://extras.wxpython.org/wxPython4/extras/linux/gtk3

#### start

cd to the root of the project and then

```
./install.sh
```

### windows

 - Python 3.6 or later (follow your system's preferred install method)
 - Pip (for python 3)

All other dependencies can be installed with Pip:

```powershell
pip3 install lxml matplotlib zeroconf pyserial gnosis simplejson nevow
```

### tips

If there are some package failed to install, try to skip them manually.

## To Run:

### linux

```bash
./openplc_editor.sh
```

or

Find "OpenPLC Editor" on your applications menu and launch it

### windows

cd to the root of the project and then

```powershell
python editor/Beremiz.py
```
