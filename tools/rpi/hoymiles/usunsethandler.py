import logging
import time
from datetime import timedelta, date


class SunsetHandler:

    def __init__(self, sunset_config, mqtt_client=None):
        self.suntimes = None
        try:
            from .usuntimes import Suntime
        except ImportError as e:
            #logging.info
            print('Sunset disabled.', e)
            return
        if sunset_config and not sunset_config.get('disabled', True):
            # (49.453872, 11.077298)
            latitude = sunset_config.get('latitude')
            longitude = sunset_config.get('longitude')
            altitude = sunset_config.get('altitude')
            self.suntimes = Suntime(longitude=longitude, latitude=latitude, altitude=altitude)
            self.suntimes.calc_sunrise_sunset(*time.localtime()[:3])
            hour, minutes = divmod(self.suntimes.sunset,  60)  # sunset in minutes
            #logging.info
            print(f'localtime()={time.localtime()}, lat={latitude}, lon={longitude}')
            print(f'Todays sunset is at {hour:02d}:{minutes:02d} UTC, sunrise is at {self.suntimes.sunrise//60}:{self.suntimes.sunrise%60:02d} UTC')
        else:
            logging.info('Sunset disabled.')

    def checkWaitForSunrise(self):
        if not self.suntimes:
            return
        # if the sunset already happened for today
        time_to_sleep = 0
        hour, minutes = time.localtime()[3:5]
        now = hour * 60 + minutes
        if self.suntimes.sunset < now:  # after sunset
            # wait until the sun rises again. if it's already after midnight, this will be today
            today = time.localtime()[:3]
            tomorrow = date(*today) + timedelta(days=1)
            self.suntimes.calc_sunrise_sunset(*tomorrow.tuple())
            time_to_sleep = int(self.suntimes.sunrise + (24*60 - now)) * 60
        elif self.suntimes.sunrise > now:  # before sunrise
            time_to_sleep = int(self.suntimes.sunrise - now) * 60

        # logging.info
        # print(f'Next sunrise is at {self.suntimes.sunrise//60}:{self.suntimes.sunrise%60:02d} UTC, next sunset is at {self.suntimes.sunset//60}:{self.suntimes.sunset%60:02d} UTC, sleeping for {time_to_sleep} seconds.')
        # h, m = divmod(time_to_sleep//60, 60); print(f'Wake up in {h:02d} hours {m:02d} min.')

        if time_to_sleep > 0:
            print(f'Next sunrise is at {self.suntimes.sunrise//60}:{self.suntimes.sunrise%60:02d} UTC, next sunset is at {self.suntimes.sunset//60}:{self.suntimes.sunset%60:02d} UTC, sleeping for {time_to_sleep} seconds.')
            time.sleep(time_to_sleep)
            logging.info(f'Woke up...')

