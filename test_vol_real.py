#!/usr/bin/env python3
"""Send volum kommando som faktisk fungerer"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

current_vol = None

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    global current_vol
    try:
        payload = json.loads(msg.payload.decode())
        if "volumechange" in msg.topic and payload.get("volume_type") == 0:
            current_vol = payload.get("volume_value")
            print(f"🔊 Volum: {current_vol}")
    except:
        pass

client = mqtt.Client(
    client_id="HomeAssistant",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set("hisenseservice", "multimqttservice")
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Kobler til TV...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()
time.sleep(2)

# Hent nåværende volum
print("\n📥 Henter volum...")
client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
time.sleep(2)

if current_vol is not None:
    new_vol = current_vol + 1
    print(f"\n📤 Prøver å sette volum til {new_vol}...")
    
    # Prøv forskjellige payloads
    payloads = [
        # Bare tallet som string
        str(new_vol),
        # JSON med volume_type og volume_value
        json.dumps({"volume_type": 0, "volume_value": new_vol}),
        # Bare tallet som int
        new_vol,
    ]
    
    for i, payload in enumerate(payloads):
        print(f"\n   Test {i+1}: {payload}")
        client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/changevolume", payload)
        time.sleep(3)
        
        # Sjekk volum
        client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
        time.sleep(2)

print("\n" + "="*50)
print(f"👀 Sjekk TV - hva er volumet nå?")
print("="*50)

client.loop_stop()
