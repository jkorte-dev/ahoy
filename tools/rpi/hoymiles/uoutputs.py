#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hoymiles output plugin library
"""

# from datetime import datetime, timezone
from hoymiles.decoders import StatusResponse, HardwareInfoResponse
import framebuf
from time import sleep
import logging


class OutputPluginFactory:
    def __init__(self, **params):
        self.inverter_ser = params.get('inverter_ser', '')
        self.inverter_name = params.get('inverter_name', None)

    def store_status(self, response, **params):
        raise NotImplementedError('The current output plugin does not implement store_status')


class DisplayPlugin(OutputPluginFactory):
    display = None
    symbols = {'sum': bytearray(b'\x00\x00\x7f\x80`\x800\x00\x18\x00\x0c\x00\x18\x000\x00`\x80\x7f\x80'),
               'cal': bytearray(b'\x7f\x80\x7f\x80@\x80D\x80L\x80T\x80D\x80D\x80@\x80\x7f\x80'),
               'wifi': bytearray(b'\xf8\x00\x0e\x00\xe3\x009\x80\x0c\x80\xe6\xc02@\x1b@\xc9@\xc9@'),
               'level': bytearray(b'\x00\x00\x01\x80\x01\x80\x01\x80\r\x80\r\x80\r\x80m\x80m\x80m\x80')}

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
            splash = "Ahoy! DTU"
            self.font_size = 10  # fontsize fix 8 + 2 pixel

            self.display = SSD1306_I2C(display_width, display_height, i2c)
            self.display.fill(0)
            self.display.text(splash, ((display_width - len(splash)*(self.font_size-2)) // 2), (display_height // 2), 1)
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
        self.show_value(0, f"     {phase_sum_power} W")
        self.show_symbol(0, 'level')
        self.show_symbol(0, 'wifi', x=self.display.width-self.font_size)  # todo show wifi symbol on wifi connect event
        if data['yield_today'] is not None:
            yield_today = data['yield_today']
            self.show_value(1, f"     {yield_today} Wh")
            self.show_symbol(1, "cal", x=15)
        if data['yield_total'] is not None:
            yield_total = round(data['yield_total'] / 1000)
            self.show_value(2, f"     {yield_total:01d} kWh")
            self.show_symbol(2, "sum", x=15)
        if data['time'] is not None:
            timestamp = data['time']  # datetime.isoformat()
            Y, M, D, h, m, s, us, tz, fold = timestamp.tuple()
            self.show_value(3, f' {D:02d}.{M:02d} {h:02d}:{m:02d}:{s:02d}')

    def show_value(self, slot, value):  # todo feature center / align
        if self.display is None:
            print(value)
            return
        x = 0
        y = slot * (self.display.height // 4)
        self.display.fill_rect(x, y, self.display.width, self.font_size, 0)  # clear data on display
        self.display.text(value, x, y, 1)
        self.display.show()

    def show_symbol(self, slot, sym, x=None, y=None):
        if slot:
            y = slot * (self.display.height // 4)
        x = x if x else 0
        y = y if y else 0
        data = self.symbols.get(sym)
        if data:
            self.display.blit(framebuf.FrameBuffer(data, self.font_size, self.font_size, framebuf.MONO_HLSB), x, y)
            self.display.show()


class MqttPlugin(OutputPluginFactory):
    """ Mqtt output plugin """
    def __init__(self, config, **params):
        super().__init__(**params)

        print("mqtt plugin", config)

        self.dry_run = config.get('dry_run', False)
        self.client = None

        try:
            from umqtt.simple import MQTTClient
        except ImportError:
            print('Install module with command: mpremote mip install mqtt.simple')
            return
        try:
            from machine import unique_id
            from ubinascii import hexlify
            mqtt_broker = config.get('host', '127.0.0.1')
            mqtt_client = MQTTClient(hexlify(unique_id()), mqtt_broker)
            mqtt_client.connect()
            print("connected to ", mqtt_broker)
            self.client = mqtt_client
        except OSError as e:
            print("MQTT disabled. network error?:", e)
            logging.exception(e)

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
            phases_ac = data['phases']
            if phases_ac is not None:
                for phase in phases_ac:
                    phase_name = f'ac/{phase_id}' if len(phases_ac) > 1 else 'ch0'
                    self._publish(f'{topic}/{phase_name}/U_AC', phase['voltage'])
                    self._publish(f'{topic}/{phase_name}/I_AC', phase['current'])
                    self._publish(f'{topic}/{phase_name}/P_AC', phase['power'])
                    self._publish(f'{topic}/{phase_name}/Q_AC', phase['reactive_power'])
                    self._publish(f'{topic}/{phase_name}/F_AC', phase['frequency'])
                    phase_id = phase_id + 1
                    phase_sum_power += phase['power']

            # DC Data
            string_id = 1
            string_sum_power = 0
            if data['strings'] is not None:
                for string in data['strings']:
                    string_name = f'ch{string_id}'
                    if 'name' in string:
                        s_name = string['name'].replace(" ", "_")
                        self._publish(f'{topic}/{string_name}/name', s_name)
                    self._publish(f'{topic}/{string_name}/U_DC', string['voltage'])
                    self._publish(f'{topic}/{string_name}/I_DC', string['current'])
                    self._publish(f'{topic}/{string_name}/P_DC', string['power'], )
                    self._publish(f'{topic}/{string_name}/YieldDay', string['energy_daily'])
                    self._publish(f'{topic}/{string_name}/YieldTotal', string['energy_total'] / 1000)
                    self._publish(f'{topic}/{string_name}/Irradiation', string['irradiation'])
                    string_id = string_id + 1
                    string_sum_power += string['power']

            # Global
            if data['temperature'] is not None:
                self._publish(f'{topic}/Temp', data['temperature'])

            # Total
            self._publish(f'{topic}/total/P_DC', string_sum_power)
            self._publish(f'{topic}/total/P_AC', phase_sum_power)
            if data['event_count'] is not None:
                self._publish(f'{topic}/total/total_events', data['event_count'])
            if data['powerfactor'] is not None:
                self._publish(f'{topic}/total/PF_AC', data['powerfactor'])
            if data['yield_total'] is not None:
                self._publish(f'{topic}/total/YieldTotal', data['yield_total'] / 1000)
            if data['yield_today'] is not None:
                self._publish(f'{topic}/total/YieldToday', data['yield_today'] / 1000)
            if data['efficiency'] is not None:
                self._publish(f'{topic}/total/Efficiency', data['efficiency'])

        elif isinstance(response, HardwareInfoResponse):
            if data["FW_ver_maj"] is not None and data["FW_ver_min"] is not None and data["FW_ver_pat"] is not None:
                self._publish(f'{topic}/Firmware/Version',
                              f'{data["FW_ver_maj"]}.{data["FW_ver_min"]}.{data["FW_ver_pat"]}')

            if data["FW_build_dd"] is not None and data["FW_build_mm"] is not None and data[
                "FW_build_yy"] is not None and data["FW_build_HH"] is not None and data["FW_build_MM"] is not None:
                self._publish(f'{topic}/Firmware/Build_at',
                              f'{data["FW_build_dd"]}/{data["FW_build_mm"]}/{data["FW_build_yy"]}T{data["FW_build_HH"]}:{data["FW_build_MM"]}')

            if data["FW_HW_ID"] is not None:
                self._publish(f'{topic}/Firmware/HWPartId', f'{data["FW_HW_ID"]}')

        else:
            raise ValueError('Data needs to be instance of StatusResponse or a instance of HardwareInfoResponse')

    def _publish(self, topic, value):
        if self.dry_run or self.client is None:
            print(topic, str(value))
        else:
            self.client.publish(topic.encode(), str(value))


class BlinkPlugin(OutputPluginFactory):
    def __init__(self, config, **params):
        super().__init__(**params)
        led_pin = config.get('led_pin')
        self.high_on = config.get('led_high_on', True)
        if led_pin is None:
            self.led = None
        else:
            from machine import Pin
            self.led = Pin(led_pin, Pin.OUT)

    def store_status(self, response, **params):
        if self.led:
            self.led.value(self.high_on)
            sleep(0.05)  # keep ist short because it is blocking
            self.led.value(not self.high_on)  # self.led.toggle() not always supported

