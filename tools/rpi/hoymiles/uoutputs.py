#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hoymiles output plugin library
"""

# from datetime import datetime, timezone
from hoymiles.decoders import StatusResponse, HardwareInfoResponse


class OutputPluginFactory:
    def __init__(self, **params):
        self.inverter_ser = params.get('inverter_ser', '')
        self.inverter_name = params.get('inverter_name', None)

    def store_status(self, response, **params):
        raise NotImplementedError('The current output plugin does not implement store_status')


class DisplayPlugin(OutputPluginFactory):
    display = None

    def __init__(self, config, **params):
        super().__init__(**params)

        try:
            from machine import Pin, I2C
            from ssd1306 import SSD1306_I2C
        except ImportError as ex:
            print('Install module with command: mpremote mip install ssd1306')
            raise ex

        try:
            i2c_num = config.get('i2c_num', 0)
            scl_pin = config.get('scl_pin')  # no default
            sda_pin = config.get('sda_pin')  # no default
            display_width = config.get('display_width', 128)
            display_height = config.get('display_height', 64)
            if scl_pin and sda_pin:
                i2c = I2C(i2c_num, scl=Pin(scl_pin), sda=Pin(sda_pin))
            else:
                i2c = I2C(i2c_num)
            print("Display i2c", i2c)
            self.display = SSD1306_I2C(display_width, display_height, i2c)
            self.display.fill(0)
            self.display.text("Ahoy DTU", 0, (display_height // 2), 1)
            self.display.show()

        except Exception as e:
            print("display not initialized", e)

    def store_status(self, response, **params):
        if not isinstance(response, StatusResponse):
            raise ValueError('Data needs to be instance of StatusResponse')

        data = response.__dict_()

        phase_sum_power = 0
        if data['phases'] is not None:
            for phase in data['phases']:
                phase_sum_power += phase['power']
        self._show_value(0, f"power: {phase_sum_power} W")
        if data['yield_today'] is not None:
            yield_today = data['yield_today']
            self._show_value(1, f"today: {yield_today} Wh")
        if data['yield_total'] is not None:
            yield_total = round(data['yield_total'] / 1000)
            self._show_value(2, f"total: {yield_total} kWh")
        if data['time'] is not None:
            timestamp = data['time'].isoformat()
            self._show_value(3, timestamp)

    def _show_value(self, slot, value):
        if self.display is None:
            print(value)
            return
        pos = slot * (self.display.height // 4)
        self.display.fill_rect(0, pos, self.display.width, 10, 0)  # clear data on display
        self.display.text(value, 0, pos, 1)
        self.display.show()


class MqttPlugin(OutputPluginFactory):
    """ Mqtt output plugin """
    client = None

    def __init__(self, config, **params):
        super().__init__(**params)

        try:
            from umqtt.simple import MQTTClient
        except ImportError:
            print('Install module with command: mpremote mip install mqtt.simple')

        print("mqtt plugin", config)

        try:
            import wlan
            wlan.do_connect()
            from machine import unique_id
            from ubinascii import hexlify
            mqtt_broker = config.get('host', '127.0.0.1')
            mqtt_client = MQTTClient(hexlify(unique_id()), mqtt_broker)
            mqtt_client.connect()
            print("connected to ", mqtt_broker)

        except Exception as e:
            print("MQTT disabled. network error:", e)
            raise e

        self.client = mqtt_client

    def store_status(self, response, **params):
        data = response.__dict_()

        if data is None:
            return

        topic = params.get('topic', None)
        if not topic:
            topic = f'{data.get("inverter_name", "hoymiles")}/{data.get("inverter_ser", None)}'

        if isinstance(response, StatusResponse):

            # Global Head
            if data['time'] is not None:
                self._publish(f'{topic}/time', data['time'].isoformat())

            # AC Data
            phase_id = 0
            phase_sum_power = 0
            if data['phases'] is not None:
                for phase in data['phases']:
                    # todo topic umbennen
                    self._publish(f'{topic}/emeter/{phase_id}/voltage', phase['voltage'])
                    self._publish(f'{topic}/emeter/{phase_id}/current', phase['current'])
                    self._publish(f'{topic}/emeter/{phase_id}/power', phase['power'])
                    self._publish(f'{topic}/emeter/{phase_id}/Q_AC', phase['reactive_power'])
                    self._publish(f'{topic}/emeter/{phase_id}/frequency', phase['frequency'])
                    phase_id = phase_id + 1
                    phase_sum_power += phase['power']

            # DC Data
            string_id = 0
            string_sum_power = 0
            if data['strings'] is not None:
                for string in data['strings']:
                    if 'name' in string:
                        string_name = string['name'].replace(" ", "_")
                    else:
                        string_name = string_id
                    # todo topic umbennen
                    self._publish(f'{topic}/emeter-dc/{string_name}/voltage', string['voltage'])
                    self._publish(f'{topic}/emeter-dc/{string_name}/current', string['current'])
                    self._publish(f'{topic}/emeter-dc/{string_name}/power', string['power'], )
                    self._publish(f'{topic}/emeter-dc/{string_name}/YieldDay', string['energy_daily'])
                    self._publish(f'{topic}/emeter-dc/{string_name}/YieldTotal', string['energy_total'] / 1000,
                                  )
                    self._publish(f'{topic}/emeter-dc/{string_name}/Irradiation', string['irradiation'])
                    string_id = string_id + 1
                    string_sum_power += string['power']

            # Global
            if data['event_count'] is not None:
                self._publish(f'{topic}/total_events', data['event_count'])
            if data['powerfactor'] is not None:
                self._publish(f'{topic}/PF_AC', data['powerfactor'])
            self._publish(f'{topic}/Temp', data['temperature'])
            if data['yield_total'] is not None:
                self._publish(f'{topic}/YieldTotal', data['yield_total'] / 1000)
            if data['yield_today'] is not None:
                self._publish(f'{topic}/YieldToday', data['yield_today'] / 1000)
            if data['efficiency'] is not None:
                self._publish(f'{topic}/Efficiency', data['efficiency'])

        elif isinstance(response, HardwareInfoResponse):
            if data["FW_ver_maj"] is not None and data["FW_ver_min"] is not None and data["FW_ver_pat"] is not None:
                self._publish(f'{topic}/Firmware/Version',
                                    f'{data["FW_ver_maj"]}.{data["FW_ver_min"]}.{data["FW_ver_pat"]}')

            if data["FW_build_dd"] is not None and data["FW_build_mm"] is not None and data["FW_build_yy"] is not None and data["FW_build_HH"] is not None and data["FW_build_MM"] is not None:
                self._publish(f'{topic}/Firmware/Build_at',
                                    f'{data["FW_build_dd"]}/{data["FW_build_mm"]}/{data["FW_build_yy"]}T{data["FW_build_HH"]}:{data["FW_build_MM"]}')

            if data["FW_HW_ID"] is not None:
                self._publish(f'{topic}/Firmware/HWPartId', f'{data["FW_HW_ID"]}')

        else:
            raise ValueError('Data needs to be instance of StatusResponse or a instance of HardwareInfoResponse')

    def _publish(self, topic, value):
        self.client.publish(topic.encode(), str(value))
        
