import json
import os
import platform as os_platform
import shutil
import subprocess
import sys
import time
import select
import wx

global compiler_logs
compiler_logs = ''


def append_compiler_log(txtCtrl, output):
    global compiler_logs
    compiler_logs += output
    def update():
        #if os_platform.system() != 'Darwin':
        #    txtCtrl.SetInsertionPoint(-1)
        txtCtrl.SetValue(compiler_logs)
        txtCtrl.ShowPosition(txtCtrl.GetLastPosition())
        txtCtrl.Refresh()
        txtCtrl.Update()

    wx.CallAfter(update)

def runCommand(command):
    cmd_response = None

    try:
        cmd_response = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        cmd_response = exc.output

    if cmd_response == None:
        return ''

    return cmd_response.decode('utf-8', errors='backslashreplace')

def read_output(process, txtCtrl, timeout=None):
    start_time = time.time()
    return_code = 0

    while True:
        output = process.stdout.readline()
        if output:
            append_compiler_log(txtCtrl, output.decode('UTF-8', errors='backslashreplace'))
            wx.YieldIfNeeded()

        # check for process exit
        poll_result = process.poll()
        if poll_result is not None:
            # process terminated, read remaining output data
            for line in process.stdout:
                append_compiler_log(txtCtrl, line.decode('UTF-8', errors='backslashreplace'))
                wx.YieldIfNeeded()
            return_code = poll_result
            break

        # watch for the timeout
        if (timeout is not None) and ((time.time() - start_time) > timeout):
            process.kill()
            return_code = -1  # timeout error code
            break

        # brief sleep to reduce CPU load
        time.sleep(1)

    return return_code


