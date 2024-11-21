ahoy_config = {'interval': 5,
               'transmit_retries': 5,
               #'logging': {'filename': 'hoymiles.log', 'level': 'DEBUG', 'max_log_filesize': 1000000, 'max_log_files': 1},
               #'sunset': {'disabled': False, 'latitude': 51.799118, 'longitude': 10.615523, 'altitude': 1142},
               'nrf': [{'ce_pin': 22, 'cs_pin': 0, 'txpower': 'low', 'spispeed': 600000}],
               #'mqtt': {'disabled': False, 'host': 'homematic-ccu2', 'port': 1883, 'user': None, 'password': None, 'useTLS': False, 'insecureTLS': False, 'QoS': 0, 'Retain': True, 'last_will': {'topic': 'raspi-hoymiles', 'payload': 'LAST-WILL-MESSAGE: Please check my HOST and Process!'}},
               #'influxdb': {'disabled': True, 'url': 'http://influxserver.local:8086', 'org': 'myorg', 'token': '<base64-token>', 'bucket': 'telegraf/autogen', 'measurement': 'hoymiles'},
               #'volkszaehler': {'disabled': True, 'inverters': [{'serial': 114172220003, 'url': 'http://localhost/middleware/', 'channels': [{'type': 'ac_frequency0', 'uid': ''}, {'type': 'ac_power0', 'uid': '7ca5ac50-1e41-11ed-927f-610c4cb2c69e'}, {'type': 'ac_voltage0', 'uid': '9a38e2e0-1d94-11ed-b539-25f8607ac030'}, {'type': 'ac_current0', 'uid': 'a9a4daf0-1e41-11ed-b68c-eb73eef3d21d'}, {'type': 'ac_reactive_power0', 'uid': ''}, {'type': 'dc_power0', 'uid': '38eb3ca0-1e53-11ed-b830-792e70a592fa'}, {'type': 'dc_voltage0', 'uid': ''}, {'type': 'dc_current0', 'uid': ''}, {'type': 'dc_energy_total0', 'uid': ''}, {'type': 'dc_energy_daily0', 'uid': 'c2a93ea0-9a4e-11ed-8000-7d82e3ac8959'}, {'type': 'dc_irradiation0', 'uid': 'c2d887a0-9a4e-11ed-a7ac-0dab944fd82d'}, {'type': 'dc_power1', 'uid': '51c0e9d0-1e53-11ed-b574-8bc81547eb8f'}, {'type': 'dc_voltage1', 'uid': ''}, {'type': 'dc_current1', 'uid': ''}, {'type': 'dc_energy_total1', 'uid': ''}, {'type': 'dc_energy_daily1', 'uid': 'c3c04df0-9a4e-11ed-82c6-a15a9aba54a3'}, {'type': 'dc_irradiation1', 'uid': 'c3f3efd0-9a4e-11ed-9a77-3fd3187e6237'}, {'type': 'temperature', 'uid': 'ad578a40-1d97-11ed-8e8b-fda01a416575'}, {'type': 'powerfactor', 'uid': ''}, {'type': 'yield_total', 'uid': ''}, {'type': 'yield_today', 'uid': 'c4a76dd0-9a4e-11ed-b79f-2de013d39150'}, {'type': 'efficiency', 'uid': 'c4d8e9c0-9a4e-11ed-9d9e-9737749e4b45'}]}]},
               'dtu': {'serial': 99978563001, 'name': 'raspi-dtu'},
               'inverters': [
                   {'name': 'garage',
                    'serial': 114182941658,
                    'txpower': 'low',
                    'mqtt': {'send_raw_enabled': False, 'topic': 'hoymiles/114182941658'},
                    'strings': [
                        {'s_name': 'String 1 left', 's_maxpower': 380},
                        {'s_name': 'String 2 right', 's_maxpower': 380},
                        {'s_name': 'String 3 up', 's_maxpower': 405},
                        {'s_name': 'String 4 down', 's_maxpower': 410}
                    ]
                    }
                ]
               }
