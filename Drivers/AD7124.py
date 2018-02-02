import Gbl
import utilities
from AD7124_Reg_Addresses import RegAddrs
from AD7124_Reg_bits import RegBits

_DUMMY_BYTE = 0xff
_READ_FLAG = 0b01000000


def read_reg(regID):
    """
     * @brief Reads a register of the AD7124
     * @param  address - address of the register
     * @return value of the register
    """
    regID |= _READ_FLAG
    bytelist = []
    bytelist.append(regID)
    bytelist.append(_DUMMY_BYTE)
    print(utilities. BytesToHex(bytelist))
    resp = Gbl.spi0.xfer2(bytelist)
    print(resp)
    return resp


def write_reg(regID, reg_val):
    """
     * @brief Writes a register of the AD7124
     * @param uint8 address - address of the register
     * @param uint8 reg_val - value to be written
     * @return none
    """
    bytelist = []
    bytelist.append(regID)
    bytelist.append(reg_val)
    Gbl.spi0.xfer2(bytelist)


def ReadDeviceRegister(reg_name):
    """
    * @brief Reads and returns the value of a device register. The read
    * value is also stored in software register list of the device.
    *
    * @param reg - string: Which register to read from.
    *
    * @return - uint8: Returns the value read from the specified register.
    """
    regobj = search_dict(RegAddrs, 'name', reg_name)
    regID = regobj['addr']
    resp = read_reg(regID)
    return resp


def WriteDeviceRegister(reg_name, value):
    """
    * @brief Writes the specified value to a device register. The
    *        value to be written is also stored in the software
    *        register list of the device.
    *
    * @param device - The handler of the instance of the driver.
    * @param reg - string: Which register to write to.
    * @param value - uint32: The value to be written to the
    *                reigster of the device.
    *
    * @return uint32: Returns 0 for success or negative error code.
    """
    regobj = search_dict(RegAddrs,'name', reg_name)
    regID = regobj['addr']
    resp = write_reg(regID, value)
    return resp


def reset():
    """
    * @brief Resets the device.
    *
    * @param device - The handler of the instance of the driver.
    *
    * @return uint32 Returns 0 for success or negative error code.
    """
    ret = 0
    wrBuf = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    ret = Gbl.spi0.writebytes(wrBuf)
    return ret

# def WaitForConvReady(spiref, timeout):
#    """
#    * @brief Waits until a new conversion result is available.
#    *
#    * @param device - The handler of the instance of the driver.
#    * @param timeout - uint32: Count representing the number of
#    *                  polls to be done until the
#    *                  function returns if no new data is available.
#    *
#    * @return int32 Returns 0 for success or negative error code.
#    """
#    ready = 0  # int
#
#    while ready == 0 and timeout:
#        timeout -= timeout
#        # Read the value of the Status Register
#        ready = AD7124_STATUS_REG_RDY()
#        if ready < 0:
#            return ready
#        sleep(.001)
#
#    if timeout == 0:
#        return -1
#    else:
#        return timeout


def search_dict(dict_name, key, value):
    """
    * @brief Returns dictionary record that matches key name
    *        with key value
    *
    * @param dict_name - The name of the dictinary
    * @param key - key name
    * @param value - key value
    *
    * @return object: Dictionary record.
    """
    for p in dict_name:
        if p[key] == value:
            return p


def ExtractRegisterFunction(func_name,reg_read_data):
    # get register address
    record = search_dict(RegBits, 'func_name', func_name)
    register_name = record['reg_name']
    mask = record['mask']
    shift = record['shift']
    polarity = record['bit_pol']
    bits_value = (reg_read_data >> shift) & mask
    return bits_value


def AD7124_STATUS_REG_ERROR_FLAG():
    error = ReadDeviceRegister("Status")
    error = (error & 0b01000000) >> 6
    return error
