#!/usr/bin/env python3
"""Send autentiseringskode til Hisense TV"""

import ssl
import time
import json
import sys
import paho.mqtt.client as mqtt

TV_IP = '10.0.0.109'
PORT = 36669
CLIENT_ID = 'HomeAssistant'

# Hent kode fra argument eller bruk default
AUTH_CODE = sys.argv[1] if len(sys.argv) > 1 else '1939'

done = False

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print('✅ Tilkoblet til TV')
        client.subscribe('#')
        # Send autentiseringskoden
        payload = json.dumps({'authNum': AUTH_CODE})
        topic = f'/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode'
        client.publish(topic, payload)
        print(f'🔐 Sendte autentiseringskode: {AUTH_CODE}')

def on_message(client, userdata, msg):
    global done
    payload = msg.payload.decode('utf-8', errors='ignore')
    
    if 'authentication' in msg.topic:
        print(f'📩 {msg.topic}')
        print(f'   {payload}')
        if 'close' not in msg.topic and payload == '':
            print('✅ AUTENTISERING VELLYKKET!')
            done = True

client = mqtt.Client(
    client_id=CLIENT_ID, 
    protocol=mqtt.MQTTv311, 
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(
    certfile='rcm_certchain_pem.cer', 
    keyfile='rcm_pem_privkey.pkcs8', 
    cert_reqs=ssl.CERT_NONE
)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print(f'🔄 Kobler til {TV_IP}:{PORT}...')
client.connect(TV_IP, PORT)
client.loop_start()

# Vent på svar
for i in range(10):
    if done:
        break
    time.sleep(0.5)

client.loop_stop()
client.disconnect()

if done:
    print('🎉 Klienten "HomeAssistant" er nå paret med TV-en!')
else:
    print('⏳ Ingen bekreftelse mottatt. Sjekk at koden er riktig.')
