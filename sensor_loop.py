import logging
import threading
import time

class SensorThread(threading.Thread):
    def __init__(self, smbdb, tlm_dict, bang_bangs, adcs, heaters, ads1015, logLevel=logging.DEBUG):
        self.logger = logging.getLogger('sensors')
        self.logger.setLevel(logLevel)
        self.db = smbdb
        self.tlm_dict = tlm_dict
        self.bb = bang_bangs
        self.adcs = adcs
        self.heaters = heaters
        self.ads1015 = ads1015
        self.loopTime = 0.5
        threading.Thread.__init__(self)
        
    def run(self):
        try:
            while True:
                self.logger.debug("starting sensor conversions")
                for adc in self.adcs:
                    try:
                        adc.read_conversion_data()
                    except Exception as e:
                        self.logger.warn("failed to read adc %d: %s", adc.idx, e)
                self.logger.debug("finished sensor conversions")

                time.sleep(self.loopTime)

        except KeyboardInterrupt:  # Ctrl+C pressed
            return

