"""
Dictionary of AD7124 Register addresses
"""

RegAddrs = [
    {'name': "no_operation", 'addr': 0x00, 'value': 0x0000, 'per_chan': False, 'rw': 1},
    {'name': "reset", 'addr': 0x01, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "reset_config", 'addr': 0x02, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "select_dac", 'addr': 0x03, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "configuration_dac", 'addr': 0x04, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "DAC_data", 'addr': 0x05, 'value': 0x0000, 'per_chan': True, 'rw': 2},
    {'name': "Select_Buck_Boost_converter", 'addr': 0x06, 'value': 0x0000, 'per_chan': False, 'rw': 2},
    {'name': "configuration_Buck_Boost_converter", 'addr': 0x07, 'value': 0x0000, 'per_chan': True, 'rw': 2},
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
