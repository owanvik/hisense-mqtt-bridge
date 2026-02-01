#!/usr/bin/env python3
"""Lytt på volum - bruk fysisk fjernkontroll"""

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
    print(f"✅ Tilkoblet! Lytter på alle meldinger...")
    print("👉 Bruk FYSISK fjernkontroll og trykk volume opp/ned!")
    print("="*50)
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic_short = msg.topic.split("/")[-1]
        
        # Vis alle volum-relaterte meldinger
        if "volume" in msg.topic.lower() or "volume" in str(payload).lower():
            print(f"📨 {topic_short}: {payload}")
            
            # Spesielt interessert i volume_type 0
            if payload.get("volume_type") == 0:
                print(f"   ⬆️ TV VOLUM: {payload.get('volume_value')}")
                
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

print("\n⏳ Lytter i 30 sekunder - bruk fjernkontrollen nå!")
try:
    client.loop_start()
    time.sleep(30)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    print("\n👋 Ferdig!")
