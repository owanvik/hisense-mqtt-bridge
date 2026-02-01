#!/usr/bin/env python3
"""Par ny bruker med TV"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HASoverom"  # NY UNIK ID

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

auth_needed = False
auth_done = False

def on_connect(client, userdata, flags, rc, props=None):
    global auth_needed
    print(f"✅ Tilkoblet TV med ny bruker: {CLIENT_ID}")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    global auth_needed, auth_done
    
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
    except:
        payload = {}
    
    # Ny bruker vil alltid trigge auth
    if "authentication" in topic and "code" not in topic:
        print(f"🔐 Auth melding mottatt!")
        if not payload or payload == {} or payload.get("result") != 1:
            auth_needed = True
            print("\n" + "="*50)
            print("📺 SE PÅ TV-SKJERMEN FOR EN 4-SIFRET KODE!")
            print("="*50)
        else:
            print("✅ Allerede autorisert!")
            auth_done = True
            
    elif "authenticationcode" in topic:
        print(f"🔑 Auth respons: {payload}")
        if payload.get("result") == 1:
            print("\n✅ AUTENTISERING VELLYKKET!")
            auth_done = True

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

print(f"🔄 Kobler til TV med NY bruker: {CLIENT_ID}")
print("📺 Hold øye med TV-skjermen!\n")

client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

# Vent på auth-melding
for i in range(15):
    time.sleep(1)
    if auth_needed or auth_done:
        break
    if i == 5:
        # Trigger auth ved å be om data
        client.publish(f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/gettvstate", "")

if auth_needed and not auth_done:
    code = input("\nSkriv inn koden fra TV: ").strip()
    
    if code:
        payload = json.dumps({"authNum": code})
        topic = f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode"
        print(f"📤 Sender kode: {code}")
        client.publish(topic, payload)
        
        for i in range(5):
            time.sleep(1)
            if auth_done:
                break
                
        if auth_done:
            # Test at det fungerer
            print("\n🧪 Tester kontroll...")
            time.sleep(1)
            client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
                          json.dumps({"keytype": "keypress", "keyvalue": "KEY_MUTE"}))
            print("📤 Sendte MUTE - så du mute-ikonet på TV?")
            time.sleep(2)
            client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
                          json.dumps({"keytype": "keypress", "keyvalue": "KEY_MUTE"}))
            print("📤 Sendte UNMUTE")
elif auth_done:
    print("\n🎉 Bruker allerede autorisert!")
else:
    print("\n⚠️ Fikk ingen auth-forespørsel fra TV")
    print("   TV-en viser kanskje koden automatisk?")
    code = input("Hvis du ser en kode på TV, skriv den inn: ").strip()
    if code:
        payload = json.dumps({"authNum": code})
        topic = f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode"
        client.publish(topic, payload)
        time.sleep(3)

client.loop_stop()
