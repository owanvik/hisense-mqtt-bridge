#!/usr/bin/env python3
"""Oppdaterer MQTT Discovery - fjerner Netflix/YouTube, legger til Volum opp/ned"""

import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client(
    client_id='hisense_cleanup', 
    protocol=mqtt.MQTTv311, 
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set('hisense', 'hisense')
client.connect('10.0.0.50', 1883, 60)
client.loop_start()
time.sleep(1)

# Slett Netflix og YouTube
client.publish('homeassistant/button/hisense_tv_soverom_netflix/config', '', retain=True)
client.publish('homeassistant/button/hisense_tv_soverom_youtube/config', '', retain=True)
print('Slettet Netflix og YouTube')

# Legg til Volume Up og Down
device_info = {
    'identifiers': ['a062fb1bf2e1'],
    'name': 'Hisense TV Soverom',
    'manufacturer': 'Hisense',
    'model': 'VIDAA TV'
}

buttons = [
    ('volume_up', 'KEY_VOLUMEUP', 'mdi:volume-plus', 'Volum opp'),
    ('volume_down', 'KEY_VOLUMEDOWN', 'mdi:volume-minus', 'Volum ned'),
]

for btn_id, key, icon, name in buttons:
    config = {
        'name': name,
        'unique_id': f'a062fb1bf2e1_{btn_id}',
        'object_id': f'hisense_tv_soverom_{btn_id}',
        'device': device_info,
        'command_topic': 'hisense/hisense_tv_soverom/command/key',
        'payload_press': key,
        'icon': icon,
        'availability_topic': 'hisense/hisense_tv_soverom/available'
    }
    client.publish(f'homeassistant/button/hisense_tv_soverom_{btn_id}/config', json.dumps(config), retain=True)
    print(f'Lagt til {name}')

# Marker som online
client.publish('hisense/hisense_tv_soverom/available', 'online', retain=True)

time.sleep(2)
client.loop_stop()
client.disconnect()
print('Ferdig!')
