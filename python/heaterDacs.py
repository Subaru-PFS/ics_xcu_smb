from importlib import reload

import logging
import time

import GPIO_config
import Gbl

reload(GPIO_config)

logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                    format = "%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s %(filename)s:%(lineno)d %(message)s")

class HeaterDacs:
    regNames = dict(reset=1,
                    resetConfig=2,
                    selectDac=3,
                    configDac=4,
                    dacData=5, data=5,
                    selectBb=6,
                    configBb=7,
                    status=0xb,
                    statusMask=0xc,
                    alarmAction=0xd,
                    alarmCode=0xe,
                    watchdogReset=0x10,
                    deviceId=0x11,

                    # Until we get rid of the database, acces old names:
                    no_operation=0,
                    reset_config=2,
                    select_dac=3,
                    configuration_dac=4,
                    DAC_data=5,
                    Select_Buck_Boost_converter=6,
                    configuration_Buck_Boost_converter=7,
                    dac_channel_calibration_enable=8,
                    dac_channel_gain_calibration=9,
                    dac_channel_offset_calibration=10,
                    status_mask=12,
                    alarm_action=13,
                    user_alarm_code=14,
                    reserved=15,
                    write_watchdog_timer_reset=16,
                    device_ID=17,
                    )

    def __init__(self, gpio=None, logLevel=logging.INFO, halfTickLen=1e-6):
        self.logger = logging.getLogger('fuckery')
        self.logger.setLevel(logLevel)
        self.logger.info('starting logging!')

        if gpio is None:
            gpio = GPIO_config.Gpio()
        self.gpio = gpio

        self.mosi = self.gpio.pin_map['SPI1_MOSI']
        self.miso = self.gpio.pin_map['SPI1_MISO']
        self.sclk = self.gpio.pin_map['SPI1_SCLK']
        self.mss = self.gpio.pin_map['nDAC_BANK_SEL']
        self.cs0 = self.gpio.pin_map['nDAC_CS0']

        # set very slow for testing. Runs without errors with 1e-6
        self.halfTickLen = halfTickLen

        self.hasBeenInitialized = False

    def reset(self):
        """Hardware reset both DACs

        Note that all registers are reset to some default but probably
        useless/wrong value.
        """

        pin = self.gpio.pin_map['nDAC_RESET']
        with Gbl.ioLock:
            # Only needs 10 ns, which we cannot even get close to.
            self.gpio.output(pin, 0)
            self.gpio.output(pin, 1)

        self.hasBeenInitialized = False

    def clear(self):
        """Reset output level of both DACs

        Actual value we reset to depends on the value of register
        """
        pin = self.gpio.pin_map['DAC_CLR']
        with Gbl.ioLock:
            self.gpio.output(pin, 1)
            self.gpio.output(pin, 0)

        self.hasBeenInitialized = False

    def set_mss(self, enable):
        """Assert or drop the Mux Master Slave Select signal. """
        self.gpio.output(self.mss, not enable)

    def halfTick(self, n=1):
        """Pause the amount of time we want a half SCLK cycle to take.

        If .halfTickLen is small (~1us), just return.
        If .halfTickLen is large (>= ~1ms), use time.sleep()
        Else make up something for a pi3.
        """
        wait = n*self.halfTickLen

        if wait <= 3e-6:
            return

        if wait >= 5e-4:
            time.sleep(wait)
            return

        i = wait * 5e5
        while i > 0:
            i -= 1

    def selectDac(self, dac_id):
        """Select the right DAC.

        From the pi, there is a single "Chip Select" line. When 0, DAC 1 is selected; when 1, DAC 2 is selected.
        We actually drive the Chip Select ("/SYNC") at the DAC using the MUX Master Slave Select:
         - de-assert MSS
         - assert correct CS0 for the desired DAC
         - assert MSS

        The .halfTicks() are not necessary, but help with visualization.
        """

        if dac_id not in {1,2}:
            raise ValueError("unknown dac_id (not 1 or 2): %s" % (dac_id))
        with Gbl.ioLock:
            self.set_mss(False)
            self.halfTick()
            self.gpio.output(self.cs0, dac_id == 2)
            self.halfTick()
            self.set_mss(True)
            self.halfTick()

    def _xfer_bit(self, value):
        """Clock out a single SPI bit, and return whatever shows up on MISO.

        Input bits to the DACs and output bits from the DACs are latched/valid on the falling edge of SCLK.

        The .halfTicks() are not necessary but can make diagnostics easier.
        """

        value = bool(value)

        self.gpio.output(self.mosi, value)
        self.gpio.output(self.sclk, 0)
        self.halfTick()

        bitval = self.gpio.input(self.miso)
        self.gpio.output(self.sclk, 1)
        self.halfTick()

        return bitval

    def xfer(self, datalist, dacNum):
        """Send a 3-byte command to the given DAC; return MISO value.

        Args
        ----
        datalist : sequence of bytes
          The data to send.
        dacNum : 1 or 2
          The DAC to command.

        Always select the DAC before this transfer, and always deselect it 
        afterwards.
        DACs need their CS or /SYNC line to be deasserted
        between the request and the read.  Otherwise the query is
        echoed but the value is always 0x0000.
        """

        if len(datalist) != 3:
            raise ValueError('DACs only take 3-byte commands.')

        # Prepare a simple sequence of bits.
        outval = 0
        for byte in datalist:
            outval = (outval << 8) | byte

        # Now transfer those bits and capture MISO in the same order.
        sent = 0            # What we actually sent
        retval = 0          # What we got back
        with Gbl.ioLock:
            self.selectDac(dacNum)
            self.halfTick()

            for i in reversed(range(24)):
                outbit = bool(outval & (1 << i))
                misobit = self._xfer_bit(outbit)

                sent = (sent << 1) | outbit
                retval = (retval << 1) | misobit

            self.set_mss(False)
            self.halfTick()

        self.logger.debug('bb %d: out=0x%06x in=0x%06x', dacNum,
                          sent, retval)

        return retval & 0xffff

    def _hackSdo(self):
        """Arrange for DAC reads to work.

        DAC 0 are somehow interdependent DAC 1. In any case,
        we sometimes need to set the DSDO bit on a DAC before the other DAC can be read. """

        self.hasBeenInitialized = True

        for dac in 1, 0:
            dacSelect = self.readReg(dac, 'selectDac')
            dacSelect |= (1 << 4)
            self.writeReg(dac, 'selectDac', dacSelect)

        self.logger.info('Fixed DSDO bits...')

    def readReg(self, dac, reg):
        """Read a DAC register.

        Args
        ----
        dac : 1 or 2
          The DAC to read
        reg : int or string.
          The register to read

        Returns:
        val : the 16-bit register value.
        """
        if isinstance(reg, str):
            reg = self.regNames[reg]

        if not self.hasBeenInitialized:
            self._hackSdo()

        # Set high bit on register number to request a read.
        with Gbl.ioLock:
            self.xfer([0x80 | reg, 0, 0], dac)
            val = self.xfer([0, 0, 0], dac)

        self.logger.debug('dac %d reg %d read val 0x%04x',
                          dac, reg, val)
        return val

    def writeReg(self, dac, reg, val):
        """Write a DAC register.

        Args
        ----
        dac : 1 or 2
          The DAC to read
        reg : int or string
          The register to write
        val : `int`
          The value to write
        """

        if isinstance(reg, str):
            reg = self.regNames[reg]

        output = [reg,
                  (val & 0xff00) >> 8,
                  val & 0xff]
        ret = self.xfer(output, dac)

        self.logger.debug('dac %d reg %d wrote val 0x%04x as %s; ret = %s',
                          dac, reg, val, output, ret)
        return ret

    def selectChannel(self, idx, channel='none'):
        """Tell the DAC that the next data/config command applies to the given channel(s).

        Args
        ----
        idx : 0, 1
          The heater idx
        channel: a, b, c, d, all, none
          The DAC channel within the heater.
        """
        channel = channel.lower()

        masks = dict(a=0x1, b=0x2, c=0x4, d=0x8,
                     all=0xf, none=0x0)
        try:
            channelMask = masks[channel]
        except KeyError:
            raise ValueError('unknown channel id %s' % channel)

        # Get the rest of the bits from someplace sensible -- CPL
        regMask = self.readReg(idx, 'selectDac') & ~(0xf << 5)
        regMask |= (channelMask << 5)
        self.writeReg(idx, 'selectDac', regMask)

    def writeDacData(self, heaterIdx, dacId, value, doCheck=True):
        """Write a single (or all) DAC data values.

        Args
        ----
        heaterIdx : 0 or 1
          Which heater to write to.
        dacIdx : a, b, c, d
          The DAC channel to write to.
        value :
          The 16-bit value to write
        doCheck : bool, default True
          whether to immediately read the data register back
          and check it. -- CPL
        """

        with Gbl.ioLock:
            self.selectChannel(heaterIdx, dacId)
            self.writeReg(heaterIdx, 'data', value)

            if doCheck:
                self.selectChannel(heaterIdx, dacId)
                check = self.readReg(heaterIdx, 'data')
            else:
                check = None

        if doCheck and value != check:
            self.logger.warn('DAC readback failed. expected 0x%04x, got 0x%04x',
                             value, check)

    def readDacData(self, heaterIdx, dacId):
        """Fetch a single (or all) DAC data values.

        Args
        ----
        heaterIdx : 0 or 1
          Which heater to write to.
        dacIdx : a, b, c, d
          The DAC channel to write to.

        Returns
        -------
        value : 16-bit heater level.

        Does not check whether the channle is actually enabled.
        """

        with Gbl.ioLock:
            self.selectChannel(heaterIdx, dacId)
            value = self.readReg(heaterIdx, 'data')

        return value
