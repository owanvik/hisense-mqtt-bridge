#!/usr/bin/env python3
"""Debug: Test at TV-klienten faktisk sender og mottar"""

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

received_messages = []

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet! rc={rc}")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    received_messages.append(msg.topic)
    try:
        payload = json.loads(msg.payload.decode())
        if "volume_value" in payload:
            print(f"🔊 Volum: {payload['volume_value']}")
    except:
        pass

# Opprett klient med SAMME client_id som bridge bruker
client = mqtt.Client(
    client_id="HomeAssistant",  # Samme som i bridge
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

# Hent volum først
print("\n📊 Henter volum...")
client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
time.sleep(1)

volum_før = None
for msg in received_messages:
    pass
    
# Send volumeup
print("\n📤 Sender KEY_VOLUMEUP...")
topic = "/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey"
payload = json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"})
result = client.publish(topic, payload)
print(f"   Publish result: rc={result.rc}, mid={result.mid}")

time.sleep(1)

# Hent volum igjen
print("\n📊 Henter volum igjen...")
client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
time.sleep(2)

print(f"\n📬 Mottok {len(received_messages)} meldinger totalt")

client.loop_stop()
client.disconnect()
