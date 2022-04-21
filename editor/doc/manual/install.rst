Beremiz installation 
====================

Windows
-------
Download installer, install. 

Linux
-----
Pre-requisites::

    # Ubuntu/Debian :
    sudo apt-get install python-wxgtk2.8 pyro mercurial
    sudo apt-get install build-essential bison flex python-numpy python-nevow

Prepare::

    mkdir ~/Beremiz
    cd ~/Beremiz

Get Source Code::

    cd ~/Beremiz
    
    hg clone http://dev.automforge.net/beremiz
    hg clone http://dev.automforge.net/plcopeneditor
    hg clone http://dev.automforge.net/matiec

Build MatIEC compiler::

    cd ~/Beremiz/matiec
    ./configure
    make

Build CanFestival (optional):: 

    # Only needed for CANopen support. Please read CanFestival 
    # manual to choose CAN interface other than 'virtual'::

    cd ~/Beremiz
    hg clone http://dev.automforge.net/CanFestival-3
    
    cd ~/Beremiz/CanFestival-3
    ./configure --can=virtual
    make

Launch Beremiz::

    cd ~/Beremiz/beremiz
    python Beremiz.py

