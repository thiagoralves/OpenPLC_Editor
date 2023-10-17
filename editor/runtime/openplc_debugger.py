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
from time import sleep

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

    def _increment_transaction_id(self):
        self.transaction_id = (self.transaction_id + 1) % 65536

    def _calculate_crc(self, message):
        crc = 0xFFFF
        for byte in message:
            crc ^= ord(byte)
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1

        return crc

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

    def send_debug_set_query(self, varidx, flag, value):
        data = struct.pack(">HBH", varidx, flag, len(value)) + value
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
        data = struct.pack(">BBBB", 0, 0, 0, 0)  # Dummy data - Modbus TCP parser requires messages with at least 6 bytes of data
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
                    raise Exception("Not connected.")
                
                self.sock.send(request)
                response = self.sock.recv(1024)
                return response

            elif self.modbus_type == 'RTU':
                if not self.serial:
                    raise Exception("Not connected.")

                print('request:')
                res_hex = ' '.join([hex(ord(byte))[2:].zfill(2) for byte in request])
                print(res_hex)
                self.serial.write(request)
                response = self.serial.read(1024)
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
                self.sock.settimeout(5)
                self.sock.connect((self.host, self.port))
                sleep(1) #make sure connection happens
            except Exception as e:
                #print(f"TCP connection error: {str(e)}")
                print("TCP connection error: {}\n".format(str(e)))
                return False

        elif self.modbus_type == 'RTU':
            try:
                self.serial = serial.Serial(port=self.serial_port, baudrate=self.baudrate, timeout=5)
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