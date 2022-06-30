/*
ModbusSerial.cpp - Source for Modbus Serial Library
Copyright (C) 2014 Andre Sarmento Barbosa

  Note: This library was expanded to also support
  Modbus IP through Ethernet and WiFi
  Copyright (C) 2021 OpenPLC
*/
#include "ModbusSerial.h"

// To use CONTROLLINO RS485 interface API
#if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
#include "Controllino.h"
#endif

#ifdef MBTCP
ModbusSerial::ModbusSerial():_server(502) {

}
#else
ModbusSerial::ModbusSerial() {

}
#endif

bool ModbusSerial::setSlaveId(byte slaveId){
  _slaveId = slaveId;
  return true;
}

byte ModbusSerial::getSlaveId() {
  return _slaveId;
}

#ifndef DEBUG_MODE
bool ModbusSerial::config(HardwareSerial* port, long baud, int txPin) {
  this->_port = port;
  this->_txPin = txPin;
  (*port).begin(baud);

  if (txPin >= 0) {
    pinMode(txPin, OUTPUT);
    digitalWrite(txPin, LOW);
  }

  #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
  if (_port == &Serial3) { // RS485 serial port
    Controllino_RS485Init();
  }
  #endif

  // Modbus states that a baud rate higher than 19200 must use a fixed 750 us
  // for inter character time out and 1.75 ms for a frame delay for baud rates
  // below 19200 the timing is more critical and has to be calculated.
  // E.g. 9600 baud in a 11 bit packet is 9600/11 = 872 characters per second
  // In milliseconds this will be 872 characters per 1000ms. So for 1 character
  // 1000ms/872 characters is 1.14583ms per character and finally modbus states
  // an inter-character must be 1.5T or 1.5 times longer than a character. Thus
  // 1.5T = 1.14583ms * 1.5 = 1.71875ms. A frame delay is 3.5T.
  // Thus the formula is T1.5(us) = (1000ms * 1000(us) * 1.5 * 11bits)/baud
  // 1000ms * 1000(us) * 1.5 * 11bits = 16500000 can be calculated as a constant

  if (baud > 19200)
  _t15 = 750;
  else
  _t15 = 16500000/baud; // 1T * 1.5 = T1.5

  /* The modbus definition of a frame delay is a waiting period of 3.5 character times
  between packets. This is not quite the same as the frameDelay implemented in
  this library but does benifit from it.
  The frameDelay variable is mainly used to ensure that the last character is
  transmitted without truncation. A value of 2 character times is chosen which
  should suffice without holding the bus line high for too long.*/

  _t35 = _t15 * 3.5;

  return true;
}

/*
#if (!defined(__AVR) && !defined(BOARD_ESP8266) && !defined(BOARD_ESP32)) || defined(__AVR_ATmega32U4__)
bool ModbusSerial::config(Serial_* port, long baud, int txPin) {
    this->_port = port;
    this->_txPin = txPin;
    (*port).begin(baud);
    //while (!(*port));

    if (txPin >= 0) {
      pinMode(txPin, OUTPUT);
      digitalWrite(txPin, LOW);
    }

    if (baud > 19200)
    _t15 = 750;
    else
    _t15 = 16500000/baud; // 1T * 1.5 = T1.5

    _t35 = _t15 * 3.5;

    return true;
  }
#endif
*/
#endif

