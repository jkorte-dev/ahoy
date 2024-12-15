from ahoy_cfg import ahoy_config
from hoymiles import HoymilesDTU
import asyncio
import hoymiles.uoutputs


def init_network_time():
    import wlan
    wlan.do_connect()
    try:
        import ntptime
        ntptime.settime()
    except OSError:
        print('failed to set ntp time')


def result_handler(result, inverter):
    print(result.to_dict())
    display.store_status(result)
    mqtt.store_status(result)


init_network_time()
mqtt = hoymiles.uoutputs.MqttPlugin(ahoy_config.get('mqtt', {'host': 'homematic-ccu2'}))
display = hoymiles.uoutputs.DisplayPlugin({'i2c_num': 0})

dtu = HoymilesDTU(ahoy_cfg=ahoy_config,
                  status_handler=result_handler,
                  info_handler=lambda result, inverter: print("hw_info", result, result.to_dict()))


asyncio.run(dtu.start())

