import sys
import os
import time

if (len(sys.argv) < 3):
    print("Usage: python arduino_builder.py <st_file> <platform> [com_port]")
    quit()

st_file = sys.argv[1]
platform = sys.argv[2]
port = None
if (len(sys.argv) > 3):
    port = sys.argv[3]

if (os.path.exists("../bin/iec2c") or os.path.exists("../bin/iec2c.exe")):
    #remove old files first
    if os.path.exists('POUS.c'):
        os.remove('POUS.c')
    if os.path.exists('POUS.h'):
        os.remove('POUS.h')
    if os.path.exists('LOCATED_VARIABLES.h'):
        os.remove('LOCATED_VARIABLES.h')
    if os.path.exists('VARIABLES.csv'):
        os.remove('VARIABLES.csv')
    if os.path.exists('Config0.c'):
        os.remove('Config0.c')
    if os.path.exists('Config0.h'):
        os.remove('Config0.h')
    if os.path.exists('Res0.c'):
        os.remove('Res0.c')
else:
    print("Error: iec2c compiler not found!")
    quit()

#Setup environment
print("Configuring environment...")
if (os.name == 'nt'):
    env_setup = os.popen('..\\bin\\arduino-cli-w32 core install arduino:avr')
    print(env_setup.read())
    env_setup = os.popen('..\\bin\\arduino-cli-w32 core install arduino:samd')
    print(env_setup.read())
    env_setup = os.popen('..\\bin\\arduino-cli-w32 core install arduino:megaavr')
    print(env_setup.read())
    env_setup = os.popen('..\\bin\\arduino-cli-w32 core install arduino:mbed_portenta')
    print(env_setup.read())
    env_setup = os.popen('..\\bin\\arduino-cli-w32 lib install ArduinoModbus')
    print(env_setup.read())
    env_setup = os.popen('..\\bin\\arduino-cli-w32 lib install Arduino_MachineControl')
    print(env_setup.read())
    
else:
    env_setup = os.popen('../bin/arduino-cli-l64 core install arduino:avr')
    print(env_setup.read())
    env_setup = os.popen('../bin/arduino-cli-l64 core install arduino:samd')
    print(env_setup.read())
    env_setup = os.popen('../bin/arduino-cli-l64 core install arduino:megaavr')
    print(env_setup.read())
    env_setup = os.popen('../bin/arduino-cli-l64 core install arduino:mbed_portenta')
    print(env_setup.read())
    env_setup = os.popen('../bin/arduino-cli-l64 lib install ArduinoModbus')
    print(env_setup.read())
    env_setup = os.popen('../bin/arduino-cli-l64 lib install Arduino_MachineControl')
    print(env_setup.read())


#Generate C files
print("Compiling .st file...")
if (os.name == 'nt'):
    compilation = os.popen('..\\bin\\iec2c.exe ' + st_file)
else:
    compilation = os.popen('../bin/iec2c ' + st_file)
print(compilation.read())

#Generate glueVars.c
if not (os.path.exists("LOCATED_VARIABLES.h")):
    print("Error: Couldn't find LOCATED_VARIABLES.h. Check iec2c compiler output for more information")
    quit()

located_vars_file = open('LOCATED_VARIABLES.h', 'r')
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
extern unsigned long long common_ticktime__;