#ifdef DEBUG_MODE
bool ModbusSerial::config(HardwareSerial* port,
  HardwareSerial* DebugSerialPort, long baud, int txPin) {
    this->_port = port;
    this->_txPin = txPin;
    (*port).begin(baud);

    DebugPort = DebugSerialPort;

    if (txPin >= 0) {
      pinMode(txPin, OUTPUT);
      digitalWrite(txPin, LOW);
    }

    if (baud > 19200)
    _t15 = 750;
    else
    _t15 = 16500000/baud; // 1T * 1.5 = T1.5

    _t35 = _t15 * 3.5;

    return true;
  }
  #endif

  #ifdef USE_SOFTWARE_SERIAL
  bool ModbusSerial::config(SoftwareSerial* port, long baud, int txPin) {
    this->_port = port;
    this->_txPin = txPin;
    (*port).begin(baud);

    delay(2000);

    if (txPin >= 0) {
      pinMode(txPin, OUTPUT);
      digitalWrite(txPin, LOW);
    }

    if (baud > 19200)
    _t15 = 750;
    else
    _t15 = 16500000/baud; // 1T * 1.5 = T1.5

    _t35 = _t15 * 3.5;

    return true;
  }
  #endif
 
 #ifdef MBTCP
 void ModbusSerial::config(uint8_t *mac) {
    #ifdef MBTCP_ETHERNET
    Ethernet.begin(mac);
    #endif
    #ifdef MBTCP_WIFI
    #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    _server.setNoDelay(true);
    #endif;
    WiFi.begin(MBTCP_SSID, MBTCP_PWD);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
    }
    #endif
    _server.begin();
}

void ModbusSerial::config(uint8_t *mac, IPAddress ip) {
    #ifdef MBTCP_ETHERNET
    Ethernet.begin(mac, ip);
    #endif
    #ifdef MBTCP_WIFI
    #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    _server.setNoDelay(true);
    #else
    WiFi.config(ip);
    #endif
    WiFi.begin(MBTCP_SSID, MBTCP_PWD);
    while (WiFi.status() != WL_CONNECTED) 
    {
        delay(500);
    }
    #endif
    _server.begin();
}

void ModbusSerial::config(uint8_t *mac, IPAddress ip, IPAddress dns) {
    #ifdef MBTCP_ETHERNET
    Ethernet.begin(mac, ip, dns);
    #endif
    #ifdef MBTCP_WIFI
    #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    _server.setNoDelay(true);
    #else
    WiFi.config(ip, dns);
    #endif
    WiFi.begin(MBTCP_SSID, MBTCP_PWD);
    while (WiFi.status() != WL_CONNECTED) 
    {
        delay(500);
    }
    #endif
    _server.begin();
}

