#!/usr/bin/env python3
"""Test volum-kontroll med før/etter måling"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = '10.0.0.109'
TV_PORT = 36669

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, 'rcm_certchain_pem.cer')
KEY_FILE = os.path.join(SCRIPT_DIR, 'rcm_pem_privkey.pkcs8')

client = mqtt.Client(
    client_id='HomeAssistant',
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

volume_before = None
volume_after = None
step = 0

def on_connect(client, userdata, flags, rc, props=None):
    global step
    if rc == 0:
        print('✅ Tilkoblet TV!')
        client.subscribe('#')
        step = 1
        # Hent volum først
        print('📊 Henter nåværende volum...')
        client.publish('/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume', '')

def on_message(client, userdata, msg):
    global volume_before, volume_after, step
    
    try:
        payload = json.loads(msg.payload.decode())
        
        if 'volume_value' in payload:
            vol = payload['volume_value']
            
            if step == 1:
                volume_before = vol
                print(f'🔊 Volum FØR: {volume_before}')
                step = 2
                
                # Send volumeup
                print('📤 Sender KEY_VOLUMEUP...')
                client.publish('/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey',
                              json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"}))
                
                # Vent og hent volum igjen
                time.sleep(1)
                client.publish('/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume', '')
                
            elif step == 2:
                volume_after = vol
                print(f'🔊 Volum ETTER: {volume_after}')
                
                if volume_after != volume_before:
                    print(f'✅ VOLUM ENDRET! {volume_before} -> {volume_after}')
                else:
                    print(f'❌ Volum uendret: {volume_before}')
                step = 3
                
    except:
        pass

client.on_connect = on_connect
client.on_message = on_message

print(f'🔄 Kobler til {TV_IP}:{TV_PORT}...')
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

# Vent på resultater
timeout = 10
start = time.time()
while step < 3 and time.time() - start < timeout:
    time.sleep(0.5)

if step < 3:
    print('⏰ Timeout - fikk ikke alle responser')
    print(f'   step={step}, volume_before={volume_before}, volume_after={volume_after}')

client.loop_stop()
client.disconnect()
print('👋 Ferdig')
