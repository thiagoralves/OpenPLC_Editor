[![docs](https://readthedocs.org/projects/beremiz/badge/?version=latest)](https://beremiz.readthedocs.io)

# Beremiz #

Beremiz is an integrated development environment for machine automation. It is Free Software, conforming to IEC-61131 among other standards.

It relies on open standards to be independent of the targeted device, and let you turn any processor into a PLC. Beremiz includes tools to create HMI, and to connect your PLC programs to existing supervisions, databases, or fieldbuses.

With Beremiz, you conform to standards, avoid vendor lock, and contribute to the better future of Automation. 

Beremiz consists of two components:

* Integrated Development Environment (IDE), [Beremiz.py](https://bitbucket.org/automforge/beremiz/src/tip/Beremiz.py?at=default). It's running on user's computer and is used to write/compile/debug PLC programs and control PLC runtime.
* Reference runtime implementation in python, [Beremiz_service.py](https://bitbucket.org/automforge/beremiz/src/tip/Beremiz_service.py?at=default). It's running on target platform, communicates with I/O and executes PLC program.

See official [Beremiz website](http://www.beremiz.org/) for more information.

## Build on Linux ##

* Prerequisites

		# Ubuntu/Debian :
		sudo apt-get install build-essential bison flex autoconf
		sudo apt-get install python-wxgtk3.0 pyro mercurial
		sudo apt-get install python-nevow python-matplotlib python-lxml python-zeroconf python-cycler
		sudo apt-get install python-autobahn python-u-msgpack

		sudo apt-get install libpython2.7-dev
		pip2 install --user sslpsk posix_spawn

* Prepare

		mkdir ~/Beremiz
		cd ~/Beremiz

* Get Source Code

		cd ~/Beremiz
		hg clone https://bitbucket.org/automforge/beremiz
		hg clone https://bitbucket.org/automforge/matiec

* Build MatIEC compiler

		cd ~/Beremiz/matiec
		autoreconf -i
		./configure
		make

* Build CanFestival (optional)  
  Only needed for CANopen support. Please read CanFestival manual to choose CAN interface other than 'virtual'.

		cd ~/Beremiz
		hg clone http://dev.automforge.net/CanFestival-3
		cd ~/Beremiz/CanFestival-3
		./configure --can=virtual
		make

* Build Modbus library (optional)
  Only needed for Modbus support.

		cd ~/Beremiz
		hg clone https://bitbucket.org/mjsousa/modbus Modbus
		cd ~/Beremiz/Modbus
		make

* Build BACnet (optional)
  Only needed for BACnet support.

		cd ~/Beremiz
		svn checkout https://svn.code.sf.net/p/bacnet/code/trunk/bacnet-stack/ BACnet
		cd BACnet
		make MAKE_DEFINE='-fPIC' MY_BACNET_DEFINES='-DPRINT_ENABLED=1 -DBACAPP_ALL -DBACFILE -DINTRINSIC_REPORTING -DBACNET_TIME_MASTER -DBACNET_PROPERTY_LISTS=1 -DBACNET_PROTOCOL_REVISION=16' library


* Launch Beremiz IDE

		cd ~/Beremiz/beremiz
		python Beremiz.py

## Run standalone Beremiz runtime ##

Runtime implementation can be different on different platforms.
For example, PLC used Cortex-M most likely would have C-based runtime. Beremiz project contains reference implementation in python, that can be easily run on GNU/Linux, Windows and Mac OS X.
This section will describe how to run it.

If project's URL is 'LOCAL://', then IDE launches temprorary instance of Beremiz python runtime (Beremiz_service.py) localy as user tries to connect to PLC. This allows to debug programs localy without PLC.

If you want to run Beremiz_service.py as standalone service, then follow these instructions:

* Start standalone Beremiz service

		cd ~/Beremiz
		mkdir beremiz_workdir
		cd ~/beremiz
		python Beremiz_service.py -p 61194 -i localhost -x 0 -a 1 ~/Beremiz/beremiz_workdir

* Launch Beremiz IDE

		cd ~/Beremiz/beremiz
		python Beremiz.py

* Open/Create PLC project in Beremiz IDE.  
  Enter target location URI in project's settings (project->Config->BeremizRoot/URI_location) pointed to your running Beremiz service (For example, PYRO://127.0.0.1:61194).
  Save project and connect to running Beremiz service.

## Examples ##

Almost for all functionality exists example in ['tests'](https://bitbucket.org/automforge/beremiz/src/tip/tests/?at=default) directory.
Most of examples are shown on [Beremiz youtube channel](https://www.youtube.com/channel/UCcE4KYI0p1f6CmSwtzyg-ZA).

## Documentation ##

 * See [Beremiz youtube channel](https://www.youtube.com/channel/UCcE4KYI0p1f6CmSwtzyg-ZA) to get quick information how to use Beremiz IDE.
 
 * [Official user manual](http://beremiz.readthedocs.io/) is built from sources in doc directory.
   Documentation does not cover all aspects of Beremiz use yet.
   Contribution are very welcome!
   
 * [User manual](http://www.sm1820.ru/files/beremiz/beremiz_manual.pdf) from INEUM (Russian).
   Be aware that it contains some information about functions available only in INEUM's fork of Beremiz.

 * [User manual](http://www.beremiz.org/LpcManager_UserManual.pdf) from Smarteh (English).
   Be aware that it contains some information about functions available only in Smarteh's fork of Beremiz.

 * Outdated short [user manual](https://www.scribd.com/document/76101511/Manual-Beremiz#scribd) from LOLI Tech (English).

 * See official [Beremiz website](http://www.beremiz.org/) for more information.

## Support and development ##

Main community support channel is [mailing list](https://sourceforge.net/p/beremiz/mailman/beremiz-devel/) (beremiz-devel@lists.sourceforge.net).

The list is moderated and requires subscription for posting to it.

To subscribe to the mailing list go [here](https://sourceforge.net/p/beremiz/mailman/beremiz-devel/).

Searchable archive using search engine of your choice is available [here](http://beremiz-devel.2374573.n4.nabble.com/).