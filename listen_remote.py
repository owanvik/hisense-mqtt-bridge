#!/usr/bin/env python3
"""Lytt på alt - trykk volum på fjernkontroll"""

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

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet! Trykk VOLUM OPP på fjernkontrollen...")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # Vis alle meldinger som ikke er våre egne
        if "/HomeAssistant/" not in msg.topic:
            print(f"\n📨 {msg.topic.replace('/remoteapp/', '')}")
            print(f"   {payload}")
    except:
        if "/HomeAssistant/" not in msg.topic:
            print(f"\n📨 {msg.topic}: {msg.payload.decode()}")

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

print("Lytter i 15 sekunder - trykk VOLUM på fjernkontrollen!")
client.loop_start()
time.sleep(15)
client.loop_stop()
print("\n✅ Ferdig")
