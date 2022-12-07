""" This test opens, modifies, builds and runs exemple project named "python".
Test succeeds if runtime's stdout behaves as expected
"""

import os
import time

# allow module import from current test directory's parent
addImportPath(os.path.dirname(getBundlePath()))

# common test definitions module
from sikuliberemiz import run_test

def test(app):

    app.k.Clean()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Build()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Connect()
    
    app.waitForChangeAndIdleStdout()
    
    app.k.Transfer()
    
    app.waitForChangeAndIdleStdout()
    
    app.click("1646062660770.png")

    app.WaitIdleUI()
    
    app.click("1646066996789.png")

    app.WaitIdleUI()

    app.click("example")

    app.WaitIdleUI()

    app.type(Key.DOWN * 10, Key.CTRL)

    app.WaitIdleUI()

    app.k.Run()

    # wait up to 10 seconds for 10 Grumpfs
    app.waitPatternInStdout("Grumpf", 10, 10)

    app.rightClick("1646066996790.png")

    # app.click("Force value")

    app.type(Key.DOWN)

    app.type(Key.ENTER)

    # app.click("1646062660790.png")

    # app.type("a", Key.CTRL)

    # app.type(Key.BACKSPACE)
    app.type(Key.HOME)

    app.type("a", Key.CTRL)

    app.type(Key.DELETE)

    app.type("'sys.stdout.write(\"DEBUG TEST OK\\n\")'")

    app.type(Key.ENTER)
    
    # wait 10 seconds for 10 patterns
    return app.waitPatternInStdout("DEBUG TEST OK", 10)

run_test(test, exemple="python")
