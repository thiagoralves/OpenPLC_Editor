import os
import sys
cmd = sys.executable + " -m pip install -r "+os.path.dirname(os.path.realpath(__file__))+"\\requirements.txt"
os.system(cmd)
