# OpenPLC Editor
OpenPLC Editor - IDE capable of creating programs for the OpenPLC Runtime
This is a dev branch aiming to update the codebase to Python3 and wxPython Phoenix.
Runs on: windows, linux, macos

## Install

### Linux

#### before

Check there is python3.6 or later in your system package manager.

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
