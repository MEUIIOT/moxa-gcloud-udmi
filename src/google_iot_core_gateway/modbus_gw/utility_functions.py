import binascii
import struct


def hexlify(data):
    # Check input object type should be byte
    if type(data) == bytes:
        return binascii.hexlify(data)
    else:
        return False


def word2int(data):
    # return int
    if type(data) == bytes:
        output = struct.unpack(">H", data)
        return output[0]
    else:
        return False


def int2word(data):
    # return int
    if type(data) == int:
        output = struct.pack(">H", data)
        return output[0]
    else:
        return False


def mybyte2int(data):
    # return int
    if type(data) == int:
        output = struct.unpack(">B", data)
        return output[0]
    else:
        return False
