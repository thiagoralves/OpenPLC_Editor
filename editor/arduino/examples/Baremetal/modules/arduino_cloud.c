#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>

extern "C" void cloud_begin(char *, char *, char *);
extern "C" void cloud_add_bool(char *, int *);
extern "C" void cloud_add_int(char *, int *);
extern "C" void cloud_add_float(char *, float *);
extern "C" void cloud_update();

bool first_update = true;

WiFiConnectionHandler *ArduinoIoTPreferredConnection;

void cloud_begin(char *thing_id, char *str_ssid, char *str_pass)
{
    Serial.begin(9600);
    ArduinoIoTPreferredConnection = new WiFiConnectionHandler(str_ssid, str_pass);
    ArduinoCloud.setThingId(thing_id);
}

void cloud_update()
{
    if (first_update)
    {
        first_update = false;
        ArduinoCloud.begin(*ArduinoIoTPreferredConnection);
    
        //Temporary
        setDebugMessageLevel(4);
        ArduinoCloud.printDebugInfo();
    }
    ArduinoCloud.update();
}

void cloud_add_bool(char *var_name, int *bool_var)
{
    ArduinoCloud.addPropertyReal(*bool_var, String(var_name));
}

void cloud_add_int(char *var_name, int *int_var)
{
    ArduinoCloud.addPropertyReal(*int_var, String(var_name));
}

void cloud_add_float(char *var_name, float *float_var)
{
    ArduinoCloud.addPropertyReal(*float_var, String(var_name));
}