#!/usr/bin/env python3
"""Test tilkobling til Hisense TV"""

import ssl
import socket
import time
import paho.mqtt.client as mqtt

TV_IP = "10.0.0.109"
PORT = 36669

connected = False
messages_received = []

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        print("✅ MQTT tilkobling vellykket!")
        connected = True
        client.subscribe("#")
    else:
        codes = {
            1: "Feil protokoll",
            2: "Ugyldig klient-ID", 
            3: "Server utilgjengelig",
            4: "Feil brukernavn/passord",
            5: "Ikke autorisert"
        }
        print(f"❌ MQTT feil: {codes.get(rc, f'Ukjent feil {rc}')}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")[:200]
    print(f"📩 {msg.topic}: {payload}")
    messages_received.append(msg.topic)

# Test basic connectivity first
print(f"🔄 Tester tilkobling til {TV_IP}:{PORT}...")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((TV_IP, PORT))
    sock.close()
    
    if result == 0:
        print(f"✅ Port {PORT} er åpen på {TV_IP}")
    else:
        print(f"❌ Port {PORT} er lukket eller TV-en er av")
        print("💡 Sjekk at TV-en er slått på")
        exit(1)
except Exception as e:
    print(f"❌ Nettverksfeil: {e}")
    exit(1)

# Try with SSL first
print("\n🔐 Prøver med SSL...")
client = mqtt.Client(
    client_id="TestClient",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set("hisenseservice", "multimqttservice")

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
client.tls_set_context(ssl_context)

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(TV_IP, PORT, keepalive=10)
    client.loop_start()
    time.sleep(3)
    
    if connected:
        # Try to get TV state
        print("\n📺 Henter TV-status...")
        client.publish("/remoteapp/tv/ui_service/TestClient/actions/gettvstate", "")
        time.sleep(2)
    
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"SSL feilet: {e}")

# Try without SSL (new connection without TLS context)
print("\n🔓 Prøver uten SSL...")
connected = False
client2 = mqtt.Client(
    client_id="TestClient",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client2.username_pw_set("hisenseservice", "multimqttservice")
client2.on_connect = on_connect
client2.on_message = on_message

try:
    client2.connect(TV_IP, PORT, keepalive=10)
    client2.loop_start()
    
    # Wait for connection with timeout
    for i in range(10):
        if connected:
            break
        time.sleep(0.5)
    
    if connected:
        print("\n📺 Henter TV-status...")
        client2.publish("/remoteapp/tv/ui_service/TestClient/actions/gettvstate", "")
        time.sleep(2)
    
    client2.loop_stop()
    client2.disconnect()
except Exception as e2:
    print(f"Uten SSL feilet også: {e2}")

if connected:
    print("\n🎉 TV-en er klar for kontroll!")
    print(f"   Mottok {len(messages_received)} meldinger")
else:
    print("\n💡 Sjekk at TV-en er slått på og på samme nettverk")
