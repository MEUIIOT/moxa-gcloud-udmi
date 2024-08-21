
# This software is licensed under GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

import os 
import json
import logging
import queue
import struct
import math
from google_iot_core_gateway.modbus_gw.utility_functions import hexlify
from google_iot_core_gateway import __version__ as version, ROOT_DIR

logger = logging.getLogger(__name__)

def is_even(number):
    return number % 2 == 0


def _get_dbo_properties(dict, register_address):
    dbo_properties = dict[str(register_address)]
    total_registers = dbo_properties['number_of_registers']
    total_bytes = dbo_properties['number_of_registers'] * 2
    data_format = dbo_properties['format']
    return total_registers, total_bytes, data_format


def _get_nested_key_value_pairs(data, parent_key=''):
    items = []
    if isinstance(data, dict):
        for key, value in data.items():
            #full_key = f"{parent_key}.{key}" if parent_key else key
            full_key = f"{key}" if parent_key else key
            if isinstance(value, dict):
                items.append((full_key, value))
                items.extend(_get_nested_key_value_pairs(value, full_key))
            elif isinstance(value, list):
                items.extend(_get_nested_key_value_pairs(value, full_key))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            full_key = f"{parent_key}[{index}]"
            if isinstance(value, dict):
                items.append((full_key, value))
                items.extend(_get_nested_key_value_pairs(value, full_key))
            elif isinstance(value, list):
                items.extend(_get_nested_key_value_pairs(value, full_key))
    return items

def get_register_offset(register_address, starting_address, total_bytes):
    """
    Example from PM5111
    "3000": {
        "dbo_name": "line1_current_sensor",
        "number_of_registers": 2,
        "format": "float32",
        "units": "Amperes"
        
    Example: register address = 3000 (address from the meter definition definition file example PM5111)
             starting address = 2999 (address recieved from incoming RTU Request)
             start_index = (3000 - 2999) => 1 * 2
             total_bytes = n * 2     (multiply by 2 in order to get total num of bytes, since each register 
                                      in RTU response is paired with 2 bytes)
                                     (where n is total number of register given the meter definition file example PM5111)             
             end_index = 2 * total_bytes  
           
    """           
    start_index = ((register_address-starting_address) * 2)-2
    end_index = start_index + total_bytes
    logger.debug("START_BYTE_Index: {} END_BYTE_INDEX: {}".format(start_index, end_index))
    return start_index, end_index


def _read_ext_config(directory, filename, config_file=None):
    """
    Configuration
    ROOT_DIR = /home/moxa/moxa-gcloud-udmi
    resources_path = /home/moxa-gcloud-udmi/resources/modbus_dbo_maps
    """
    if config_file is None:
        resources_path = os.path.join(ROOT_DIR, directory)
        if os.path.isdir(resources_path):
            config_file = os.path.join(resources_path, filename)
        else:
            config_file = os.path.join(ROOT_DIR, filename)        
    try:
        with open(config_file) as json_data_file:
            cfg_obj = json.load(json_data_file)
            return cfg_obj
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Invalid path to the config file: {config_file}")
        logger.error(e)
        return None


def map_modbus_slave_to_type(ext_conf):
    """
    The new dictionary, transformed_dict, uses the modbus_slave_id as the key and the type as the value.
    RETURN: transformed_dict: {'1': 'PM5561', '2': 'PM5111'}
    """
    try:
        if ext_conf["site_details"]["proxy_ids"]:
            site_details_devices = ext_conf["site_details"]["proxy_ids"]
            logger.debug("site_details_devices: {}".format(site_details_devices))
            # Transform the dictionary
            transformed_dict = {}
            for device, details in site_details_devices.items():
                #modbus_id = str(details['modbus_slave_id'])
                modbus_id =  details['modbus_slave_id']
                device_type = details['type']
                transformed_dict[modbus_id] = device_type
            # Output the transformed dictionary
            logger.debug("site_details_devices: {}".format(transformed_dict))
            return transformed_dict
    except:
        pass


def modbus_to_json(rtu_request, rtu_response):
    logger.debug("rtu_request: {}, rtu_response {}".format(rtu_request, rtu_response))
    
    function_code = rtu_request[1]

    if function_code in (0x03, 0x04):
        return build_fc3_fc4_payload(rtu_request, rtu_response)
    else:
        logger.error(f"Not Implement! Modbus to JSON parsing for function code: {function_code}")
        return None