def runCommandToWin(txtCtrl, command, cwd=None, timeout=None):
    return_code = -2  # default value for unexpected errors
    append_compiler_log(txtCtrl, '$ ' + ' '.join(map(str, command)) + '\n')
    try:
        if os_platform.system() == 'Windows':
            compilation = subprocess.Popen(command, cwd=cwd, creationflags=0x08000000, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        elif os_platform.system() == 'Darwin':
            compilation = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            compilation = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return_code = read_output(compilation, txtCtrl, timeout)
        append_compiler_log(txtCtrl, '$? = ' + str(return_code) + '\n')

    except subprocess.CalledProcessError as exc:
        append_compiler_log(txtCtrl, exc.output)
        return_code = exc.returncode if exc.returncode is not None else -3

    return return_code

def build(st_file, platform, source_file, port, txtCtrl, hals, update_subsystem):
    global compiler_logs
    compiler_logs = ''

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
        append_compiler_log(txtCtrl, _("Error: iec2c compiler not found!") + '\n')
        return

    #Install/Update board support
    if board_installed == False or update_subsystem == True:
        if board_installed == False:
            append_compiler_log(txtCtrl, _("Support for {platform} is not installed on OpenPLC Editor. Please be patient and wait while {platform} is being installed...").format(platform=platform) + '\n')
        elif update_subsystem == True:
            append_compiler_log(txtCtrl, _("Updating support for {platform}. Please be patient and wait while {platform} is being installed...").format(platform=platform) + '\n')

        cli_command = ''
        if os_platform.system() == 'Windows':
            cli_command = ['editor\\arduino\\bin\\arduino-cli-w64', '--no-color']
        elif os_platform.system() == 'Darwin':
            cli_command = ['editor/arduino/bin/arduino-cli-mac', '--no-color']
        else:
            cli_command = ['editor/arduino/bin/arduino-cli-l64', '--no-color']

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
        runCommandToWin(txtCtrl, cli_command + ['config', 'init'])

        # Setup boards - remove 3rd party boards to re-add them later since we don't know if they're there or not
        runCommandToWin(txtCtrl, cli_command + ['config', 'remove', 'board_manager.additional_urls',
            'https://arduino.esp8266.com/stable/package_esp8266com_index.json',
            'https://espressif.github.io/arduino-esp32/package_esp32_index.json',
            'https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json',
            'https://raw.githubusercontent.com/CONTROLLINO-PLC/CONTROLLINO_Library/master/Boards/package_ControllinoHardware_index.json',
            'https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json',
            'https://facts-engineering.gitlab.io/facts-open-source/p1am/beta_file_hosting/package_productivity-P1AM_200-boardmanagermodule_index.json',
            'https://raw.githubusercontent.com/VEA-SRL/IRUINO_Library/main/package_vea_index.json',
            'https://raw.githubusercontent.com/facts-engineering/facts-engineering.github.io/master/package_productivity-P1AM-boardmanagermodule_index.json'])

        # Setup boards - add 3rd party boards
        runCommandToWin(txtCtrl, cli_command + ['config', 'add', 'board_manager.additional_urls',
            'https://arduino.esp8266.com/stable/package_esp8266com_index.json',
            'https://espressif.github.io/arduino-esp32/package_esp32_index.json',
            'https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json',
            'https://raw.githubusercontent.com/CONTROLLINO-PLC/CONTROLLINO_Library/master/Boards/package_ControllinoHardware_index.json',
            'https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json',
            'https://facts-engineering.gitlab.io/facts-open-source/p1am/beta_file_hosting/package_productivity-P1AM_200-boardmanagermodule_index.json',
            'https://raw.githubusercontent.com/facts-engineering/facts-engineering.github.io/master/package_productivity-P1AM-boardmanagermodule_index.json',
            'https://raw.githubusercontent.com/VEA-SRL/IRUINO_Library/main/package_vea_index.json'])

        # Update
        runCommandToWin(txtCtrl, cli_command + ['core', 'update-index'])
        runCommandToWin(txtCtrl, cli_command + ['update'])

        # Install board
        runCommandToWin(txtCtrl, cli_command + ['core', 'install', core])

        # Install all libs - required after core install/update
        runCommandToWin(txtCtrl, cli_command + ['lib', 'install',
                    'WiFiNINA',
                    'Ethernet',
                    'Arduino_MachineControl',
                    'Arduino_EdgeControl',
                    'OneWire',
                    'DallasTemperature',
                    'P1AM',
                    'CONTROLLINO',
                    'PubSubClient',
                    'ArduinoJson',
                    'arduinomqttclient',
                    'RP2040_PWM',
                    'AVR_PWM',
                    'megaAVR_PWM',
                    'SAMD_PWM',
                    'SAMDUE_PWM',
                    'Portenta_H7_PWM',
                    'CAN',
                    'STM32_CAN',
                    'STM32_PWM'])

    # Generate C files
    append_compiler_log(txtCtrl, _("Compiling .st file...") + '\n')
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
        return_code = runCommandToWin(txtCtrl, ['editor\\arduino\\bin\\iec2c.exe', '-f', '-l', '-p', 'plc_prog.st'], cwd='editor\\arduino\\src')
    elif os_platform.system() == 'Darwin':
        return_code = runCommandToWin(txtCtrl, ['../bin/iec2c_mac', '-f', '-l', '-p', 'plc_prog.st'], cwd='./editor/arduino/src')
    else:
        return_code = runCommandToWin(txtCtrl, ['../bin/iec2c', '-f', '-l', '-p', 'plc_prog.st'], cwd='./editor/arduino/src')

    # Remove temporary plc program
    # if os.path.exists(base_path+'plc_prog.st'):
    #    os.remove(base_path+'plc_prog.st')

    # Generate glueVars.c
    if not (os.path.exists(base_path+'LOCATED_VARIABLES.h')):
        append_compiler_log(txtCtrl, "Error: Couldn't find LOCATED_VARIABLES.h. Check iec2c compiler output for more information\n")
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
#define MAX_MEMORY_WORD            0
#define MAX_MEMORY_DWORD           0
#define MAX_MEMORY_LWORD           0

IEC_BOOL *bool_input[MAX_DIGITAL_INPUT/8][8];
IEC_BOOL *bool_output[MAX_DIGITAL_OUTPUT/8][8];
IEC_UINT *int_input[MAX_ANALOG_INPUT];
IEC_UINT *int_output[MAX_ANALOG_OUTPUT];

#else

#define MAX_DIGITAL_INPUT          56
#define MAX_DIGITAL_OUTPUT         56
#define MAX_ANALOG_INPUT           32
#define MAX_ANALOG_OUTPUT          32
#define MAX_MEMORY_WORD            20
#define MAX_MEMORY_DWORD           20
#define MAX_MEMORY_LWORD           20

IEC_BOOL *bool_input[MAX_DIGITAL_INPUT/8][8];
IEC_BOOL *bool_output[MAX_DIGITAL_OUTPUT/8][8];
IEC_UINT *int_input[MAX_ANALOG_INPUT];
IEC_UINT *int_output[MAX_ANALOG_OUTPUT];
IEC_UINT *int_memory[MAX_MEMORY_WORD];
IEC_UDINT *dint_memory[MAX_MEMORY_DWORD];
IEC_ULINT *lint_memory[MAX_MEMORY_LWORD];

#endif


void glueVars()
{
"""
    for located_var in located_vars:
        # cleanup located var line
        if ('__LOCATED_VAR(' in located_var):
            located_var = located_var.split('(')[1].split(')')[0]
            var_data = located_var.split(',')
            if (len(var_data) < 5):
                append_compiler_log(txtCtrl, _('Error processing located var line: {var_line_text}').format(var_line_text=located_var) + '\n')
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
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    bool_output[' + var_address + \
                        '][' + var_subaddress + '] = ' + var_name + ';\n'
                elif ('IX' in var_name):
                    if (int(var_address) > 6 or int(var_subaddress) > 7):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    bool_input[' + var_address + \
                        '][' + var_subaddress + '] = ' + var_name + ';\n'
                elif ('QW' in var_name):
                    if (int(var_address) > 32):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    int_output[' + \
                        var_address + '] = ' + var_name + ';\n'
                elif ('IW' in var_name):
                    if (int(var_address) > 32):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    int_input[' + \
                        var_address + '] = ' + var_name + ';\n'
                elif ('MW' in var_name):
                    if (int(var_address) > 20):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    int_memory[' + \
                        var_address + '] = ' + var_name + ';\n'
                elif ('MD' in var_name):
                    if (int(var_address) > 20):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    dint_memory[' + \
                        var_address + '] = ' + var_name + ';\n'
                elif ('ML' in var_name):
                    if (int(var_address) > 20):
                        append_compiler_log(txtCtrl, _('Error: wrong location for var {var_name}').format(var_name=var_name) + '\n')
                        return
                    glueVars += '    lint_memory[' + \
                        var_address + '] = ' + var_name + ';\n'
                else:
                    append_compiler_log(txtCtrl, _('Could not process location "{var_name}" from line: {var_line_text}').format(var_name=var_name, located_var=located_var) + '\n')
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
    append_compiler_log(txtCtrl, _('Generating binary file...') + '\n')

    # if (os.name == 'nt'):
    #    compilation = subprocess.check_output('editor\\arduino\\bin\\arduino-cli-w64 compile -v --libraries=editor\\arduino --build-property compiler.c.extra_flags="-Ieditor\\arduino\\src\\lib" --build-property compiler.cpp.extra_flags="-Ieditor\\arduino\\src\\lib" --export-binaries -b ' + platform + ' editor\\arduino\\examples\\Baremetal\\Baremetal.ino 2>&1')
    #compilation = subprocess.Popen(['editor\\arduino\\bin\\arduino-cli-w64', 'compile', '-v', '--libraries=..\\..\\', '--build-property', 'compiler.c.extra_flags="-I..\\src\\lib"', '--build-property', 'compiler.cpp.extra_flags="I..\\src\\lib"', '--export-binaries', '-b', platform, '..\\examples\\Baremetal\\Baremetal.ino'], cwd='editor\\arduino\\src', stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    # else:
    #    compilation = subprocess.check_output('editor/arduino/bin/arduino-cli-l64 compile -v --libraries=editor/arduino --build-property compiler.c.extra_flags="-Ieditor/arduino/src/lib" --build-property compiler.cpp.extra_flags="-Ieditor/arduino/src/lib" --export-binaries -b ' + platform + ' editor/arduino/examples/Baremetal/Baremetal.ino 2>&1')
    #compiler_logs += compilation.decode('utf-8')
    #wx.CallAfter(txtCtrl.SetValue, compiler_logs)
    #wx.CallAfter(scrollToEnd, txtCtrl)

    append_compiler_log(txtCtrl, '\n' + _('COMPILATION START: {platform}').format(platform=platform) + '\n')

    extraflags = ''
    if core == 'esp32:esp32':
        extraflags = ' -MMD -c'

    if os_platform.system() == 'Windows':
        return_code = runCommandToWin(txtCtrl, ['editor\\arduino\\bin\\arduino-cli-w64', '--no-color', 'compile', '-v', '--libraries=editor\\arduino', '--build-property', 'compiler.c.extra_flags=-Ieditor\\arduino\\src\\lib' + extraflags, '--build-property',
                                       'compiler.cpp.extra_flags=-Ieditor\\arduino\\src\\lib' + extraflags, '--export-binaries', '-b', platform, 'editor\\arduino\\examples\\Baremetal\\Baremetal.ino'])
    elif os_platform.system() == 'Darwin':
        return_code = runCommandToWin(txtCtrl, ['editor/arduino/bin/arduino-cli-mac', '--no-color', 'compile', '-v', '--libraries=editor/arduino', '--build-property', 'compiler.c.extra_flags=-Ieditor/arduino/src/lib' + extraflags, '--build-property',
                                       'compiler.cpp.extra_flags=-Ieditor/arduino/src/lib' + extraflags, '--export-binaries', '-b', platform, 'editor/arduino/examples/Baremetal/Baremetal.ino'])
    else:
        return_code = runCommandToWin(txtCtrl, ['editor/arduino/bin/arduino-cli-l64', '--no-color', 'compile', '-v', '--libraries=editor/arduino', '--build-property', 'compiler.c.extra_flags=-Ieditor/arduino/src/lib' + extraflags, '--build-property',
                                       'compiler.cpp.extra_flags=-Ieditor/arduino/src/lib' + extraflags, '--export-binaries', '-b', platform, 'editor/arduino/examples/Baremetal/Baremetal.ino'])

    if (return_code != 0):
        append_compiler_log(txtCtrl, '\n' + _('COMPILATION FAILED!') + '\n')

    if (return_code == 0):
        if (port != None):
            append_compiler_log(txtCtrl, '\n' + _('Uploading program to Arduino board at {port}...').format(port=port) + '\n')
            if os_platform.system() == 'Windows':
                return_code = runCommandToWin(txtCtrl, ['editor\\arduino\\bin\\arduino-cli-w64', '--no-color', 'upload', '--port',
                                                port, '--fqbn', platform, 'editor\\arduino\\examples\\Baremetal/'])
            elif os_platform.system() == 'Darwin':
                return_code = runCommandToWin(txtCtrl, ['editor/arduino/bin/arduino-cli-mac', '--no-color', 'upload', '--port',
                                                port, '--fqbn', platform, 'editor/arduino/examples/Baremetal/'])
            else:
                return_code = runCommandToWin(txtCtrl, ['editor/arduino/bin/arduino-cli-l64', '--no-color', 'upload', '--port',
                                                port, '--fqbn', platform, 'editor/arduino/examples/Baremetal/'])

            append_compiler_log(txtCtrl, '\n' + _('Done!') + '\n')
        else:
            cwd = os.getcwd()
            append_compiler_log(txtCtrl, '\n' + _('OUTPUT DIRECTORY:') + '\n')
            if os_platform.system() == 'Windows':
                append_compiler_log(txtCtrl, cwd + '\\editor\\arduino\\examples\\Baremetal\\build\n')
            else:
                append_compiler_log(txtCtrl, cwd + '/editor/arduino/examples/Baremetal/build\n')
            append_compiler_log(txtCtrl, '\n' + _('COMPILATION DONE!'))
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
