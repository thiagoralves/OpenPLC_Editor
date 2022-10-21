/*
ModbusSlave.cpp - Source for Modbus Slave Library
Copyright (C) 2022 OpenPLC - Thiago Alves
*/

#include "ModbusSlave.h"

//Global Modbus vars
struct MBinfo modbus;
uint8_t mb_frame[MAX_MB_FRAME];
uint16_t mb_frame_len;
Stream* mb_serialport;
int8_t mb_txpin;
uint16_t mb_t15; // inter character time out
uint16_t mb_t35; // frame delay
#ifdef MBTCP_ETHERNET
    EthernetServer mb_server(502);
    uint8_t mb_mbap[MBAP_SIZE];
#endif
#ifdef MBTCP_WIFI
    WiFiServer mb_server(502);
    uint8_t mb_mbap[MBAP_SIZE];
#if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    WiFiClient mb_serverClients[MAX_SRV_CLIENTS];
#endif
#endif

bool init_mbregs(uint8_t size_holding, uint8_t size_coils, uint8_t size_inputregs, uint8_t size_inputstatus)
{
    //Save sizes
    modbus.holding_size = size_holding;
    modbus.coils_size = size_coils;
    modbus.input_regs_size = size_inputregs;
    modbus.input_status_size = size_inputstatus;

    //round discrete regs sizes
    if (size_coils % 8 > 0) 
        size_coils = (size_coils / 8) + 1;
    else
        size_coils = size_coils / 8;
    if (size_inputstatus % 8 > 0) 
        size_inputstatus = (size_inputstatus / 8) + 1;
    else
        size_inputstatus = (size_inputstatus / 8);

    modbus.coils = (uint8_t *)malloc(size_coils * sizeof(uint8_t));
    if (modbus.coils == NULL) return false;
    memset(modbus.coils, 0, size_coils * sizeof(uint8_t));

    modbus.holding = (uint16_t *)malloc(size_holding * sizeof(uint16_t));
    if (modbus.holding == NULL) return false;
    memset(modbus.holding, 0, size_holding * sizeof(uint8_t));

    modbus.input_status = (uint8_t *)malloc(size_inputstatus * sizeof(uint8_t));
    if (modbus.input_status == NULL) return false;
    memset(modbus.input_status, 0, size_inputstatus * sizeof(uint8_t));

    modbus.input_regs = (uint16_t *)malloc(size_inputregs * sizeof(uint16_t));
    if (modbus.input_regs == NULL) return false;
    memset(modbus.input_regs, 0, size_inputregs * sizeof(uint8_t));

    return true;
}

bool get_discrete(uint16_t addr, bool regtype)
{
    uint8_t byte_addr = addr / 8;
    uint8_t bit_addr = addr % 8;
    if (regtype == COILS)
        return bitRead(modbus.coils[byte_addr], bit_addr);
    else
        return bitRead(modbus.input_status[byte_addr], bit_addr);
}

void write_discrete(uint16_t addr, bool regtype, bool value)
{
    uint8_t byte_addr = addr / 8;
    uint8_t bit_addr = addr % 8;
    if (regtype == COILS)
        bitWrite(modbus.coils[byte_addr], bit_addr, value);
    else
        bitWrite(modbus.input_status[byte_addr], bit_addr, value);
}