//OpenPLC Buffers
//Booleans
IEC_BOOL *bool_input[2][8];
IEC_BOOL *bool_output[2][8];
IEC_UINT *int_input[16];
IEC_UINT *int_output[16];
void glueVars()
{
"""

for located_var in located_vars:
    #cleanup located var line
    if ('__LOCATED_VAR(' in located_var):
        located_var = located_var.split('(')[1].split(')')[0]
        var_data = located_var.split(',')
        if (len(var_data) < 5):
            print('Error processing located var line: ' + located_var)
        else:
            var_type = var_data[0]
            var_name = var_data[1]
            var_address = var_data[4]
            var_subaddress = '0'
            if (len(var_data) > 5):
                var_subaddress = var_data[5]
            
            #check variable type and assign to correct buffer pointer
            if ('QX' in var_name):
                if (int(var_address) > 2 or int(var_subaddress) > 7):
                    print('Error: wrong location for var ' + var_name)
                    quit()
                glueVars += '    bool_output[' + var_address + '][' + var_subaddress + '] = ' + var_name + ';\n'
            elif ('IX' in var_name):
                if (int(var_address) > 2 or int(var_subaddress) > 7):
                    print('Error: wrong location for var ' + var_name)
                    quit()
                glueVars += '    bool_input[' + var_address + '][' + var_subaddress + '] = ' + var_name + ';\n'
            elif ('QW' in var_name):
                if (int(var_address) > 16):
                    print('Error: wrong location for var ' + var_name)
                    quit()
                glueVars += '    int_output[' + var_address + '] = ' + var_name + ';\n'
            elif ('IW' in var_name):
                if (int(var_address) > 16):
                    print('Error: wrong location for var ' + var_name)
                    quit()
                glueVars += '    int_input[' + var_address + '] = ' + var_name + ';\n'
            else:
                print('Could not process location "' + var_name + '" from line: ' + located_var)
                quit()

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

f = open('glueVars.c', 'w')
f.write(glueVars)
f.flush()
f.close()

time.sleep(2) #make sure glueVars.c was written to disk

# Patch POUS.c to include POUS.h
f = open('POUS.c', 'r')
pous_c = '#include "POUS.h"\n\n' + f.read()
f.close()

f = open('POUS.c', 'w')
f.write(pous_c)
f.flush()
f.close()

# Patch Res0.c to include POUS.h instead of POUS.c
f = open('Res0.c', 'r')
res0_c = ''
lines = f.readlines()
for line in lines:
    if '#include "POUS.c"' in line:
        res0_c += '#include "POUS.h"\n'
    else:
        res0_c += line
f.close()

f = open('Res0.c', 'w')
f.write(res0_c)
f.flush()
f.close()

#Generate .elf file
print("Generating binary file...")
if (os.name == 'nt'):
    compilation = os.popen('..\\bin\\arduino-cli-w32 compile -v --libraries=..\\..\\ --build-property compiler.c.extra_flags="-I..\\src\\lib" --build-property compiler.cpp.extra_flags="-I..\\src\\lib" --export-binaries -b ' + platform + ' ..\\examples\\Baremetal\\Baremetal.ino')
else:
    compilation = os.popen('../bin/arduino-cli-l64 compile -v --libraries=../../ --build-property compiler.c.extra_flags="-I../src/lib" --build-property compiler.cpp.extra_flags="-I../src/lib" --export-binaries -b ' + platform + ' ../examples/Baremetal/Baremetal.ino')
print(compilation.read())
if (port != None):
    if (os.name == 'nt'):
        uploading = os.popen('..\\bin\\arduino-cli-w32 upload --port ' + port + ' --fqbn ' + platform + ' ..\\examples\\Baremetal/')
    else:
        uploading = os.popen('../bin/arduino-cli-l64 upload --port ' + port + ' --fqbn ' + platform + ' ../examples/Baremetal/')
    print(uploading.read())
    
#print("No clean up")
#quit()
    
if (os.name != 'nt'):
    print("Cleaning up...")
    if os.path.exists('POUS.c'):
        os.remove('POUS.c')
    if os.path.exists('POUS.h'):
        os.remove('POUS.h')
    if os.path.exists('LOCATED_VARIABLES.h'):
        os.remove('LOCATED_VARIABLES.h')
    if os.path.exists('VARIABLES.csv'):
        os.remove('VARIABLES.csv')
    if os.path.exists('Config0.c'):
        os.remove('Config0.c')
    if os.path.exists('Config0.h'):
        os.remove('Config0.h')
    if os.path.exists('Config0.o'):
        os.remove('Config0.o')
    if os.path.exists('Res0.c'):
        os.remove('Res0.c')
    if os.path.exists('Res0.o'):
        os.remove('Res0.o')
    if os.path.exists('glueVars.c'):
        os.remove('glueVars.c')
    
    
