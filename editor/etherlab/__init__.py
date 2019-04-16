from __future__ import absolute_import

from etherlab.etherlab import *
from util.BitmapLibrary import AddBitmapFolder
import util.paths as paths

AddBitmapFolder(os.path.join(paths.AbsDir(__file__), "images"))
