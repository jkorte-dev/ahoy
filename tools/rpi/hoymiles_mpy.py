from ahoy_cfg import ahoy_config
from hoymiles import HoymilesDTU
import hoymiles.uoutputs


def init_network_time():
    import ntptime
    import wlan
    wlan.do_connect()
    ntptime.settime()


def result_handler(result, inverter):
    print(result.__dict_())
#    mqtt.store_status(result)
    display.store_status(result)


init_network_time()
mqtt = hoymiles.uoutputs.MqttPlugin(ahoy_config.get('mqtt', {'host': 'homematic-ccu2'}))
display = hoymiles.uoutputs.DisplayPlugin({'i2c_num': 0})

dtu = HoymilesDTU(ahoy_cfg=ahoy_config,
                  status_handler=result_handler,
                  info_handler=lambda result, inverter: print("hw_info", result, result.__dict_()))
dtu.start()
