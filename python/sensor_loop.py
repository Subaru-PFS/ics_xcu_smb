import logging
import threading
import time

class SensorThread(threading.Thread):
    def __init__(self, smbdb, tlm_dict, bang_bangs, adcs, heaters, ads1015,
                 sensorPeriod=None,
                 logLevel=logging.INFO):
        self.logger = logging.getLogger('sensors')
        self.logger.setLevel(logLevel)
        self.db = smbdb
        self.tlm_dict = tlm_dict
        self.bb = bang_bangs
        self.adcs = adcs
        self.heaters = heaters
        self.ads1015 = ads1015
        self.loopPeriod = 10.0 if sensorPeriod is None else sensorPeriod
        self.__exitEvent = threading.Event()
        
        threading.Thread.__init__(self, name='sensors', daemon=True)

    def pleaseExit(self):
        self.__exitEvent.set()
        self.logger.warn('please wait up to %s seconds for the sensor loop to stop', self.loopPeriod)
        
    def run(self):
        try:
            lastTime = time.time()
            while True:
                self.logger.debug("starting sensor conversions")
                for adc in self.adcs:
                    if self.__exitEvent.is_set():
                        self.logger.info("exiting sensor loop because we were asked to")
                        return
                
                    try:
                        adc.read_conversion_data()
                    except Exception as e:
                        self.logger.warn("failed to read adc %d: %s", adc.idx, e)
                self.logger.debug("finished sensor conversions")
                for h in self.heaters:
                    h.updateControlLoop(self.adcs)
                    
                if self.__exitEvent.is_set():
                    self.logger.info("exiting sensor loop because we were asked to.")
                    return

                if self.loopPeriod is None:
                    time.sleep(0.5)
                else:
                    nextTime = lastTime + self.loopPeriod
                    now = time.time()
                    dt = nextTime - now
                    
                    if dt < 0.01:
                        self.logger.warn('loop period is too short. last=%g, next=%g, dt=%g',
                                         lastTime, nextTime, nextTime-now)
                        dt = 0.01
                    time.sleep(dt)
                    lastTime = time.time()
                    
        except Exception as e:
            self.logger.warn('sensor loop received and is ignoring exception: %s', e)

