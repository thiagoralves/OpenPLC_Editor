<!---
[![docs](https://readthedocs.org/projects/beremiz/badge/?version=latest)](https://beremiz.readthedocs.io)
-->

# Beremiz #

Beremiz is an integrated development environment for machine automation. It is Free Software, conforming to IEC-61131 among other standards.

It relies on open standards to be independent of the targeted device, and let you turn any processor into a PLC. Beremiz includes tools to create HMI, and to connect your PLC programs to existing supervisions, databases, or fieldbuses.

With Beremiz, you conform to standards, avoid vendor lock, and contribute to the better future of Automation. 

Beremiz consists of two components:

* Integrated Development Environment (IDE), Beremiz.py. It is running on user's computer and is used to write/compile/debug PLC programs and control PLC runtime.
* Reference runtime implementation in python, Beremiz_service.py. It's running on target platform, communicates with I/O and executes PLC program.

See official [Beremiz website](http://www.beremiz.org/) for more information.

## Install latest release ##

Windows installer and Snap package for Linux are available in [Github releases](https://github.com/beremiz/beremiz/releases) and [Snapcraft's store](https://snapcraft.io/beremiz)

## Tutorials and examples ##

In IDE, find menu "File>Tutorials and examples" to quickly open examples that should run as-is.

There are more examples in `tests/projects` and `exemples` directories.

Some example and test are shown on [Beremiz youtube channel](https://www.youtube.com/channel/UCcE4KYI0p1f6CmSwtzyg-ZA).

## Development with Beremiz ##

Developers are invited to subscribe to [mailing list](https://sourceforge.net/p/beremiz/mailman/beremiz-devel/) (beremiz-devel@lists.sourceforge.net).

The list is moderated and requires subscription before posting.

To subscribe to the mailing list go [here](https://sourceforge.net/p/beremiz/mailman/beremiz-devel/).

Searchable archive using search engine of your choice is available [here](http://beremiz-devel.2374573.n4.nabble.com/).

## Build on Linux (developer setup) ##

### Prerequisites (Ubuntu/Debian) :
```
sudo apt-get install build-essential bison flex autoconf
sudo apt-get install python2-dev libpython2.7-dev libgtk-3-dev libssl-dev libgl1-mesa-dev libglu1-mesa-dev python-setuptools

python2 -m pip install  \
    future              \
    matplotlib          \
    msgpack_python      \
    u-msgpack-python    \
    zeroconf2           \
    enum34              \
    pyro                \
    sslpsk              \
    posix_spawn         \
    twisted             \
    nevow               \
    autobahn            \
    click               \
    opcua               \
    pycountry           \
    fonttools           \
    Brotli              \
    lxml==4.5.0         \
    wxPython==4.1.1

```

### Prepare build directory

All commands hereafter assume that selected directory to contain all downloaded source code and build results is `~/Beremiz`

```
mkdir ~/Beremiz
cd ~/Beremiz
```

### Get Source Code (Mercurial)

```
cd ~/Beremiz
hg clone https://hg.beremiz.org/beremiz
hg clone https://hg.beremiz.org/matiec
```

### Get Source Code (Git)

```
cd ~/Beremiz
git clone https://github.com/beremiz/beremiz
git clone https://github.com/beremiz/matiec
```

### Build MatIEC compiler

```
cd ~/Beremiz/matiec
autoreconf -i
./configure
make
```

### Build CanFestival (optional)

Only needed for CANopen support. Please read CanFestival manual to choose CAN interface other than `virtual`.

```
cd ~/Beremiz
hg clone http://hg.beremiz.org/CanFestival-3
cd ~/Beremiz/CanFestival-3
./configure --can=virtual
make
```

### Build Modbus library (optional)

Only needed for Modbus support.

```
cd ~/Beremiz
hg clone https://hg.beremiz.org/Modbus
cd ~/Beremiz/Modbus
make
```

### Build BACnet (optional)

Only needed for BACnet support.

```
cd ~/Beremiz
svn checkout https://svn.code.sf.net/p/bacnet/code/trunk/bacnet-stack/ BACnet
cd BACnet
make MAKE_DEFINE='-fPIC' MY_BACNET_DEFINES='-DPRINT_ENABLED=1 -DBACAPP_ALL -DBACFILE -DINTRINSIC_REPORTING -DBACNET_TIME_MASTER -DBACNET_PROPERTY_LISTS=1 -DBACNET_PROTOCOL_REVISION=16' library
```

### Launch Beremiz IDE

```
cd ~/Beremiz/beremiz
python Beremiz.py
```

## Run standalone Beremiz runtime ##

* Start standalone Beremiz service

```
mkdir ~/beremiz_runtime_workdir
python Beremiz_service.py -p 61194 -i localhost -x 0 -a 1 ~/beremiz_runtime_workdir
```

To connect IDE with runtime, enter target location URI in project's settings (project->Config->BeremizRoot/URI_location) pointed to your running Beremiz service in this case :

```
PYRO://127.0.0.1:61194
```

If project's URL is 'LOCAL://', then IDE launches on demand a local instance of Beremiz python runtime working on a temporary directory.

## Build documentation

Source code for documentation is stored in `doc` directory in project's source tree.
It's written in reStructuredText (ReST) and uses Sphinx to generate documentation in different formats.

To build documentation you need following packages on Ubuntu/Debian:

```
sudo apt-get install build-essential python-sphynx
```

### Documentation in HTML

Build documentation

```
cd ~/Beremiz/doc
make all
```

Result documentation is stored in directories `doc/_build/dirhtml*`.

### Documentation in PDF

To build pdf documentation you have to install additional packages on Ubuntu/Debian:

```
sudo apt-get install textlive-latex-base texlive-latex-recommended \
     texlive-fonts-recommended texlive-latex-extra
```

Build documentation

```
cd ~/Beremiz/doc
make latexpdf
```

Result documentation is stored in `doc/_build/latex/Beremiz.pdf`.

## Documentation ##

 * See [Beremiz youtube channel](https://www.youtube.com/channel/UCcE4KYI0p1f6CmSwtzyg-ZA) to get quick information how to use Beremiz IDE.

 * [Official documentation](http://beremiz.readthedocs.io/) is built from sources in doc directory.
   Documentation does not cover all aspects of Beremiz use yet.
   Contribution are very welcome!
   
 * [User manual](http://www.sm1820.ru/files/beremiz/beremiz_manual.pdf) from INEUM (Russian).
   Be aware that it contains some information about functions available only in INEUM's fork of Beremiz.

 * [User manual](http://www.beremiz.org/LpcManager_UserManual.pdf) from Smarteh (English).
   Be aware that it contains some information about functions available only in Smarteh's fork of Beremiz.

 * Outdated short [user manual](https://www.scribd.com/document/76101511/Manual-Beremiz#scribd) from LOLI Tech (English).

 * See official [Beremiz website](http://www.beremiz.org/) for more information.

