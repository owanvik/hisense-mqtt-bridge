#!/usr/bin/env python3
"""Debug: Se alle volum-meldinger fra TV"""

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
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "volume" in msg.topic.lower() or "volume" in str(payload).lower():
            print(f"\n📨 Topic: {msg.topic}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
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

print("\n📊 Henter volum...")
client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
time.sleep(2)

print("\n📤 Sender KEY_VOLUMEUP...")
client.publish("/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey",
              json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"}))
time.sleep(2)

print("\n📊 Henter volum igjen...")
client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
time.sleep(2)

client.loop_stop()
