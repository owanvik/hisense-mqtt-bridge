#!/usr/bin/env python3
"""Test ulike SSL-konfigurasjoner for Hisense TV"""

import ssl
import socket
import time
import paho.mqtt.client as mqtt

TV_IP = "10.0.0.109"
PORT = 36669

def test_connection(use_ssl, ssl_version=None, description=""):
    print(f"\n{'='*50}")
    print(f"🧪 Test: {description}")
    print(f"{'='*50}")
    
    connected = [False]
    
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ MQTT tilkobling vellykket!")
            connected[0] = True
            client.subscribe("#")
        else:
            codes = {
                0: "OK",
                1: "Feil protokoll",
                2: "Ugyldig klient-ID", 
                3: "Server utilgjengelig",
                4: "Feil brukernavn/passord",
                5: "Ikke autorisert"
            }
            print(f"❌ MQTT feil (rc={rc}): {codes.get(rc, 'Ukjent')}")

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="ignore")[:100]
        print(f"📩 {msg.topic}: {payload}")

    def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
        print(f"🔌 Frakoblet (rc={rc})")

    client = mqtt.Client(
        client_id="HisenseTest",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set("hisenseservice", "multimqttservice")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    if use_ssl:
        try:
            if ssl_version:
                ssl_context = ssl.SSLContext(ssl_version)
            else:
                ssl_context = ssl.create_default_context()
            
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Tillat alle ciphers
            try:
                ssl_context.set_ciphers('ALL:@SECLEVEL=0')
            except:
                pass
            
            client.tls_set_context(ssl_context)
        except Exception as e:
            print(f"SSL setup feilet: {e}")
            return False
    
    try:
        client.connect(TV_IP, PORT, keepalive=10)
        client.loop_start()
        
        # Vent på tilkobling
        for i in range(10):
            if connected[0]:
                break
            time.sleep(0.5)
        
        if connected[0]:
            # Prøv å hente TV-status
            client.publish("/remoteapp/tv/ui_service/HisenseTest/actions/gettvstate", "")
            time.sleep(2)
        
        client.loop_stop()
        client.disconnect()
        return connected[0]
        
    except Exception as e:
        print(f"Feil: {e}")
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
        return False

# Test nettverkstilgang først
print(f"🔄 Sjekker om port {PORT} er åpen på {TV_IP}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((TV_IP, PORT))
    sock.close()
    
    if result == 0:
        print(f"✅ Port {PORT} er åpen!")
    else:
        print(f"❌ Port {PORT} er lukket. Er TV-en slått på?")
        exit(1)
except Exception as e:
    print(f"❌ Nettverksfeil: {e}")
    exit(1)

# Prøv forskjellige konfigurasjoner
results = []

# Test 1: Uten SSL
results.append(("Uten SSL", test_connection(False, description="Uten SSL")))

# Test 2: SSL med default context
results.append(("SSL Default", test_connection(True, description="SSL med default context")))

# Test 3: TLS 1.2
try:
    results.append(("TLS 1.2", test_connection(True, ssl.PROTOCOL_TLS_CLIENT, "TLS 1.2")))
except:
    pass

# Oppsummering
print("\n" + "="*50)
print("📊 OPPSUMMERING")
print("="*50)
for name, success in results:
    status = "✅ OK" if success else "❌ Feilet"
    print(f"   {name}: {status}")

if any(s for _, s in results):
    print("\n🎉 Minst én konfigurasjon fungerte!")
else:
    print("\n💡 Ingen konfigurasjoner fungerte.")
    print("   Mulige årsaker:")
    print("   - TV-en må kanskje autentiseres via RemoteNOW-appen først")
    print("   - TV-modellen bruker kanskje en annen protokoll")
    print("   - Prøv å starte RemoteNOW-appen på telefonen først")
