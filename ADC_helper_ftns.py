# Function to convert number into string
# Switcher is dictionary data type here
def select_gain_to_strings(argument):
    switcher = {
        1: "Pga1",
        2: "Pga2",
        4: "Pga4",
        8: "Pga8",
        16: "Pga16",
        32: "Pga32",
        64: "Pga64",
        128: "Pga128"
    }
    return switcher.get(argument, "Pga1")

def to_voltage(value, gain, vref, bipolar):
    voltage = value
    if bipolar:
        voltage = voltage / 0x7FFFFF - 1
    else:
        voltage = voltage / 0xFFFFFF

    voltage = voltage * vref / gain
    return voltage