void mbconfig_serial_iface(HardwareSerial* port, long baud, int txPin)
{
    mb_serialport = port;
    mb_txpin = txPin;
    (*port).begin(baud);

    //RS-485 control
    if (txPin >= 0) 
    {
        pinMode(txPin, OUTPUT);
        digitalWrite(txPin, LOW);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
        if (mb_serialport == &Serial3) 
            Controllino_RS485Init();
    #endif

    // Modbus states that a baud rate higher than 19200 must use a fixed 750 us
    // for inter character time out. For baud rates below 19200 the timing
    // is more critical and has to be calculated.
    // E.g. 9600 baud in a 11 bit packet is 9600/11 = 872 characters per second
    // In milliseconds this will be 872 characters per 1000ms. So for 1 character
    // 1000ms/872 characters is 1.14583ms per character. Finally modbus states
    // an inter-character must be 1.5T or 1.5 times longer than a character. Thus
    // 1.5T = 1.14583ms * 1.5 = 1.71875ms.
    // Thus the formula is T1.5(us) = (1000ms * 1000(us) * 1.5 * 11bits)/baud
    // 1000ms * 1000(us) * 1.5 * 11bits = 16500000 can be calculated as a constant

    if (baud > 19200)
        mb_t15 = 750;
    else
        mb_t15 = 16500000/baud; // 1T * 1.5 = T1.5

    /* The modbus definition of a frame delay is a waiting period of 3.5 character times
    between packets.*/

    mb_t35 = mb_t15 * 3.5;
}

#ifdef MBTCP
void mbconfig_ethernet_iface(uint8_t *mac, uint8_t *ip, uint8_t *dns, uint8_t *gateway, uint8_t *subnet)
{
    #ifdef MBTCP_ETHERNET
        if (ip == NULL)
            Ethernet.begin(mac);
        else if (dns == NULL)
            Ethernet.begin(mac, IPAddress(ip));
        else if (gateway == NULL)
            Ethernet.begin(mac, IPAddress(ip), IPAddress(dns));
        else if (subnet == NULL)
            Ethernet.begin(mac, IPAddress(ip), IPAddress(dns), IPAddress(gateway));
        else
            Ethernet.begin(mac, IPAddress(ip), IPAddress(dns), IPAddress(gateway), IPAddress(subnet));
    #endif
    #ifdef MBTCP_WIFI
        #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
            if (subnet != NULL)
            {
                uint8_t secondaryDNS[] = {8, 8, 8, 8};
                WiFi.config(IPAddress(ip), IPAddress(gateway), IPAddress(subnet), IPAddress(dns), IPAddress(secondaryDNS));
            }
            mb_server.setNoDelay(true);
        #else
            if (dns == NULL)
                WiFi.config(IPAddress(ip));
            else if (gateway == NULL)
                WiFi.config(IPAddress(ip), IPAddress(dns));
            else if (subnet == NULL)
                WiFi.config(IPAddress(ip), IPAddress(dns), IPAddress(gateway));
            else
                WiFi.config(IPAddress(ip), IPAddress(dns), IPAddress(gateway), IPAddress(subnet));
        #endif
        WiFi.begin(MBTCP_SSID, MBTCP_PWD);
        int num_tries = 0;
        while (WiFi.status() != WL_CONNECTED) 
        {
            delay(500);
            num_tries++;
            if (num_tries == 10) break;
        }
    #endif
    mb_server.begin();
}
#endif

void mbtask()
{
    #ifdef MBTCP
        handle_tcp();
    #endif
    #ifdef MBSERIAL
        handle_serial();
    #endif
}

#ifdef MBTCP
void handle_tcp()
{
    #ifdef MBTCP_ETHERNET
        EthernetClient client = mb_server.available();
    #endif
    #if defined(MBTCP_WIFI) && !defined(BOARD_ESP8266) && !defined(BOARD_ESP32)
        WiFiClient client = mb_server.available();
    #endif

    //ESP boards have a slightly different implementation of the WiFi API - therefore their specific
    //code lies below
    #if (defined(BOARD_ESP8266) || defined(BOARD_ESP32)) && defined(MBTCP_WIFI)
        if (mb_server.hasClient()) 
        {
            for (int i = 0; i < MAX_SRV_CLIENTS; i++) 
            {
                if (!mb_serverClients[i]) //equivalent to !serverClients[i].connected()
                { 
                    mb_serverClients[i] = mb_server.available();
                    break;
                }
            }
        }

        //search all clients for data
        for (int i = 0; i < MAX_SRV_CLIENTS; i++) 
        {
            int j = 0;
            if (mb_serverClients[i].connected() && mb_serverClients[i].available())
            {
                //Read packet
                while (mb_serverClients[i].available())
                {
                    mb_mbap[j] = mb_serverClients[i].read();
                    j++;
                    if (j==MBAP_SIZE) break;  //MBAP has 6 bytes (we use UnitID as SlaveID)
                }
                
                mb_frame_len = mb_mbap[4] << 8 | mb_mbap[5];
        
                if (mb_mbap[2] !=0 || mb_mbap[3] !=0) return;   //Not a MODBUSIP packet
                if (mb_frame_len < 6 || mb_frame_len > MAX_MB_FRAME) return;      //Packet is too small or too big

                j = 0;
                while (mb_serverClients[i].available()) 
                {
                    mb_frame[j] = mb_serverClients[i].read();
                    j++;
                    if (j==mb_frame_len) break;
                }

                //Safety check - discard packages that lie about their size
                if (i != mb_frame_len) return;

                //Process packet and write back
                process_mbpacket();
                //Calculate packet length for MBAP header (mb_frame_len + 1)
                mb_mbap[4] = (mb_frame_len+1) >> 8;
                mb_mbap[5] = (mb_frame_len+1) & 0x00FF;
    
                uint8_t sendbuffer[mb_frame_len + MBAP_SIZE];

                //MBAP
                for (j = 0 ; j < MBAP_SIZE ; j++)
                    sendbuffer[j] = mb_mbap[j];

                //PDU Frame
                for (j = 0 ; j < mb_frame_len ; j++)
                    sendbuffer[j+MBAP_SIZE] = mb_frame[j];
                
                //Write back
                mb_serverClients[i].write(sendbuffer, mb_frame_len + MBAP_SIZE);
            }
        }

        //If this is not an ESP board, then here is the default code
    #else
        if (client) 
        {
            if (client.connected()) 
            {
                int i = 0;
                while (client.available())
                {
                    mb_mbap[i] = client.read();
                    i++;
                    if (i==MBAP_SIZE) break;  //MBAP has 6 bytes (we use UnitID as SlaveID)
                }

                mb_frame_len = mb_mbap[4] << 8 | mb_mbap[5];
        
                if (mb_mbap[2] !=0 || mb_mbap[3] !=0) return;   //Not a MODBUSIP packet
                if (mb_frame_len < 6 || mb_frame_len > MAX_MB_FRAME) return;      //Packet is too small or too big

                i = 0;
                while (client.available())
                {
                    mb_frame[i] = client.read();
                    i++;
                    if (i==mb_frame_len || i==MAX_MB_FRAME) break;
                }

                //Safety check - discard packages that lie about their size
                if (i != mb_frame_len) return;

                //Process packet and write back
                process_mbpacket();
                //Calculate packet length for MBAP header (mb_frame_len + 1)
                mb_mbap[4] = (mb_frame_len+1) >> 8;
                mb_mbap[5] = (mb_frame_len+1) & 0x00FF;
    
                uint8_t sendbuffer[mb_frame_len + MBAP_SIZE];

                //MBAP
                for (i = 0 ; i < MBAP_SIZE ; i++)
                    sendbuffer[i] = mb_mbap[i];

                //PDU Frame
                for (i = 0 ; i < mb_frame_len ; i++)
                    sendbuffer[i+MBAP_SIZE] = mb_frame[i];
                
                //Write back
                client.write(sendbuffer, mb_frame_len + MBAP_SIZE);
            }
        }
    #endif
}
#endif

#ifdef MBSERIAL
void handle_serial()
{
    mb_frame_len = 0;

    if ((*mb_serialport).available() == 0) 
        return;
	
    while ((*mb_serialport).available() > mb_frame_len) 
    {
        mb_frame_len = (*mb_serialport).available();
        delayMicroseconds(mb_t15);
    }

    //Check if packet is too big or too small
    if ((*mb_serialport).available() > MAX_MB_FRAME || (*mb_serialport).available() < 6)
    {
        (*mb_serialport).flush();
        return;
    }

    //Read packet
    for (uint16_t i = 0; i < mb_frame_len; i++)
    {
        mb_frame[i] = (*mb_serialport).read();
    }

    //Validate crc
    uint16_t packet_crc = ((mb_frame[mb_frame_len - 2] << 8) | mb_frame[mb_frame_len - 1]);
    if (packet_crc != calcCrc()) 
    {
        (*mb_serialport).flush();
        return;
    }

    //Validate SlaveID
    if (mb_frame[0] != modbus.slaveid) 
    {
        (*mb_serialport).flush();
        return;
    }

    //Remove CRC (must do that before processing packet)
    mb_frame_len -= 2;
    
    //Process packet and write back
    process_mbpacket();

    //Add CRC
    //Check if response message is too big for this device
    if (mb_frame_len + 2 > MAX_MB_FRAME) exceptionResponse(mb_frame[1], MB_EX_SLAVE_FAILURE);
    mb_frame_len += 2; //increase frame length by two bytes to acomodate CRC
    packet_crc = calcCrc(); //calculate CRC of the new packet
    mb_frame[mb_frame_len - 2] = (uint8_t)(packet_crc >> 8);
    mb_frame[mb_frame_len - 1] = (uint8_t)(packet_crc & 0x00FF);

    if (mb_txpin >= 0) 
    {
        digitalWrite(mb_txpin, HIGH);
        delayMicroseconds(mb_t35);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
        if (mb_serialport == &Serial3) // RS485 serial port
            Controllino_RS485TxEnable(); // Enable RS485 chip to transmit 
    #endif

    (*mb_serialport).write(mb_frame, mb_frame_len);
    (*mb_serialport).flush();
    delayMicroseconds(mb_t35);

    if (mb_txpin >= 0)
        digitalWrite(mb_txpin, LOW);
    
    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
        if (mb_serialport == &Serial3) // RS485 serial port
            Controllino_RS485RxEnable(); // Go back to receive mode after transmitted data
    #endif
}
#endif

void process_mbpacket()
{
    uint8_t fcode  = mb_frame[1];
    uint16_t field1 = (uint16_t)mb_frame[2] << 8 | (uint16_t)mb_frame[3];
    uint16_t field2 = (uint16_t)mb_frame[4] << 8 | (uint16_t)mb_frame[5];
    
    switch (fcode) 
    {
        case MB_FC_WRITE_REG:
            //field1 = reg, field2 = value
            writeSingleRegister(field1, field2);
        break;

        case MB_FC_READ_REGS:
            //field1 = startreg, field2 = numregs
            readRegisters(field1, field2);
        break;

        case MB_FC_WRITE_REGS:
            //field1 = startreg, field2 = status
            writeMultipleRegisters(field1, field2, mb_frame[6]);
        break;

        case MB_FC_READ_COILS:
            //field1 = startreg, field2 = numregs
            readCoils(field1, field2);
        break;

        case MB_FC_READ_INPUT_STAT:
            //field1 = startreg, field2 = numregs
            readInputStatus(field1, field2);
        break;

        case MB_FC_READ_INPUT_REGS:
            //field1 = startreg, field2 = numregs
            readInputRegisters(field1, field2);
        break;

        case MB_FC_WRITE_COIL:
            //field1 = reg, field2 = status
            writeSingleCoil(field1, field2);
        break;

        case MB_FC_WRITE_COILS:
            //field1 = startreg, field2 = numoutputs
            writeMultipleCoils(field1, field2, mb_frame[6]);
        break;

        default:
            exceptionResponse(fcode, MB_EX_ILLEGAL_FUNCTION);
    }
}


//Modbus handling functions
void readRegisters(uint16_t startreg, uint16_t numregs)
{
    //Check value (numregs)
    if (numregs < 0x0001 || numregs > 0x007D) 
    {
        exceptionResponse(MB_FC_READ_REGS, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address
    if ((startreg+numregs) > modbus.holding_size)
    {
        exceptionResponse(MB_FC_READ_REGS, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

	//calculate the query reply message length
	//for each register queried add 2 bytes
	mb_frame_len = 3 + (numregs * 2);
    if (mb_frame_len > MAX_MB_FRAME)
    {
        //Response message is too big for this device
        exceptionResponse(MB_FC_READ_REGS, MB_EX_SLAVE_FAILURE);
        return;
    }

    //Clean frame buffer (leave only SlaveID)
    for (int i = 1; i < mb_frame_len; i++) mb_frame[i] = 0;

    mb_frame[1] = MB_FC_READ_REGS;
    mb_frame[2] = mb_frame_len - 3;   //byte count

    uint16_t val;
    uint16_t i = 0;
	while(numregs--) 
    {
        //retrieve the value from the register bank for the current register
        val = modbus.holding[startreg + i];
        //write the high byte of the register value
        mb_frame[3 + (i * 2)]  = val >> 8;
        //write the low byte of the register value
        mb_frame[4 + (i * 2)] = val & 0xFF;
        i++;
	}
}

void writeSingleRegister(uint16_t reg, uint16_t value)
{
    if (reg > (modbus.holding_size - 1)) 
    {
        exceptionResponse(MB_FC_WRITE_REG, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    modbus.holding[reg] = value;
}

void writeMultipleRegisters(uint16_t startreg, uint16_t numoutputs, uint8_t bytecount)
{
    //Check value
    if (numoutputs < 0x0001 || numoutputs > 0x007B || bytecount != 2 * numoutputs) 
    {
        exceptionResponse(MB_FC_WRITE_REGS, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address (startreg...startreg + numregs)
    if ((startreg + numoutputs) > modbus.holding_size)
    {
        exceptionResponse(MB_FC_WRITE_REGS, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //Prepare answer frame buffer
	mb_frame_len = 6;
    mb_frame[1] = MB_FC_WRITE_REGS;
    mb_frame[2] = startreg >> 8;
    mb_frame[3] = startreg & 0x00FF;
    mb_frame[4] = numoutputs >> 8;
    mb_frame[5] = numoutputs & 0x00FF;

    uint16_t val;
    uint16_t i = 0;
	while(numoutputs--) 
    {
        val = (uint16_t)mb_frame[7+i*2] << 8 | (uint16_t)mb_frame[8+i*2];
        modbus.holding[startreg + i] = val;
        i++;
	}
}

void exceptionResponse(uint16_t fcode, uint16_t excode)
{
    //Clean frame buffer (leave only SlaveID)
    mb_frame_len = 3;
    for (int i = 0; i < mb_frame_len; i++) mb_frame[i] = 0;
    mb_frame[0] = modbus.slaveid;
    mb_frame[1] = fcode + 0x80;
    mb_frame[2] = excode;
}

void readCoils(uint16_t startreg, uint16_t numregs)
{
    //Check value (numregs)
    if (numregs < 0x0001 || numregs > 0x07D0) 
    {
        exceptionResponse(MB_FC_READ_COILS, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address
    if (startreg + numregs > modbus.coils_size) 
    {
        exceptionResponse(MB_FC_READ_COILS, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //Determine the message length = slaveid + function type + byte count and
	//for each group of 8 registers the message length increases by 1
	mb_frame_len = 3 + numregs/8;
	if (numregs%8) mb_frame_len++; //Add 1 to the message length for the partial byte.
    if (mb_frame_len > MAX_MB_FRAME)
    {
        //Response message is too big for this device
        exceptionResponse(MB_FC_READ_COILS, MB_EX_SLAVE_FAILURE);
        return;
    }
    
    //Clean frame buffer (leave only SlaveID)
    for (int i = 1; i < mb_frame_len; i++) mb_frame[i] = 0;

    mb_frame[1] = MB_FC_READ_COILS;
    mb_frame[2] = mb_frame_len - 3; //byte count (mb_frame_len - slave id, function code and byte count)

    uint8_t bitn = 0;
    uint16_t totregs = numregs;
    uint16_t i;
	while (numregs) 
    {
        i = (totregs - numregs--) / 8;
		if (get_discrete((uint8_t)startreg, COILS))
			bitSet(mb_frame[3+i], bitn);
		else
			bitClear(mb_frame[3+i], bitn);
        
		//increment the bit index
		bitn++;
		if (bitn == 8) bitn = 0;
		//increment the register
		startreg++;
	}
}

void readInputStatus(uint16_t startreg, uint16_t numregs)
{
    //Check value (numregs)
    if (numregs < 0x0001 || numregs > 0x07D0) 
    {
        exceptionResponse(MB_FC_READ_INPUT_STAT, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address
    if ((startreg + numregs) > modbus.input_status_size)
    {
        exceptionResponse(MB_FC_READ_INPUT_STAT, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //Determine the message length = function type, byte count and
    //for each group of 8 registers the message length increases by 1
    mb_frame_len = 3 + numregs/8;
    if (numregs%8) mb_frame_len++; //Add 1 to the message length for the partial byte.
    if (mb_frame_len > MAX_MB_FRAME)
    {
        //Response message is too big for this device
        exceptionResponse(MB_FC_READ_INPUT_STAT, MB_EX_SLAVE_FAILURE);
        return;
    }

    //Clean frame buffer (leave only SlaveID)
    for (int i = 1; i < mb_frame_len; i++) mb_frame[i] = 0;

    mb_frame[1] = MB_FC_READ_INPUT_STAT;
    mb_frame[2] = mb_frame_len - 3;

    byte bitn = 0;
    uint16_t totregs = numregs;
    uint16_t i;
    while (numregs) 
    {
        i = (totregs - numregs--) / 8;
        if (get_discrete(startreg, INPUTSTATUS))
        bitSet(mb_frame[3+i], bitn);
        else
        bitClear(mb_frame[3+i], bitn);
        //increment the bit index
        bitn++;
        if (bitn == 8) bitn = 0;
        //increment the register
        startreg++;
    }
}

void readInputRegisters(uint16_t startreg, uint16_t numregs)
{
    //Check value (numregs)
    if (numregs < 0x0001 || numregs > 0x007D) 
    {
        exceptionResponse(MB_FC_READ_INPUT_REGS, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address
    if ((startreg + numregs) > modbus.input_regs_size) 
    {
        exceptionResponse(MB_FC_READ_INPUT_REGS, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //calculate the query reply message length
    //for each register queried add 2 bytes
    mb_frame_len = 3 + (numregs * 2);
    if (mb_frame_len > MAX_MB_FRAME)
    {
        //Response message is too big for this device
        exceptionResponse(MB_FC_READ_INPUT_REGS, MB_EX_SLAVE_FAILURE);
        return;
    }

    //Clean frame buffer (leave only SlaveID)
    for (int i = 1; i < mb_frame_len; i++) mb_frame[i] = 0;

    mb_frame[1] = MB_FC_READ_INPUT_REGS;
    mb_frame[2] = mb_frame_len - 3;

    uint16_t val;
    uint16_t i = 0;
    while(numregs--) 
    {
        //retrieve the value from the register bank for the current register
        val = modbus.input_regs[startreg + i];
        //write the high byte of the register value
        mb_frame[3 + (i * 2)]  = val >> 8;
        //write the low byte of the register value
        mb_frame[4 + (i * 2)] = val & 0xFF;
        i++;
    }
}

void writeSingleCoil(uint16_t reg, uint16_t status)
{
    //Check value (status)
    if (status != 0xFF00 && status != 0x0000)
    {
        exceptionResponse(MB_FC_WRITE_COIL, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address
    if (reg > (modbus.coils_size - 1))
    {
        exceptionResponse(MB_FC_WRITE_COIL, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //Execute
    write_discrete(reg, COILS, status == 0xFF00 ? true : false);
}

void writeMultipleCoils(uint16_t startreg, uint16_t numoutputs, uint16_t bytecount)
{
    //Check value
    uint8_t bytecount_calc = numoutputs / 8;
    if (numoutputs%8) bytecount_calc++;
    if (numoutputs < 0x0001 || numoutputs > 0x07B0 || bytecount != bytecount_calc) 
    {
        exceptionResponse(MB_FC_WRITE_COILS, MB_EX_ILLEGAL_VALUE);
        return;
    }

    //Check Address (startreg...startreg + numregs)
    if ((startreg + numoutputs) > modbus.coils_size)
    {
        exceptionResponse(MB_FC_WRITE_COILS, MB_EX_ILLEGAL_ADDRESS);
        return;
    }

    //Prepare answer frame buffer
	mb_frame_len = 6;
    mb_frame[1] = MB_FC_WRITE_COILS;
    mb_frame[2] = startreg >> 8;
    mb_frame[3] = startreg & 0x00FF;
    mb_frame[4] = numoutputs >> 8;
    mb_frame[5] = numoutputs & 0x00FF;

    //Execute
    uint8_t bitn = 0;
    uint16_t totoutputs = numoutputs;
    uint16_t i;
    while (numoutputs) 
    {
        i = (totoutputs - numoutputs--) / 8;
        write_discrete(startreg, COILS, bitRead(mb_frame[7+i], bitn));
        //increment the bit index
        bitn++;
        if (bitn == 8) bitn = 0;
        //increment the register
        startreg++;
    }
}

uint16_t calcCrc() 
{
    uint8_t CRCHi = 0xFF, CRCLo = 0x0FF, Index;

    int i = 0;
    Index = CRCHi ^ mb_frame[i];
    CRCHi = CRCLo ^ _auchCRCHi[Index];
    CRCLo = _auchCRCLo[Index];
    i++;

    while (i < (mb_frame_len - 2))
    {
        Index = CRCHi ^ mb_frame[i];
        i++;
        CRCHi = CRCLo ^ _auchCRCHi[Index];
        CRCLo = _auchCRCLo[Index];
    }

    return ((uint16_t)CRCHi << 8) | (uint16_t)CRCLo;
}