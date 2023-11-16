""" This test opens, builds and runs exemple project named "python".
Test succeeds if runtime's stdout behaves as expected
"""

import os
import time

# allow module import from current test directory's parent
addImportPath(os.path.dirname(getBundlePath()))

# common test definitions module
from sikuliberemiz import *

def test(app):
    # Start the app
    
    app.k.Clean()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Build()
    
    app.waitPatternInStdout("Successfully built.", 10)
    
    app.k.Connect()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Transfer()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Run()

    app.waitForChangeAndIdleStdout()
    # app.WaitIdleUI()

    app.ocropts.fontSize(20)
    #app.ocropts.textHeight(25)
    app.click("OFF")

    # wait 10 seconds for 10 Grumpfs
    return app.waitPatternInStdout("ALL GREEN LIGHTS", 10)
    
run_test(test, testproject="svghmi_basic")
