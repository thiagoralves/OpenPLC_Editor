#include <Arduino_CAN.h>

extern "C" void *init_arduinocan(uint8_t,int);
extern "C" bool write_arduinocan(uint32_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
extern "C" bool write_arduinocan_word(uint32_t,uint64_t);
extern "C" uint64_t read_arduinocan();

void *init_arduinocan(uint8_t pin_en, int baudrate)
{   
#ifdef PIN_CAN0_STBY
    if(PIN_CAN0_STBY > -1) {
        pinMode(PIN_CAN0_STBY, OUTPUT);
        digitalWrite(PIN_CAN0_STBY, LOW);
    } else {
        pinMode(pin_en, OUTPUT);
        digitalWrite(pin_en, LOW);
    }
#elif
    pinMode(pin_en, OUTPUT);
    digitalWrite(pin_en, LOW);
#endif
    if (!CAN.begin((CanBitRate)baudrate))
    {
        Serial.println("CAN.begin(...) failed.");
        for (;;) {}
    }
}

bool write_arduinocan(uint32_t id ,uint8_t d0, uint8_t d1 ,uint8_t d2, uint8_t d3, uint8_t d4, uint8_t d5, 
                                                                    uint8_t d6, uint8_t d7)
{
    //uint8_t data[4] = {d1, d2, d3, d4};
    uint8_t const msg_data[] = {d0, d1, d2, d3, d4, d5, d6, d7};
    //memcpy((void *)(msg_data + 4), &data, sizeof(data));
    CanMsg msg(id, sizeof(msg_data), msg_data);

    /* Transmit the CAN message, capture and display an
    * error core in case of failure.
    */
    if (int const rc = CAN.write(msg); rc < 0)
    {
        return 0;
    }
    return 1;
}

bool write_arduinocan_word(uint32_t id , uint64_t data)
{

    uint32_t const msg_data[2] = {0,0};
    memcpy((void *)(msg_data), &data, sizeof(data));
    CanMsg msg(id, sizeof(msg_data), (uint8_t *)&msg_data);

    if (int const rc = CAN.write(msg); rc < 0)
    {
        return 0;
    }
    return 1;
}

uint64_t read_arduinocan()
{
    uint64_t data = 0;
    if (CAN.available())
    {
        CanMsg const msg = CAN.read();
        uint8_t payload[8] = {0};
        for(int i = 0; i < msg.data_length || i < 8; i++) {
            payload[i] = msg.data[i];
        }
        memcpy((void *)(&data), &payload, sizeof(payload));
    }
    return data;
}