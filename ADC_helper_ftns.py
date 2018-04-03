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



"""
@dictionary OperatingMode
@brief Control the mode of operation for ADC
"""
OperatingMode = {
    #  Continuous conversion mode (default). In continuous conversion mode, the ADC continuously performs
    #  conversions and places the result in the data register.
    "ContinuousMode": 0,
    #  Single conversion mode. When single conversion mode is selected, the ADC powers up and performs a
    #  single conversion on the selected channel.
    "SingleConvMode": 1,
    #  Standby mode. In standby mode, all sections of the AD7124 can be powered down except the LDOs.
    "StandbyMode": 2,
    #  Power-down mode. In power-down mode, all the AD7124 circuitry is powered down, including the current sources,
    #  power switch, burnout currents, bias voltage generator, and clock circuitry.
    "PowerDownMode": 3,
    #  Idle mode. In idle mode, the ADC filter and modulator are held in a reset state even though the
    #  modulator clocks continue to be provided.
    "IdleMode": 4,
    #  Internal zero-scale (offset) calibration. An internal short is automatically connected to the input.
    #  RDY goes high when the calibration is initiated and returns low when the calibration is complete.
    "InternalOffsetCalibrationMode": 5,
    #  Internal full-scale (gain) calibration. A full-scale input voltage is automatically connected to the
    #  selected analog input for this calibration.
    "InternalGainCalibrationMode": 6,
    #  System zero-scale (offset) calibration. Connect the system zero-scale input to the channel input
    #  pins of the selected channel. RDY goes high when the calibration is initiated and returns
    #  low when the calibration is complete.
    "SystemOffsetCalibrationMode": 7,
    #  System full-scale (gain) calibration. Connect the system full-scale input to the channel input pins
    #  of the selected channel. RDY goes high when the calibration is initiated and returns low when
    #  the calibration is complete.
    "SystemGainCalibrationMode": 8
}

"""
@dictionary  PowerMode
@brief Power Mode Select
These bits select the power mode. The current consumption and output data rate
ranges are dependent on the power mode.
"""
PowerMode = {
    "LowPower": 0,  # low power
    "MidPower": 1,  # mid power
    "FullPower": 2  # full power
}

"""
@dictionary ClkSel
@brief These bits select the clock source for the ADC
Either the on-chip 614.4 kHz clock can be used or an external clock can be
used. The ability to use an external clock allows several AD7124 devices to be
synchronized. Also, 50 Hz and 60 Hz rejection is improved when an accurate external clock drives the ADC.
"""
ClkSel = {
    "InternalClk": 0,  # internal 614.4 kHz clock. The internal clock is not available at the CLK pin
    "InternalWithOutputClk": 1,  # internal 614.4 kHz clock. This clock is available at the CLK pin
    "ExternalClk": 2,  # external 614.4 kHz clock
    "ExternalDiv4Clk": 3  # external clock. The external clock is divided by 4 within the AD7124
}

"""
@dictionary IoutCurrent
@brief These bits set the value of the excitation current for IOUT
"""
IoutCurrent = {
    "CurrentOff": 0,  # ff
    "Current50ua": 1,  # 50 uA
    "Current100ua": 2,  # 100 uA
    "Current250ua": 3,  # 250 uA
    "Current500ua": 4,  # 500 uA
    "Current750ua": 5,  # 750 uA
    "Current1000ua": 6  # 1 mA
}

"""
@dictionary IoutCh
@brief Channel select bits for the excitation current for IOUT.
"""
IoutCh = {
    "IoutCh0": 0,  # IOUT is available on the AIN0 pin.
    "IoutCh1": 1,  # IOUT is available on the AIN1 pin.
    "IoutCh2": 4,  # IOUT is available on the AIN2 pin.
    "IoutCh3": 5,  # IOUT is available on the AIN3 pin.
    "IoutCh4": 10,  # IOUT is available on the AIN4 pin.
    "IoutCh5": 11,  # IOUT is available on the AIN5 pin.
    "IoutCh6": 14,  # IOUT is available on the AIN6 pin.
    "IoutCh7": 15  # IOUT is available on the AIN7 pin.
}

