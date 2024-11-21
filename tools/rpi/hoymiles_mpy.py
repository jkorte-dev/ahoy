from ahoy_cfg import ahoy_config
from hoymiles import HoymilesDTU


def result_handler(result, inverter): print(result.__dict_())


dtu = HoymilesDTU(ahoy_cfg=ahoy_config,
                  status_handler=result_handler,
                  info_handler=lambda result, inverter: print("hw_info", result, result.__dict_()))
dtu.start()