void ModbusSerial::config(uint8_t *mac, IPAddress ip, IPAddress dns, IPAddress gateway) {
    #ifdef MBTCP_ETHERNET
    Ethernet.begin(mac, ip, dns, gateway);
    #endif
    #ifdef MBTCP_WIFI
    #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    _server.setNoDelay(true);
    #else
    WiFi.config(ip, dns, gateway);
    #endif
    WiFi.begin(MBTCP_SSID, MBTCP_PWD);
    while (WiFi.status() != WL_CONNECTED) 
    {
        delay(500);
    }
    #endif
    _server.begin();
}
 
 void ModbusSerial::config(uint8_t *mac, IPAddress ip, IPAddress dns, IPAddress gateway, IPAddress subnet) {
    #ifdef MBTCP_ETHERNET
    Ethernet.begin(mac, ip, dns, gateway, subnet);
    #endif
    #ifdef MBTCP_WIFI
    #if defined(BOARD_ESP8266) || defined(BOARD_ESP32)
    IPAddress secondaryDNS(8, 8, 8, 8);
    WiFi.config(ip, gateway, subnet, dns, secondaryDNS);
    _server.setNoDelay(true);
    #else
    WiFi.config(ip, dns, gateway, subnet);
    #endif
    WiFi.begin(MBTCP_SSID, MBTCP_PWD);
    while (WiFi.status() != WL_CONNECTED) 
    {
        delay(500);
    }
    #endif
    _server.begin();
}
 #endif

  bool ModbusSerial::receive(byte* frame) {
    //first byte of frame = address
    byte address = frame[0];
    //Last two bytes = crc
    uint16_t crc = ((frame[_len - 2] << 8) | frame[_len - 1]);

    //Slave Check
    if (address != 0xFF && address != this->getSlaveId()) {
      return false;
    }

    //CRC Check
    if (crc != this->calcCrc(_frame[0], _frame+1, _len-3)) {
      return false;
    }

    //PDU starts after first byte
    //framesize PDU = framesize - address(1) - crc(2)
    this->receivePDU(frame+1);
    //No reply to Broadcasts
    if (address == 0xFF) _reply = MB_REPLY_OFF;
    return true;
  }

  bool ModbusSerial::send(byte* frame) {
    byte i;

    if (this->_txPin >= 0) {
      digitalWrite(this->_txPin, HIGH);
      delay(1);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
    if (_port == &Serial3) { // RS485 serial port
      Controllino_RS485TxEnable(); // Enable RS485 chip to transmit 
    }
    #endif

    for (i = 0 ; i < _len ; i++) {
      (*_port).write(frame[i]);
    }

    (*_port).flush();
    delayMicroseconds(_t35);

    if (this->_txPin >= 0) {
      digitalWrite(this->_txPin, LOW);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
    if (_port == &Serial3) { // RS485 serial port
      Controllino_RS485RxEnable(); // Go back to receive mode after transmitted data
    }
    #endif
  }

  bool ModbusSerial::sendPDU(byte* pduframe) {
    if (this->_txPin >= 0) {
      digitalWrite(this->_txPin, HIGH);
      delay(1);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
    if (_port == &Serial3) { // RS485 serial port
      Controllino_RS485TxEnable(); // Enable RS485 chip to transmit 
    }
    #endif

    delayMicroseconds(_t35);

    //Send slaveId
    (*_port).write(_slaveId);

    //Send PDU
    byte i;
    for (i = 0 ; i < _len ; i++) {
      (*_port).write(pduframe[i]);
    }

    //Send CRC
    word crc = calcCrc(_slaveId, _frame, _len);
    (*_port).write(crc >> 8);
    (*_port).write(crc & 0xFF);

    (*_port).flush();
    delayMicroseconds(_t35);

    if (this->_txPin >= 0) {
      digitalWrite(this->_txPin, LOW);
    }

    #if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
    if (_port == &Serial3) { // RS485 serial port
      Controllino_RS485RxEnable(); // Go back to receive mode after transmitted data
    }
    #endif

    #ifdef DEBUG_MODE
    (*DebugPort).println("SENT Serial RESPONSE");
    (*DebugPort).print(_slaveId);
    (*DebugPort).print(':');
    for (int i = 0 ; i < _len ; i++) {
      (*DebugPort).print(_frame[i]);
      (*DebugPort).print(':');
    }
    (*DebugPort).print(crc >> 8);
    (*DebugPort).print(':');
    (*DebugPort).print(crc & 0xFF);
    (*DebugPort).print(':');
    (*DebugPort).println();
    (*DebugPort).println(F("-----------------"));
    #endif
  }

  void ModbusSerial::task() {

    #ifdef MBTCP
    #ifdef MBTCP_ETHERNET
    EthernetClient client = _server.available();
    #endif
    #if defined(MBTCP_WIFI) && !defined(BOARD_ESP8266) && !defined(BOARD_ESP32)
    WiFiClient client = _server.available();
    #endif

    //ESP boards have a slightly different implementation of the WiFi API - therefore their specific
    //code lies below
    #if (defined(BOARD_ESP8266) || defined(BOARD_ESP32)) && defined(MBTCP_WIFI)
    if (_server.hasClient()) {
        for (int i = 0; i < MAX_SRV_CLIENTS; i++) {
            if (!_serverClients[i]) { //equivalent to !serverClients[i].connected()
                _serverClients[i] = _server.available();
                break;
            }
        }
    }

    //search all clients for data
    for (int i = 0; i < MAX_SRV_CLIENTS; i++) {
        int j = 0;
        if (_serverClients[i].connected() && _serverClients[i].available())
        {
            while (_serverClients[i].available()) {
                _MBAP[j] = _serverClients[i].read();
                j++;
                if (j==7) break;  //MBAP length has 7 bytes size
            }
            
            _len = _MBAP[4] << 8 | _MBAP[5];
            _len--;  // Do not count with last byte from MBAP
    
            if (_MBAP[2] !=0 || _MBAP[3] !=0) return;   //Not a MODBUSIP packet
            if (_len > MODBUSIP_MAXFRAME) return;      //Length is over MODBUSIP_MAXFRAME
    
            _frame = (byte*) malloc(_len);
            j = 0;
            while (_serverClients[i].available()) {
                _frame[j] = _serverClients[i].read();
                j++;
                if (j==_len) break;
            }
    
            this->receivePDU(_frame);
            if (_reply != MB_REPLY_OFF) {
                //MBAP
                _MBAP[4] = (_len+1) >> 8;     //_len+1 for last byte from MBAP
                _MBAP[5] = (_len+1) & 0x00FF;
    
                byte sendbuffer[7 + _len];
    
                for (j = 0 ; j < 7 ; j++) {
                    sendbuffer[j] = _MBAP[j];
                }
                //PDU Frame
                for (j = 0 ; j < _len ; j++) {
                    sendbuffer[j+7] = _frame[j];
                }
                _serverClients[i].write(sendbuffer, _len + 7);
            }
    
            free(_frame);
            _len = 0;
        }
    }

    //If this is not an ESP board, then here is the default code
    #else
    if (client) {
        if (client.connected()) {
            int i = 0;
            while (client.available()){
                _MBAP[i] = client.read();
                i++;
                if (i==7) break;  //MBAP length has 7 bytes size
            }
            _len = _MBAP[4] << 8 | _MBAP[5];
            _len--;  // Do not count with last byte from MBAP

            if (_MBAP[2] !=0 || _MBAP[3] !=0) return;   //Not a MODBUSIP packet
            if (_len > MODBUSIP_MAXFRAME) return;      //Length is over MODBUSIP_MAXFRAME

            _frame = (byte*) malloc(_len);
            i = 0;
            while (client.available()){
                _frame[i] = client.read();
                i++;
                if (i==_len) break;
            }

            this->receivePDU(_frame);
            if (_reply != MB_REPLY_OFF) {
                //MBAP
                _MBAP[4] = (_len+1) >> 8;     //_len+1 for last byte from MBAP
                _MBAP[5] = (_len+1) & 0x00FF;

                byte sendbuffer[7 + _len];

                for (i = 0 ; i < 7 ; i++) {
                    sendbuffer[i] = _MBAP[i];
                }
                //PDU Frame
                for (i = 0 ; i < _len ; i++) {
                    sendbuffer[i+7] = _frame[i];
                }
                client.write(sendbuffer, _len + 7);
            }

            free(_frame);
            _len = 0;
        }
    }
    #endif
    #endif
    
    #ifdef MBSERIAL
    _len = 0;
	
	// overflow if len > 255 (len is byte)
    if ((*_port).available() > 0xFF) {
        (*_port).flush(); // flush data
        return;
    }
    if ((*_port).available() == 0) 
        return;
	
    while ((*_port).available() > _len) {
      _len = (*_port).available(); // (len is byte)
      delayMicroseconds(_t15);
    }


    byte i;
    _frame = (byte*) malloc(_len);
    for (i=0 ; i < _len ; i++) _frame[i] = (*_port).read();

    #ifdef DEBUG_MODE
    (*DebugPort).println(F("GOT Serial CMD"));
    for (int i=0 ; i < _len ; i++) {
      (*DebugPort).print(_frame[i], DEC);
      (*DebugPort).print(":");
      //(*DebugPort).println(sendbuffer[i], HEX);
    }
    (*DebugPort).println();
    (*DebugPort).println(F("-----------------"));
    #endif

    if (_len > 3) { // ignore data receiver, if len <= 3
        if (this->receive(_frame)) {
            if (_reply == MB_REPLY_NORMAL)
                this->sendPDU(_frame);
            else
                if (_reply == MB_REPLY_ECHO)
                    this->send(_frame);
        }
    }

    free(_frame);
    _len = 0;
    #endif
}

  word ModbusSerial::calcCrc(byte address, byte* pduFrame, byte pduLen) {
    byte CRCHi = 0xFF, CRCLo = 0x0FF, Index;

    Index = CRCHi ^ address;
    CRCHi = CRCLo ^ _auchCRCHi[Index];
    CRCLo = _auchCRCLo[Index];

    while (pduLen--) {
      Index = CRCHi ^ *pduFrame++;
      CRCHi = CRCLo ^ _auchCRCHi[Index];
      CRCLo = _auchCRCLo[Index];
    }

    return (CRCHi << 8) | CRCLo;
  }
