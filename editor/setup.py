"""
Install Beremiz
"""
from setuptools import setup

setup(
    name='beremiz',
    version='0.1', 
    install_requires=["Twisted == 20.3.0", "attrs == 19.2.0", "Automat == 0.3.0",
                      "zope.interface == 4.4.2", "Nevow == 0.14.5", "PyHamcrest == 2.0.2",
                      "Pygments == 2.9.0", "Pyro == 3.16", "constantly == 15.1.0",
                      "future == 0.18.2", "hyperlink == 21.0.0", "incremental == 21.3.0",
                      "pathlib == 1.0.1", "prompt-toolkit == 3.0.19", "zeroconf-py2compat == 0.19.10", 
                      "idna == 2.10"]
)
