import json
import os
import platform as os_platform
import shutil
import subprocess
import sys
import time

import threading

import wx

global compiler_logs
compiler_logs = ''


def scrollToEnd(txtCtrl):
    if os_platform.system() != 'Darwin':
        txtCtrl.SetInsertionPoint(-1)
    txtCtrl.ShowPosition(txtCtrl.GetLastPosition())
    txtCtrl.Refresh()
    txtCtrl.Update()


def runCommand(command):
    cmd_response = None

    try:
        cmd_response = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        #cmd_response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as exc:
        cmd_response = exc.output

    if cmd_response is None:
        return ''

    return cmd_response.decode('utf-8')

def loadHals():
    # load hals list from json file, or construct it
    if (os.name == 'nt'):
        jfile = 'editor\\arduino\\examples\\Baremetal\\hals.json'
    else:
        jfile = 'editor/arduino/examples/Baremetal/hals.json'
    
    f = open(jfile, 'r')
    jsonStr = f.read()
    f.close()
    return(json.loads(jsonStr))

def saveHals(halObj):
    jsonStr = json.dumps(halObj)
    if (os.name == 'nt'):
        jfile = 'editor\\arduino\\examples\\Baremetal\\hals.json'
    else:
        jfile = 'editor/arduino/examples/Baremetal/hals.json'
    f = open(jfile, 'w')
    f.write(jsonStr)
    f.flush()
    f.close()
    
def readBoardInstalled(platform):
    hals = loadHals()
    cli_command = ''
    if os_platform.system() == 'Windows':
        cli_command = 'editor\\arduino\\bin\\arduino-cli-w32'
    elif os_platform.system() == 'Darwin':
        cli_command = 'editor/arduino/bin/arduino-cli-mac'
    else:
        cli_command = 'editor/arduino/bin/arduino-cli-l64'
    for board in hals:
            if hals[board]['platform'] == platform:
                board_details = runCommand(cli_command + ' board details -b ' + platform)
                board_details = board_details.splitlines()
                board_version = '0'
                for line in board_details:
                    if "Board version:" in line:
                        board_version = line.split('Board version:')[1]
                        board_version = ''.join(board_version.split()) #remove white spaces
                        hals[board]['version'] = board_version
                        saveHals(hals)
                        break

def loadHalsAsync():
    global hals
    hals = loadHals()

def readBoardsInstalledAsync():
    global boardInstalled
    # this as to be done asynchrounously
    cli_command = ''
    if os_platform.system() == 'Windows':
        cli_command = 'editor\\arduino\\bin\\arduino-cli-w32'
    elif os_platform.system() == 'Darwin':
        cli_command = 'editor/arduino/bin/arduino-cli-mac'
    else:
        cli_command = 'editor/arduino/bin/arduino-cli-l64'
    
    boardInstalled = runCommand(cli_command + ' board listall')


# Define a function to run the command in a thread
def run_command_thread(board, cli_command):
    global hals, hasToSave  
    if board in boardInstalled:
        platform = hals[board]['platform']
        start = time.time()
        board_details = runCommand(cli_command + ' board details -b ' + platform)
        print("2 "+str(time.time()-start))

        for line in board_details.splitlines():
            if "Board version:" in line:
                board_version = line.split('Board version:')[1].replace(" ", "")
                if hals[board]['version'] != board_version:
                    hals[board]['version'] = board_version
                    hasToSave = True

                break
    elif hals[board]['version'] != '0':
        hals[board]['version'] = '0'
        hasToSave = True

def readBoardsInstalled():
    global hasToSave 
    hasToSave = False
    start = time.time()
    threadLoadHals = threading.Thread(target=loadHalsAsync)
    threadBoardInstalled = threading.Thread(target=readBoardsInstalledAsync)
    # Start the threads
    threadLoadHals.start()
    threadBoardInstalled.start()

    
    cli_command = ''
    if os_platform.system() == 'Windows':
        cli_command = 'editor\\arduino\\bin\\arduino-cli-w32'
    elif os_platform.system() == 'Darwin':
        cli_command = 'editor/arduino/bin/arduino-cli-mac'
    else:
        cli_command = 'editor/arduino/bin/arduino-cli-l64'
    
    threads = []

    # Wait for the threads to finish
    threadLoadHals.join()
    print("1 "+str(time.time()-start))
    
    threadBoardInstalled.join()
    print("3 "+str(time.time()-start))

    # Create a new thread for each board
    
    for board in hals:
        t = threading.Thread(target=run_command_thread, args=(board, cli_command))
        threads.append(t)
        t.start()


    # Wait for all threads to finish
    for t in threads:
        t.join()
    
    if hasToSave:
        saveHals(hals)