def build_fc3_fc4_payload(rtu_request, rtu_response) -> str:
    """Build and return json payload for FC3, FC4

    Structure of request and response is the same for both FC3 andd FC4:

    6.3 03 (0x03) Read Holding Registers
    ====================================
    This function code is used to read the contents of a contiguous block of holding registers in a
    remote device. The Request PDU specifies the starting register address and the number of
    registers. In the PDU Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    The register data in the response message are packed as two bytes per register, with the
    binary contents right justified within each byte. For each register, the first byte contains the
    high order bits and the second contains the low order bits.
        Request
            Function code 1 Byte 0x03
            Starting Address 2 Bytes 0x0000 to 0xFFFF
            Quantity of Registers 2 Bytes 1 to 125 (0x7D)
        Response
            Function code 1 Byte 0x03
            Byte count 1 Byte 2 x N*
            Register value N* x 2 Bytes
                *N = Quantity of Registers
        Error
            Error code 1 Byte 0x83
            Exception code 1 Byte 01 or 02 or 03 or 04


    6.4 04 (0x04) Read Input Registers
    ==================================
    This function code is used to read from 1 to 125 contiguous input registers in a remote device.
    The Request PDU specifies the starting register address and the number of registers. In the
    PDU Registers are addressed starting at zero. Therefore input registers numbered 1-16 are
    addressed as 0-15.
    The register data in the response message are packed as two bytes per register, with the
    binary contents right justified within each byte. For each register, the first byte contains the
    high order bits and the second contains the low order bits.
        Request
            Function code 1 Byte 0x04
            Starting Address 2 Bytes 0x0000 to 0xFFFF
            Quantity of Input Registers 2 Bytes 0x0001 to 0x007D
        Response
            Function code 1 Byte 0x04
            Byte count 1 Byte 2 x N*
            Input Registers N* x 2 Bytes
                *N = Quantity of Input Registers
        Error
            Error code 1 Byte 0x84
            Exception code 1 Byte 01 or 02 or 03 or 04
    """

    slave_id, function_code, starting_address, quantity_of_registers = struct.unpack('>BBHH', rtu_request[:6])
    logger.debug("req_slave_id: {} req_function_code:{} start_address:{} quantity:{}".format(
    slave_id, function_code, starting_address, quantity_of_registers))

    assert function_code in (0x03, 0x04)

    payload = {'slave_id': slave_id,
               "fc": function_code,
               'data': None, 
               'error': None
               }

    # check if there is error rtu_response
    if isinstance(rtu_response, Exception):
        payload['error'] = str(rtu_response)
        logger.debug("build_modbus_to_json: {}".format(payload))
        return json.dumps(payload)
    elif rtu_response is None:
        payload['error'] = "Unknown error"
        logger.debug("build_modbus_to_json: {}".format(payload))
        return json.dumps(payload)

    resp_slave_id, resp_function_code, byte_count = struct.unpack('>BBB', rtu_response[:3])
    logger.debug("resp_slave_id: {} resp_function_code:{} byte_count:{}".format(resp_slave_id, resp_function_code, byte_count))

    if not all((slave_id == resp_slave_id,
                function_code == resp_function_code,
                byte_count == quantity_of_registers * 2,
                # 3 byte header, the registers, 2 byte CRC
                len(rtu_response) == 3 + byte_count + 2)):
        # TODO: response was received but is invalid, should it be reported to UDMI?
        logger.error('Invalid payload')
        return None
    
    """
    The code accounts for three different meter types, PM5111, PM5561 and PM8240 
    each of which has a distinct slave ID. This means the function is 
    set up to handle and differentiate between these two types based on their unique slave IDs
    
    It examines the slave ID obtained from an RTU response returned from energy meter
    It compares this RTU response slave ID with the slave ID specified in the 
    config-google-gateway.json configuration file.

    Return a Dictionary:

    If the IDs Match: The function returns a dictionary where the key is the slave ID 
    and the value is the meter definition associated with that slave ID.

    """
    ext_conf = _read_ext_config('resources', "config-google-gateway.json") 
    site_devices = map_modbus_slave_to_type(ext_conf)
    
    if resp_slave_id in site_devices:
        meter_type = site_devices[resp_slave_id]
       
        data = _read_ext_config('resources/modbus_dbo_maps', meter_type + '.json')
        
        # Get nested key-value pairs from the JSON object
        nested_key_value_pairs = _get_nested_key_value_pairs(data)
        temp_dict = {}
        for key, value in nested_key_value_pairs:
            #print(f"{key}: {value}")
            temp_dict[key] = value
    else:
        logger.error("[ERROR] Response Slave ID {} not available in site_details in config-google-gateway.json".format(resp_slave_id))
        #exit()
        return

    # unpack quantity_of_registers of 2-byte big-endian values
    registers = struct.unpack('>' + 'H' * quantity_of_registers, rtu_response[3:3 + byte_count])
    rtu_response_bytes = rtu_response[3:-2]
    

    """
    The following code increase the register address by +1 from starting address recieved in rtu request. 
    Once the register address found in the temp_dict object that has keys representing the register addresses
    as per meter definiation files PM5111, PM5561 and PM8240    
    """    
    data_dict = {}
    for register_address, register_value in enumerate(registers, starting_address):
         """
         The following if statement will be executed to solve the problem of recieving rtu request 
         with starting address is odd sequence Example: 2999, 3203. The idea is skip the odd starting 
         register address
         """
         if str(register_address) in temp_dict.keys() and is_even(register_address):
            total_registers, total_bytes, format = _get_dbo_properties(temp_dict, register_address)
            start_index, end_index = get_register_offset(register_address, starting_address, total_bytes)
            byte_value = rtu_response_bytes[start_index:end_index]
            
            logger.debug("register_addres: {} Original byte value {}: Original hex value {}:  byte_length: {}".format(
            register_address, rtu_response_bytes[start_index:end_index], 
            (rtu_response_bytes[start_index:end_index]).hex(),
            len(rtu_response_bytes[start_index:end_index])))
            
            # The following code is valid for all float32 registers 3000 to 3084 and 3110 
            if format == "float32" and total_bytes == len(byte_value):
               # Unpack the bytes as a float32 big endian value
               float_value = struct.unpack('>f',  byte_value)[0]
               logger.debug("big endian float32 value: {}".format(float_value))
               if math.isnan(float_value):
                  logger.debug("The value {} is Not Applicable because it is not a number".format(float_value))
                  hex_value = rtu_response_bytes[start_index:end_index].hex()
                  data_dict[register_address] = "N/A(" + str(hex_value) +")"
               else:  
                   data_dict[register_address] = float_value
             
            elif format == "float32" and total_bytes != len(byte_value):
                 logger.error("[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes))
                 data_dict[register_address] = "[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes)
            
            # The following code is for 3216, 3232
            if format == "int64" and total_bytes == len(byte_value):
                 # Unpack the bytes as an int64 (big-endian format)
                 int_value = struct.unpack('>q', byte_value)[0]
                 logger.debug("big endian int64 value: {}".format(int_value))
                 data_dict[register_address] = int_value
                 
            elif format == "int64" and total_bytes != len(byte_value):
                 logger.error("[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes))
                 data_dict[register_address] = "[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes)
         
            # The following code is for 130
            if format == "int32u" and total_bytes == len(byte_value):
                 # Unpack the bytes as an int32 (big-endian format)
                 int_value = struct.unpack('>I', byte_value)[0]
                 logger.debug("big endian 32-bit integer unsigned value: {}".format(int_value))
                 data_dict[register_address] = int_value
         
            elif format == "int32u" and total_bytes != len(byte_value):
                 print("[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes))
                 data_dict[register_address] = "[ERROR]. Received ({}) bytes not equal to expected bytes length ({}) as per meter definition file".format(len(byte_value), total_bytes)
         
         
         #The following code is valid for sequence that starts with odd series for example 1637
         # for register starting address 1636  
         else:         
            if str(register_address + 1) in temp_dict.keys():
                total_registers, total_bytes, format = _get_dbo_properties(temp_dict, register_address + 1)
                start_index, end_index = get_register_offset(register_address+1, starting_address, total_bytes)
                byte_value = rtu_response_bytes[start_index:end_index]
                if format == "int16u" and total_bytes == len(byte_value):
                    # Unpack the bytes as an int16u (big-endian format)
                    #int_value = struct.unpack('>H', rtu_response_bytes)[0]
                    int_value = struct.unpack('>H', byte_value)[0]
                    logger.debug("big endian 16-bit integer unsigned value: {}".format(int_value))
                    data_dict[register_address + 1] = register_value
         
               
    payload['data'] = data_dict   
    logger.debug(f"build_fc3_fc4_payload: {payload}")
    return json.dumps(payload)
