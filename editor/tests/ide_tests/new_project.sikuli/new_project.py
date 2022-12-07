""" This test opens, builds and runs a new project.
Test succeeds if runtime's stdout behaves as expected
"""

import os
import time

# allow module import from current test directory's parent
addImportPath(os.path.dirname(getBundlePath()))

# common test definitions module
from sikuliberemiz import *

def test(app):
    
    new_project_path = os.path.join(os.path.abspath(os.path.curdir), "new_test_project")
    
    # New project path must exist (usually created in directory selection dialog)
    os.mkdir(new_project_path)
    
    app.WaitIdleUI()
    
    # Create new project (opens new project directory selection dialog)
    app.k.New()
    
    app.WaitIdleUI()
    
    # Move to "Home" section of file selecor, otherwise address is 
    # "file ignored" at first run
    app.type("f", Key.CTRL)
    app.type(Key.ESC)
    app.type(Key.TAB)
    
    # Enter directory by name
    app.k.Address()
    
    # Fill address bar
    app.type(new_project_path + Key.ENTER)
    
    app.WaitIdleUI()
    
    # When prompted for creating first program select type ST
    app.type(Key.TAB*4)  # go to lang dropdown
    app.type(Key.DOWN*2) # change selected language
    app.type(Key.ENTER)  # validate
    
    app.WaitIdleUI()
    
    # Name created program
    app.type("Test program")
    
    app.WaitIdleUI()
    
    # Focus on Variable grid
    app.type(Key.TAB*4)
    
    # Add 2 variables
    app.type(Key.ADD*2)
    
    # Focus on ST text
    app.WaitIdleUI()
    
    app.type(Key.TAB*8)
    
    app.type("""\
    LocalVar0 := LocalVar1;
    {printf("Test OK\\n");fflush(stdout);}
    """)
    
    app.k.Save()
    
    # Close ST POU
    app.type("w", Key.CTRL)
    
    app.WaitIdleUI()
    
    # Focus project tree and select root item
    app.type(Key.TAB)
    
    app.type(Key.LEFT)
    
    app.type(Key.UP)
    
    # Edit root item
    app.type(Key.ENTER)
    
    app.WaitIdleUI()
    
    # Switch to config tab
    app.type(Key.RIGHT*2)
    
    # Focus on URI
    app.type(Key.TAB)
    
    # Set URI
    app.type("LOCAL://")
    
    # FIXME: Select other field to ensure URI is validated
    app.type(Key.TAB)
    
    app.k.Save()
    
    # Close project config editor
    app.type("w", Key.CTRL)
    
    app.WaitIdleUI()
    
    # Focus seems undefined at that time (FIXME)
    # Force focussing on "something" so that next shortcut is taken
    app.type(Key.TAB)
    
    app.waitIdleStdout()
    
    app.k.Build()
    
    app.waitIdleStdout(5,30)
    
    app.k.Connect()
    
    app.waitIdleStdout()
    
    app.k.Transfer()
    
    app.waitIdleStdout()
    
    app.k.Run()
    
    # wait 10 seconds
    return app.waitPatternInStdout("Test OK", 10)


run_test(test)
