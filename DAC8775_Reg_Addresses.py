"""
Dictionary of AD7124 Register addresses
"""

RegAddrs = [
    {'name': "no_operation", 'addr': 0x00, 'value': 0x0000, 'per_chan': False, 'rw': 1},
    {'name': "reset", 'addr': 0x01, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "reset_config", 'addr': 0x02, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "select_dac", 'addr': 0x03, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "configuration_dac", 'addr': 0x04, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "Select_DAC_register", 'addr': 0x05, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "Select_Buck_Boost_converter", 'addr': 0x06, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "configuration_Buck-Boost_converter", 'addr': 0x07, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "dac_channel_calibration_enable", 'addr': 0x08, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "dac_channel_gain_calibration", 'addr': 0x09, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "dac_channel_offset_calibration", 'addr': 0x0A, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "status", 'addr': 0x0B, 'value': 0x1000, 'per_chan': False, 'rw': 2},
    {'name': "status_mask", 'addr': 0x0c, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "alarm_action", 'addr': 0x0d, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "user_alarm_code", 'addr': 0x0e, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "reserved", 'addr': 0x0f, 'value': 0x0000, 'per_chan': True, 'rw': 0},
    {'name': "write_watchdog_timer_reset", 'addr': 0x10, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "device_ID", 'addr': 0x11, 'value': 0x0000, 'per_chan': False, 'rw': 2},
]


def search_reg_address_from_name(name):
    for a in RegAddrs:
        if a['name'] == name:
            return a['addr']

    return -1

"""
@dictionary GPIO Pin Numbers
@Maps DAC singals to GPIO PINS.
"""
gpio = {
    "SDA_0": 2,
    "SCL_0": 3,
    "GPIO4": 4,
    "nLDAC": 6,
    "nADC_CS1": 7,
    "nADC_CS0": 8,
    "SPI0_MISO": 9,
    "SPI0_MOSI": 10,
    "SPI0_SCLK": 11,
    "DAC_CLR": 12,
    "nALARM": 13,
    "nDAC_CS": 16,
    "GPIO17": 17,
    "GPIO18": 18,
    "SPI1 MOSI": 20,
    "SPI1 SCLK": 21,
    "GPIO22": 22,
    "GPIO23": 23,
    "GPIO24": 24,
    "GPIO25": 25,
    "nRESET": 26,
    "GPIO27": 27,

}