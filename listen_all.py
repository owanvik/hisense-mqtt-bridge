#!/usr/bin/env python3
"""Lytt på ALT fra TV"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HASoverom"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    # Hent volum
    client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
    
def on_message(client, userdata, msg):
    try:
        if msg.payload:
            try:
                payload = json.loads(msg.payload.decode())
                topic_short = "/".join(msg.topic.split("/")[-3:])
                print(f"📨 {topic_short}: {payload}")
            except:
                topic_short = "/".join(msg.topic.split("/")[-3:])
                print(f"📨 {topic_short}: {msg.payload.decode()[:100]}")
    except:
        pass

client = mqtt.Client(
    client_id=CLIENT_ID,
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

print("⏳ Lytter - trykk Ctrl+C for å stoppe")
print("👉 Bruk fjernkontroll og trykk volume opp/ned!")
print("="*50)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n👋 Ferdig!")
