from ahoy_cfg import ahoy_config
from hoymiles import HoymilesDTU
import asyncio
import hoymiles.uoutputs
import gc

#ahoy_config['sunset'] = {'disabled': True}


def init_network_time():
    print('init_network_time')
    import wlan
    import time
    wlan.do_connect()
    init = 10
    while init:
        try:
            import ntptime
            ntptime.settime()
            init=0
        except OSError:
            print('failed to set ntp time')
            init -= 1
            time.sleep(1)
    gc.collect()


def result_handler(result, inverter):
    print(result.to_dict())
    display.store_status(result)
    mqtt.store_status(result)
    blink.store_status(result)
    print("mem_free:", gc.mem_free())


init_network_time()

display = hoymiles.uoutputs.DisplayPlugin({'i2c_num': 0})
mqtt = hoymiles.uoutputs.MqttPlugin(ahoy_config.get('mqtt', {'host': 'homematic-ccu2'}))
blink = hoymiles.uoutputs.BlinkPlugin(ahoy_config.get('blink', {}))  # {'led_pin': 7, 'led_high_on': True, 'neopixel': False}

dtu = HoymilesDTU(ahoy_cfg=ahoy_config,
                  status_handler=result_handler,
                  info_handler=lambda result, inverter: print("hw_info", result, result.to_dict()))


asyncio.run(dtu.start())