"""
@ dictionary InputSel
@ brief Analog input AIN input select
"""
InputSel = {
    "AIN0Input": 0,  # AIN0
    "AIN1Input": 1,  # AIN1
    "AIN2Input": 1,  # AIN2
    "AIN3Input": 3,  # AIN3
    "AIN4Input": 4,  # AIN4
    "AIN5Input": 5,  # AIN5
    "AIN6Input": 6,  # AIN6
    "AIN7Input": 7,  # AIN7
    "TEMPInput": 16,  # Temperature sensor (internal)
    "AVSSInput": 17,  # AVss
    "REFInput": 18,  # Internal reference
    "DGNDInput": 19,  # DGND
    "AVDD6PInput": 20,  # (AVdd - AVss)/6+. Use in conjunction with (AVdd - AVss)/6- to monitor supply AVdd - AVss
    "AVDD6MInput": 21,  # (AVdd - AVss)/6-. Use in conjunction with (AVdd - AVss)/6+ to monitor supply AVdd - AVss
    "IOVDD6PInput": 22,  # (IOVdd - DGND)/6+. Use in conjunction with (IOVdd - DGND)/6- to monitor IOVdd - DGND
    "IOVDD6MInput": 23,  # (IOVdd - DGND)/6-. Use in conjunction with (IOVdd - DGND)/6+ to monitor IOVdd - DGND
    "ALDO6PInput": 24,  # (ALDO - AVss)/6+. Use in conjunction with (ALDO - AVss)/6- to monitor the analog LDO
    "ALDO6MInput": 25,  # (ALDO - AVss)/6-. Use in conjunction with (ALDO - AVss)/6+ to monitor the analog LDO
    "DLDO6PInput": 26,  # (DLDO - DGND)/6+. Use in conjunction with (DLDO - DGND)/6- to monitor the digital LDO
    "DLDO6MInput": 27,  # (DLDO - DGND)/6-. Use in conjunction with (DLDO - DGND)/6+ to monitor the digital LDO
    "V20mVPInput": 28,  # V_20MV_P. Use in conjunction with V_20MV_M to apply a 20 mV p-p signal to the ADC
    "V20mVMInput": 29  # V_20MV_M. Use in conjunction with V_20MV_P to apply a 20 mV p-p signal to the ADC
}

"""
@dictionary  PgaSel (Programmable Gain Array)
@brief Gain select bits.
These bits select the gain to use when converting on any channels using this configuration register.
 """
PgaSel = {
    "Pga1": 0,  # Gain 1, Input Range When VREF = 2.5 V: +/-2.5 V
    "Pga2": 1,  # Gain 2, Input Range When VREF = 2.5 V: +/-1.25 V
    "Pga4": 2,  # Gain 4, Input Range When VREF = 2.5 V: +/- 625 mV
    "Pga8": 3,  # Gain 8, Input Range When VREF = 2.5 V: +/-312.5 mV
    "Pga16": 4,  # Gain 16, Input Range When VREF = 2.5 V: +/-156.25 mV
    "Pga32": 5,  # Gain 32, Input Range When VREF = 2.5 V: +/-78.125 mV
    "Pga64": 6,  # Gain 64, Input Range When VREF = 2.5 V: +/-39.06 mV
    "Pga128": 7  # Gain 128, Input Range When VREF = 2.5 V: +/-19.53 mV
}

"""
@dictionary  RefSel
@brief Reference source select bits.
These bits select the reference source to use when converting on any channels using
this configuration register.
"""
RefSel = {
    "RefIn1": 0,  # REFIN1(+)/REFIN1(-)
    "RefIn2": 1,  # REFIN2(+)/REFIN2(-)
    "RefInternal": 2,  # internal reference
    "RefAVdd": 3  # AVDD
}

"""
@dictionary BurnoutCurrent
@brief These bits select the magnitude of the sensor burnout detect current source.
"""
BurnoutCurrent = {
    "BurnoutOff": 0,  # burnout current source off (default)
    "Burnout500nA": 1,  # burnout current source on, 0.5 uA
    "Burnout2uA": 2,  # burnout current source on, 2 uA
    "Burnout4uA": 3  # burnout current source on, 4 uA
}

"""
@dictionary FilterType
@brief Filter type select bits.
These bits select the filter type.
"""
FilterType = {
    "Sinc4Filter": 0,  # sinc4 filter (default)
    "Sinc3Filter": 2,  # sinc 3 filter
    #  fast settling filter using the sinc 4 filter. The sinc 4 filter is followed by an averaging block,
    #  which results in a settling time equal to the conversion time. In full power and mid power modes,
    #  averaging by 16 occurs whereas averaging by 8 occurs in low power mode.
    "Sinc4FastFilter": 4,
    #  fast settling filter using the sinc 3 filter. The sinc 3 filter is followed by an averaging block,
    #  which results in a settling time equal to the conversion time. In full power and mid power modes,
    #  averaging by 16 occurs whereas averaging by 8 occurs in low power mode.
    "Sinc3FastFilter": 5,
    #  post filter enabled. The AD7124 includes several post filters, selectable using the POST_FILTER bits.
    #  The post filters have single cycle settling, the settling time being considerably better than a simple
    #  sinc 3 /sinc 4 filter. These filters offer excellent 50 Hz and60 Hz rejection.
    "PostFilter": 7
}

"""
@dictionary PostFilterType
@brief Post filter type select bits.
When the filter bits are set to 1, the sinc 3 filter is followed by a post filter which
offers good 50 Hz and 60 Hz rejection at output data rates that have zero latency approximately.
"""
PostFilterType = {
    "dB47PostFilter": 2,  # Rejection at 50 Hz and 60 Hz +/- 1 Hz: 47 dB, Output Data Rate (SPS): 27.27 Hz
    "dB62PostFilter": 3,  # Rejection at 50 Hz and 60 Hz +/- 1 Hz: 62 dB, Output Data Rate (SPS): 25 Hz
    "dB86PostFilter": 5,  # Rejection at 50 Hz and 60 Hz +/- 1 Hz: 86 dB, Output Data Rate (SPS): 20 Hz
    "dB92PostFilter": 6  # Rejection at 50 Hz and 60 Hz +/- 1 Hz: 92 dB, Output Data Rate (SPS): 16.7 Hz
}
