# This file is part of OpenPLC Runtime
#
# Copyright (C) 2023 Autonomy
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see <http://www.gnu.org/licenses/>.
#
#

import socket
import struct
import serial
import binascii
from enum import IntEnum
import time

class FunctionCode(IntEnum):
    DEBUG_INFO = 0x41
    DEBUG_SET = 0x42
    DEBUG_GET = 0x43
    DEBUG_GET_LIST = 0x44
    DEBUG_GET_MD5 = 0x45

class DebugResponse(IntEnum):
    SUCCESS = 0x7E
    ERROR_OUT_OF_BOUNDS = 0x81
    ERROR_OUT_OF_MEMORY = 0x82

class RemoteDebugClient:
    # Table of CRC values for high-order byte
    _auchCRCHi = [
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
        0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
        0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40]
    # Table of CRC values for low-order byte
    _auchCRCLo = [
        0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4,
        0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09,
        0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD,
        0x1D, 0x1C, 0xDC, 0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
        0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7,
        0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A,
        0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38, 0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE,
        0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
        0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2,
        0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4, 0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F,
        0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB,
        0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
        0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0, 0x50, 0x90, 0x91,
        0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C,
        0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88,
        0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
        0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80,
        0x40]


    def __init__(self, modbus_type, host='', port=None, serial_port=None, baudrate=19200, slave_id=1):
        self.modbus_type = modbus_type
        self.host = host
        self.port = port
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.transaction_id = 0  # Initialize transaction ID
        self.sock = None # TCP socket
        self.serial = None # Serial port
        self.timeout = 5

    def _increment_transaction_id(self):
        self.transaction_id = (self.transaction_id + 1) % 65536

    def _calculate_crc(self, message):
        CRCHi = 0xFF
        CRCLo = 0xFF

        for byte in message:
            index = CRCHi ^ byte
            CRCHi = CRCLo ^ self._auchCRCHi[index]
            CRCLo = self._auchCRCLo[index]

        return (CRCHi << 8) | CRCLo

    def _assemble_request(self, function_code, data):
        if self.modbus_type == 'TCP':
            self._increment_transaction_id()
            transaction_id = self.transaction_id
            protocol_id = 0  # Modbus protocol ID is always 0x0000
            slave_id = self.slave_id

            # Construct the Modbus TCP frame
            header = struct.pack(">HHHBB", transaction_id, protocol_id, 2 + len(data), slave_id, function_code)
            request = header + data

        elif self.modbus_type == 'RTU':
            slave_id = self.slave_id

            # Construct the Modbus RTU frame without CRC
            #print("Assembling request with fc {}".format(str(function_code)))
            #header = 
            #request = bytes([slave_id, function_code]) + data
            request = struct.pack('>BB', slave_id, function_code) + data


        else:
            print("Unsupported Modbus type.")
            return None

        return request

    def send_debug_info_query(self):
        data = struct.pack(">BBBB", 0, 0, 0, 0)  # Dummy data - Modbus TCP parser requires messages with at least 6 bytes of data
        return self._send_modbus_request(FunctionCode.DEBUG_INFO, data)
    
    def send_debug_set_query(self, varidx, flag, value, var_type):
        if flag == False:
            data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 1) + struct.pack(">B", 0)
        else:
            if var_type in ['BOOL', 'STEP', 'TRANSITION', 'ACTION', 'SINT', 'USINT', 'BYTE']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 1) + struct.pack(">B", int(value))
            elif var_type in ['INT', 'UINT', 'WORD']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 2) + struct.pack(">h", value)
            elif var_type in ['DINT', 'UDINT', 'DWORD']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 4) + struct.pack(">i", value)
            elif var_type in ['LINT', 'ULINT', 'LWORD']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 8) + struct.pack(">q", value)
            elif var_type in ['REAL']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 4) + struct.pack(">f", value)
            elif var_type in ['LREAL']:
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", 8) + struct.pack(">d", value)
            elif var_type == 'STRING':
                # For strings, serialize the length and the string itself
                data = struct.pack(">H", varidx) + struct.pack(">B", flag) + struct.pack(">H", len(value)) + value
            else:
                # Handle unsupported data types or raise an error if needed
                #raise TypeError("Unsupported data type: {}".format(type(value)))
                print("Unsupported data type: {}".format(var_type))
        
        return self._send_modbus_request(FunctionCode.DEBUG_SET, data)

    def send_debug_get_query(self, startidx, endidx):
        data = struct.pack(">HH", startidx, endidx)
        return self._send_modbus_request(FunctionCode.DEBUG_GET, data)
    
    def send_debug_get_list_query(self, num_indexes, index_array):
        if len(index_array) != num_indexes:
            print("Invalid index array length.")
            return None

        #data = struct.pack(f">H{num_indexes}H", num_indexes, *index_array)
        data = struct.pack(">H{}H".format(num_indexes), num_indexes, *index_array)
        return self._send_modbus_request(FunctionCode.DEBUG_GET_LIST, data)
    
    def get_md5_hash(self):
        endianness_check = 0xDEAD
        # Pack the fixed value as a 16-bit unsigned short in big-endian byte order
        # along with two extra dummy bytes to satisfy Modbus minimum packet size
        data = struct.pack(">HBB", endianness_check, 0, 0)
        res = self._send_modbus_request(FunctionCode.DEBUG_GET_MD5, data)
        
        # Check if response is valid
        if res == None or len(res) < 10:
            print("Error: Invalid response while fetching MD5 hash")
            return None
        
        response_code = struct.unpack('>B', res[8:9])[0]  # Unpack the response code as a byte
        
        if response_code != DebugResponse.SUCCESS:
            print("Error: Invalid response code while fetching MD5 hash")
            return None
        
        md5_hash = res[9:].decode('utf-8')
        return md5_hash

    def _send_modbus_request(self, function_code, data):
        request = self._assemble_request(function_code, data)
        if self.modbus_type == 'RTU':
            # Add CRC for Modbus RTU
            #crc = binascii.crc_hqx(data, 0xFFFF)
            crc = self._calculate_crc(request)

            #crc_bytes = crc.to_bytes(2, 'big')
            crc_bytes = struct.pack('>H', crc)  # Convert crc to bytes using struct.pack
            request += crc_bytes

        
        return self._send_request(request)
        
    def _send_request(self, request):
        try:
            if self.modbus_type == 'TCP':
                if not self.sock:
                    #raise Exception("Not connected.")
                    print("Device is not connected")
                    return None

                
                self.sock.send(request)
                response = self.sock.recv(1024)
                return response

            elif self.modbus_type == 'RTU':
                if not self.serial:
                    #raise Exception("Not connected.")
                    print("Device is not connected")
                    return None

                #if should_print == True:
                #    print('request:')
                #    res_hex = ' '.join([hex(ord(byte))[2:].zfill(2) for byte in request])
                #    print(res_hex)

                ## Wait until timeout for the response to arrive
                #start_time = time.time()
                #
                #while (time.time() - start_time) < self.timeout:
                #    if self.serial.in_waiting >= expected_response_length:
                #        response = self.serial.read(expected_response_length)
                #        return response
                #
                ## If no response is received within the timeout, return an empty string
                #return ''

                self.serial.write(request)
                response = self.serial.read(1024)
                if response == None or len(response) < 2:
                    return None
                
                # TCP header is bigeer. Pad serial response 6 bytes to the right so that it matches TCP response
                inserted_bytes = b'\x00\x00\x00\x00\x00\x00'
                response = inserted_bytes + response
                # Remove the last two bytes (CRC)
                response = response[:-2]
                return response

            else:
                print("Unsupported Modbus type.")
                return None

        except Exception as e:
            #print(f"Error sending request: {str(e)}")
            print("Error sending request: {}".format(str(e)))
            print("Trying to reconnect...")
            self.disconnect()
            self.connect()
            return None

    def connect(self):
        if self.modbus_type == 'TCP':
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                self.sock.connect((self.host, self.port))
                time.sleep(1) #make sure connection happens
            except Exception as e:
                #print(f"TCP connection error: {str(e)}")
                print("TCP connection error: {}\n".format(str(e)))
                return False

        elif self.modbus_type == 'RTU':
            try:
                self.serial = serial.Serial(port=self.serial_port, baudrate=self.baudrate, timeout=0.03)
                time.sleep(2) #make sure connection happens
            except Exception as e:
                #print(f"Serial port connection error: {str(e)}")
                print("Serial port connection error: {}".format(str(e)))
                return False
        
        return True

    def disconnect(self):
        if self.modbus_type == 'TCP':
            if self.sock:
                self.sock.close()
                self.sock = None

        elif self.modbus_type == 'RTU':
            if self.serial:
                self.serial.close()
                self.serial = None
