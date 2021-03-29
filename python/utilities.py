def lo8(x):
    return x & 0xff


def hi8(x):
    return x >> 8


def lo4(x):
    return x & 0xf


def hi4(x):
    return x >> 4


def _bv(bit):
    return 1 << bit


def reverse_bits(byte):
    byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    return byte


def bytes_to_hex(nbytes):
    """
    :param nbytes
    This script will print out a byte array in a human readable format 
    (hexadecimal). This is often useful during debugging. 
    """
    return '[{}]'.format(', '.join(hex(x) for x in nbytes))


def temp_k_to_c(temp_k):
    temp_c = temp_k-273.15
    return temp_c


def temp_k_to_f(temp_k):
    temp_f = (temp_k*1.8 - 459.67)
    return temp_f


def temp_f_to_k(temp_f):
    temp_k = (temp_f + 459.67)*.555556
    return temp_k


def getbytes_from_reg_bits(kwargs, reg_dict):
    write_bytes = 0x0000
    for kword in kwargs:
        found = False
        for item in reg_dict:
            if item["NAME"] == kword:
                name = item["NAME"]
                value = int(kwargs[name])
                shift = item["SHIFT"]
                mask = item["MASK"]
                write_bytes = write_bytes | ((value & mask) << shift)
                found = True
        if not found:
            import ipdb; ipdb.set_trace()
            raise KeyError("unknown field name %s for register fields %s" % (kword, [f['NAME'] for f in reg_dict]))

    return write_bytes