def setLangArduino():
    cli_command = ''
    if os_platform.system() == 'Windows':
        cli_command = 'editor\\arduino\\bin\\arduino-cli-w32'
    elif os_platform.system() == 'Darwin':
        cli_command = 'editor/arduino/bin/arduino-cli-mac'
    else:
        cli_command = 'editor/arduino/bin/arduino-cli-l64'

    dump = runCommand(cli_command + ' config dump')
    dump = dump.splitlines()
    arduino_dir = ''
    for line in dump:
        if "data:" in line:
            #get the directory of arduino ide
            arduino_dir = line.split('data:')[1]
            arduino_dir = ''.join(arduino_dir.split()) #remove white spaces
            

        if "locale:" in line:
            if "en" not in line:
                #remove the line from dump variable
                dump.remove(line)
            else:
                return #already set to english
                
    dump.append('locale: en')
    dump = '\n'.join(dump)
    #write on the config file all the lines# Open the file in write mode
    with open(arduino_dir + '/arduino-cli.yaml', 'w') as f:
        # Write the variable to the file
        f.write(str(dump))

    #runCommand('echo ' + dump + ' > ' + arduino_dir + '/arduino-cli.yaml')


def build(st_file, platform, source_file, port, txtCtrl, update_subsystem):
    global compiler_logs
    compiler_logs = ''   
    setLangArduino()
 
    #check if platform is installed in the arduino ide
    readBoardInstalled(platform)

    hals = loadHals()
    
    
    

    #Check if board is installed
    board_installed = False
    core = ''
    for board in hals:
        if hals[board]['platform'] == platform:
            core = hals[board]['core']
            if hals[board]['version'] != "0":
                board_installed = True
    
    #Check MatIEC compiler
    if (os.path.exists("editor/arduino/bin/iec2c") or os.path.exists("editor/arduino/bin/iec2c.exe") or os.path.exists("editor/arduino/bin/iec2c_mac")):
        # remove old files first
        if os.path.exists('editor/arduino/src/POUS.c'):
            os.remove('editor/arduino/src/POUS.c')
        if os.path.exists('editor/arduino/src/POUS.h'):
            os.remove('editor/arduino/src/POUS.h')
        if os.path.exists('editor/arduino/src/LOCATED_VARIABLES.h'):
            os.remove('editor/arduino/src/LOCATED_VARIABLES.h')
        if os.path.exists('editor/arduino/src/VARIABLES.csv'):
            os.remove('editor/arduino/src/VARIABLES.csv')
        if os.path.exists('editor/arduino/src/Config0.c'):
            os.remove('editor/arduino/src/Config0.c')
        if os.path.exists('editor/arduino/src/Config0.h'):
            os.remove('editor/arduino/src/Config0.h')
        if os.path.exists('editor/arduino/src/Res0.c'):
            os.remove('editor/arduino/src/Res0.c')
    else:
        compiler_logs += "Error: iec2c compiler not found!\n"
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)
        return

    #Install/Update board support
    if board_installed == False or update_subsystem == True:
        if board_installed == False:
            compiler_logs += "Support for " + platform + " is not installed on OpenPLC Editor. Please be patient and wait while " + platform + " is being installed...\n"
            wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        elif update_subsystem == True:
            compiler_logs += "Updating support for " + platform + ". Please be patient and wait while " + platform + " is being installed...\n"
            wx.CallAfter(txtCtrl.SetValue, compiler_logs)

        cli_command = ''
        if os_platform.system() == 'Windows':
            cli_command = 'editor\\arduino\\bin\\arduino-cli-w32'
        elif os_platform.system() == 'Darwin':
            cli_command = 'editor/arduino/bin/arduino-cli-mac'
        else:
            cli_command = 'editor/arduino/bin/arduino-cli-l64'

        """
        ### ARDUINO-CLI CHEAT SHEET ###

        1. List installed boards:
          => arduino-cli board listall
        
        2. Search for a core (even if not installed yet):
          => arduino-cli core search [search text]
        
        3. Dump current configuration:
          => arduino-cli config dump

        4. Get additional board parameters:
          => arduino-cli board details -fqbn [board fqbn]
        """

        # Initialize arduino-cli config - if it hasn't been initialized yet
        compiler_logs += runCommand(cli_command + ' config init')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)

        # Setup boards - remove 3rd party boards to re-add them later since we don't know if they're there or not
        compiler_logs += runCommand(
            cli_command + ' config remove board_manager.additional_urls \
https://arduino.esp8266.com/stable/package_esp8266com_index.json \
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json \
https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json \
https://raw.githubusercontent.com/CONTROLLINO-PLC/CONTROLLINO_Library/master/Boards/package_ControllinoHardware_index.json \
https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json \
https://facts-engineering.gitlab.io/facts-open-source/p1am/beta_file_hosting/package_productivity-P1AM_200-boardmanagermodule_index.json \
https://raw.githubusercontent.com/VEA-SRL/IRUINO_Library/main/package_vea_index.json \
"2>&1"')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)

        # Setup boards - add 3rd party boards
        compiler_logs += runCommand(
            cli_command + ' config add board_manager.additional_urls \
https://arduino.esp8266.com/stable/package_esp8266com_index.json \
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json \
https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json \
https://raw.githubusercontent.com/CONTROLLINO-PLC/CONTROLLINO_Library/master/Boards/package_ControllinoHardware_index.json \
https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json \
https://facts-engineering.gitlab.io/facts-open-source/p1am/beta_file_hosting/package_productivity-P1AM_200-boardmanagermodule_index.json \
https://raw.githubusercontent.com/VEA-SRL/IRUINO_Library/main/package_vea_index.json')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)

        # Update
        compiler_logs += runCommand(cli_command + ' core update-index')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)
        compiler_logs += runCommand(cli_command + ' update')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)

        # Install board
        compiler_logs += runCommand(cli_command + ' core install ' + core)
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)
        
        # Install all libs - required after core install/update
        compiler_logs += runCommand(cli_command + ' lib install \
WiFiNINA \
Ethernet \
Arduino_MachineControl \
Arduino_EdgeControl \
OneWire \
DallasTemperature \
P1AM \
CONTROLLINO \
"Adafruit ADS1X15" \
PubSubClient \
ArduinoJson \
arduinomqttclient \
RP2040_PWM')
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)

        readBoardsInstalled()

    # Generate C files
    compiler_logs += "Compiling .st file...\n"
    wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    wx.CallAfter(scrollToEnd, txtCtrl)
    if (os.name == 'nt'):
        base_path = 'editor\\arduino\\src\\'
    else:
        base_path = 'editor/arduino/src/'
    f = open(base_path+'plc_prog.st', 'w')
    f.write(st_file)
    f.flush()
    f.close()

    time.sleep(0.2)  # make sure plc_prog.st was written to disk

    if os_platform.system() == 'Windows':
        compilation = subprocess.Popen(['editor\\arduino\\bin\\iec2c.exe', 'plc_prog.st'], cwd='editor\\arduino\\src',
                                       creationflags=0x08000000, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif os_platform.system() == 'Darwin':
        compilation = subprocess.Popen(['../bin/iec2c_mac', 'plc_prog.st'],
                                       cwd='./editor/arduino/src', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        compilation = subprocess.Popen(
            ['../bin/iec2c', 'plc_prog.st'], cwd='./editor/arduino/src', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = compilation.communicate()
    compiler_logs += stdout.decode('UTF-8')
    compiler_logs += stderr.decode('UTF-8')
    wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    wx.CallAfter(scrollToEnd, txtCtrl)

    # Remove temporary plc program
    # if os.path.exists(base_path+'plc_prog.st'):
    #    os.remove(base_path+'plc_prog.st')

    # Generate glueVars.c
    if not (os.path.exists(base_path+'LOCATED_VARIABLES.h')):
        compiler_logs += "Error: Couldn't find LOCATED_VARIABLES.h. Check iec2c compiler output for more information\n"
        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
        wx.CallAfter(scrollToEnd, txtCtrl)
        return

    located_vars_file = open(base_path+'LOCATED_VARIABLES.h', 'r')
    located_vars = located_vars_file.readlines()
    glueVars = """
#include "iec_std_lib.h"

#define __LOCATED_VAR(type, name, ...) type __##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR
#define __LOCATED_VAR(type, name, ...) type* name = &__##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR

TIME __CURRENT_TIME;
BOOL __DEBUG;
extern unsigned long long common_ticktime__;

//OpenPLC Buffers
#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__) || defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega16U4__)

#define MAX_DIGITAL_INPUT          8
#define MAX_DIGITAL_OUTPUT         32
#define MAX_ANALOG_INPUT           6
#define MAX_ANALOG_OUTPUT          32

#else

#define MAX_DIGITAL_INPUT          56
#define MAX_DIGITAL_OUTPUT         56
#define MAX_ANALOG_INPUT           32
#define MAX_ANALOG_OUTPUT          32

#endif

IEC_BOOL *bool_input[MAX_DIGITAL_INPUT/8][8];
IEC_BOOL *bool_output[MAX_DIGITAL_OUTPUT/8][8];
IEC_UINT *int_input[MAX_ANALOG_INPUT];
IEC_UINT *int_output[MAX_ANALOG_OUTPUT];

void glueVars()
{
"""
    for located_var in located_vars:
        # cleanup located var line
        if ('__LOCATED_VAR(' in located_var):
            located_var = located_var.split('(')[1].split(')')[0]
            var_data = located_var.split(',')
            if (len(var_data) < 5):
                compiler_logs += 'Error processing located var line: ' + located_var + '\n'
                wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                wx.CallAfter(scrollToEnd, txtCtrl)
            else:
                var_type = var_data[0]
                var_name = var_data[1]
                var_address = var_data[4]
                var_subaddress = '0'
                if (len(var_data) > 5):
                    var_subaddress = var_data[5]

                # check variable type and assign to correct buffer pointer
                if ('QX' in var_name):
                    if (int(var_address) > 6 or int(var_subaddress) > 7):
                        compiler_logs += 'Error: wrong location for var ' + var_name + '\n'
                        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                        wx.CallAfter(scrollToEnd, txtCtrl)
                        return
                    glueVars += '    bool_output[' + var_address + \
                        '][' + var_subaddress + '] = ' + var_name + ';\n'
                elif ('IX' in var_name):
                    if (int(var_address) > 6 or int(var_subaddress) > 7):
                        compiler_logs += 'Error: wrong location for var ' + var_name + '\n'
                        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                        wx.CallAfter(scrollToEnd, txtCtrl)
                        return
                    glueVars += '    bool_input[' + var_address + \
                        '][' + var_subaddress + '] = ' + var_name + ';\n'
                elif ('QW' in var_name):
                    if (int(var_address) > 32):
                        compiler_logs += 'Error: wrong location for var ' + var_name + '\n'
                        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                        wx.CallAfter(scrollToEnd, txtCtrl)
                        return
                    glueVars += '    int_output[' + \
                        var_address + '] = ' + var_name + ';\n'
                elif ('IW' in var_name):
                    if (int(var_address) > 32):
                        compiler_logs += 'Error: wrong location for var ' + var_name + '\n'
                        wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                        wx.CallAfter(scrollToEnd, txtCtrl)
                        return
                    glueVars += '    int_input[' + \
                        var_address + '] = ' + var_name + ';\n'
                else:
                    compiler_logs += 'Could not process location "' + \
                        var_name + '" from line: ' + located_var + '\n'
                    wx.CallAfter(txtCtrl.SetValue, compiler_logs)
                    wx.CallAfter(scrollToEnd, txtCtrl)
                    return

    glueVars += """
}

void updateTime()
{
    __CURRENT_TIME.tv_nsec += common_ticktime__;

    if (__CURRENT_TIME.tv_nsec >= 1000000000)
    {
        __CURRENT_TIME.tv_nsec -= 1000000000;
        __CURRENT_TIME.tv_sec += 1;
    }
}
    """
    f = open(base_path+'glueVars.c', 'w')
    f.write(glueVars)
    f.flush()
    f.close()

    time.sleep(2)  # make sure glueVars.c was written to disk

    # Patch POUS.c to include POUS.h
    f = open(base_path+'POUS.c', 'r')
    pous_c = '#include "POUS.h"\n\n' + f.read()
    f.close()

    f = open(base_path+'POUS.c', 'w')
    f.write(pous_c)
    f.flush()
    f.close()

    # Patch Res0.c to include POUS.h instead of POUS.c
    f = open(base_path+'Res0.c', 'r')
    res0_c = ''
    lines = f.readlines()
    for line in lines:
        if '#include "POUS.c"' in line:
            res0_c += '#include "POUS.h"\n'
        else:
            res0_c += line
    f.close()

    f = open(base_path+'Res0.c', 'w')
    f.write(res0_c)
    f.flush()
    f.close()

    # Copy HAL file
    if os_platform.system() == 'Windows':
        source_path = 'editor\\arduino\\src\\hal\\'
        destination = 'editor\\arduino\\src\\arduino.cpp'
    else:
        source_path = 'editor/arduino/src/hal/'
        destination = 'editor/arduino/src/arduino.cpp'

    shutil.copyfile(source_path + source_file, destination)

    # Generate Pin Array Sizes defines
    # We need to write the hal specific pin size defines on the global defines.h so that it is
    # available everywhere

    if os_platform.system() == 'Windows':
        define_path = 'editor\\arduino\\examples\\Baremetal\\'
    else:
        define_path = 'editor/arduino/examples/Baremetal/'
    file = open(define_path+'defines.h', 'r')
    define_file = file.read() + '\n\n//Pin Array Sizes\n'
    hal = open(destination, 'r')
    lines = hal.readlines()
    for line in lines:
        if (line.find('define NUM_DISCRETE_INPUT') > 0):
            define_file += line
        if (line.find('define NUM_ANALOG_INPUT') > 0):
            define_file += line
        if (line.find('define NUM_DISCRETE_OUTPUT') > 0):
            define_file += line
        if (line.find('define NUM_ANALOG_OUTPUT') > 0):
            define_file += line

    # Write defines.h file back to disk
    if os_platform.system() == 'Windows':
        define_path = 'editor\\arduino\\examples\\Baremetal\\'
    else:
        define_path = 'editor/arduino/examples/Baremetal/'
    f = open(define_path+'defines.h', 'w')
    f.write(define_file)
    f.flush()
    f.close()

    # Generate .elf file
    compiler_logs += "Generating binary file...\n"
    wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    wx.CallAfter(scrollToEnd, txtCtrl)

    # if (os.name == 'nt'):
    #    compilation = subprocess.check_output('editor\\arduino\\bin\\arduino-cli-w32 compile -v --libraries=editor\\arduino --build-property compiler.c.extra_flags="-Ieditor\\arduino\\src\\lib" --build-property compiler.cpp.extra_flags="-Ieditor\\arduino\\src\\lib" --export-binaries -b ' + platform + ' editor\\arduino\\examples\\Baremetal\\Baremetal.ino 2>&1')
    #compilation = subprocess.Popen(['editor\\arduino\\bin\\arduino-cli-w32', 'compile', '-v', '--libraries=..\\..\\', '--build-property', 'compiler.c.extra_flags="-I..\\src\\lib"', '--build-property', 'compiler.cpp.extra_flags="I..\\src\\lib"', '--export-binaries', '-b', platform, '..\\examples\\Baremetal\\Baremetal.ino'], cwd='editor\\arduino\\src', stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    # else:
    #    compilation = subprocess.check_output('editor/arduino/bin/arduino-cli-l64 compile -v --libraries=editor/arduino --build-property compiler.c.extra_flags="-Ieditor/arduino/src/lib" --build-property compiler.cpp.extra_flags="-Ieditor/arduino/src/lib" --export-binaries -b ' + platform + ' editor/arduino/examples/Baremetal/Baremetal.ino 2>&1')
    #compiler_logs += compilation.decode('utf-8')
    #wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    #wx.CallAfter(scrollToEnd, txtCtrl)

    compiler_logs += '\nCOMPILATION START: '
    compiler_logs += platform
    compiler_logs += '\n'

    if os_platform.system() == 'Windows':
        compilation = subprocess.Popen(['editor\\arduino\\bin\\arduino-cli-w32', 'compile', '-v', '--libraries=editor\\arduino', '--build-property', 'compiler.c.extra_flags="-Ieditor\\arduino\\src\\lib"', '--build-property',
                                       'compiler.cpp.extra_flags="-Ieditor\\arduino\\src\\lib"', '--export-binaries', '-b', platform, 'editor\\arduino\\examples\\Baremetal\\Baremetal.ino'], creationflags=0x08000000, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif os_platform.system() == 'Darwin':
        compilation = subprocess.Popen(['editor/arduino/bin/arduino-cli-mac', 'compile', '-v', '--libraries=editor/arduino', '--build-property', 'compiler.c.extra_flags="-Ieditor/arduino/src/lib"', '--build-property',
                                       'compiler.cpp.extra_flags="-Ieditor/arduino/src/lib"', '--export-binaries', '-b', platform, 'editor/arduino/examples/Baremetal/Baremetal.ino'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        compilation = subprocess.Popen(['editor/arduino/bin/arduino-cli-l64', 'compile', '-v', '--libraries=editor/arduino', '--build-property', 'compiler.c.extra_flags="-Ieditor/arduino/src/lib"', '--build-property',
                                       'compiler.cpp.extra_flags="-Ieditor/arduino/src/lib"', '--export-binaries', '-b', platform, 'editor/arduino/examples/Baremetal/Baremetal.ino'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = compilation.communicate()
    compiler_logs += stdout.decode('UTF-8')
    compiler_logs += stderr.decode('UTF-8')
    if (compilation.returncode != 0):
        compiler_logs += '\nCOMPILATION FAILED!\n'
    wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    wx.CallAfter(scrollToEnd, txtCtrl)

    if (compilation.returncode == 0):
        if (port != None):
            compiler_logs += '\nUploading program to Arduino board at ' + port + '...\n'
            wx.CallAfter(txtCtrl.SetValue, compiler_logs)
            wx.CallAfter(scrollToEnd, txtCtrl)
            if os_platform.system() == 'Windows':
                compiler_logs += runCommand('editor\\arduino\\bin\\arduino-cli-w32 upload --port ' +
                                            port + ' --fqbn ' + platform + ' editor\\arduino\\examples\\Baremetal/')
            elif os_platform.system() == 'Darwin':
                compiler_logs += runCommand('editor/arduino/bin/arduino-cli-mac upload --port ' +
                                            port + ' --fqbn ' + platform + ' editor/arduino/examples/Baremetal/ 2>&1')
            else:
                compiler_logs += runCommand('editor/arduino/bin/arduino-cli-l64 upload --port ' +
                                            port + ' --fqbn ' + platform + ' editor/arduino/examples/Baremetal/')
            compiler_logs += '\nDone!\n'
            wx.CallAfter(txtCtrl.SetValue, compiler_logs)
            wx.CallAfter(scrollToEnd, txtCtrl)
        else:
            cwd = os.getcwd()
            compiler_logs += '\nOUTPUT DIRECTORY:\n'
            if os_platform.system() == 'Windows':
                compiler_logs += cwd + '\\editor\\arduino\\examples\\Baremetal\\build\n'
            else:
                compiler_logs += cwd + '/editor/arduino/examples/Baremetal/build\n'
            compiler_logs += '\nCOMPILATION DONE!'
            wx.CallAfter(txtCtrl.SetValue, compiler_logs)
            wx.CallAfter(scrollToEnd, txtCtrl)
    time.sleep(1)  # make sure files are not in use anymore

    # no clean up
    return

    # Clean up and return
    if os.path.exists(base_path+'POUS.c'):
        os.remove(base_path+'POUS.c')
    if os.path.exists(base_path+'POUS.h'):
        os.remove(base_path+'POUS.h')
    if os.path.exists(base_path+'LOCATED_VARIABLES.h'):
        os.remove(base_path+'LOCATED_VARIABLES.h')
    if os.path.exists(base_path+'VARIABLES.csv'):
        os.remove(base_path+'VARIABLES.csv')
    if os.path.exists(base_path+'Config0.c'):
        os.remove(base_path+'Config0.c')
    if os.path.exists(base_path+'Config0.h'):
        os.remove(base_path+'Config0.h')
    if os.path.exists(base_path+'Config0.o'):
        os.remove(base_path+'Config0.o')
    if os.path.exists(base_path+'Res0.c'):
        os.remove(base_path+'Res0.c')
    if os.path.exists(base_path+'Res0.o'):
        os.remove(base_path+'Res0.o')
    if os.path.exists(base_path+'glueVars.c'):
        os.remove(base_path+'glueVars.c')
