#!/usr/bin/env python3
"""
Hisense TV MQTT Controller
Kobler til Hisense TV via den innebygde MQTT brokeren.

Developer credentials:
- Port: 36669
- Username: hisenseservice
- Password: multimqttservice
"""

import ssl
import json
import time
import paho.mqtt.client as mqtt

# === KONFIGURER DIN TV HER ===
TV_IP = "10.0.0.109"
CLIENT_ID = "HomeAssistant"  # Kan være hva som helst
# =============================

# MQTT Credentials (standard for alle Hisense TV-er)
MQTT_PORT = 36669
MQTT_USERNAME = "hisenseservice"
MQTT_PASSWORD = "multimqttservice"

# MQTT Topics
TOPICS = {
    "subscribe_all": "#",
    "tv_state": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/gettvstate",
    "source_list": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/sourcelist",
    "app_list": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/applist",
    "get_volume": f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume",
    "change_volume": f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume",
    "send_key": f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
    "launch_app": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/launchapp",
    "change_source": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/changesource",
    "auth_code": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode",
}

# Tilgjengelige taster
KEYS = [
    "KEY_POWER", "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT",
    "KEY_OK", "KEY_BACK", "KEY_MENU", "KEY_HOME", "KEY_EXIT",
    "KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE",
    "KEY_PLAY", "KEY_PAUSE", "KEY_STOP", "KEY_FORWARDS", "KEY_BACK",
    "KEY_0", "KEY_1", "KEY_2", "KEY_3", "KEY_4",
    "KEY_5", "KEY_6", "KEY_7", "KEY_8", "KEY_9",
]


class HisenseTV:
    def __init__(self, ip: str, use_ssl: bool = True):
        self.ip = ip
        self.use_ssl = use_ssl
        self.client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
        self.connected = False
        
        # Set credentials
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Setup SSL for newer TVs (self-signed cert)
        if use_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(ssl_context)
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Koblet til Hisense TV på {self.ip}")
            self.connected = True
            # Subscribe to all topics
            client.subscribe("#")
        else:
            print(f"❌ Tilkobling feilet med kode: {rc}")
            self.connected = False
    
    def _on_message(self, client, userdata, msg):
        print(f"\n📩 Topic: {msg.topic}")
        try:
            payload = msg.payload.decode('utf-8')
            # Prøv å parse som JSON
            try:
                data = json.loads(payload)
                print(f"   Data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"   Data: {payload}")
        except Exception as e:
            print(f"   Raw: {msg.payload}")
    
    def _on_disconnect(self, client, userdata, rc):
        print(f"🔌 Frakoblet fra TV (kode: {rc})")
        self.connected = False
    
    def connect(self):
        """Koble til TV-en"""
        print(f"🔄 Kobler til {self.ip}:{MQTT_PORT}...")
        try:
            self.client.connect(self.ip, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            time.sleep(2)  # Vent på tilkobling
            return self.connected
        except Exception as e:
            print(f"❌ Feil ved tilkobling: {e}")
            if self.use_ssl:
                print("💡 Tips: Prøv med use_ssl=False hvis TV-en din ikke støtter SSL")
            return False
    
    def disconnect(self):
        """Koble fra TV-en"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def authenticate(self, code: str):
        """Send autentiseringskode (4-sifret kode vist på TV-skjermen)"""
        payload = json.dumps({"authNum": code})
        self.client.publish(TOPICS["auth_code"], payload)
        print(f"🔐 Sendte autentiseringskode: {code}")
    
    def send_key(self, key: str):
        """Send tastetrykk til TV-en"""
        if key not in KEYS:
            print(f"⚠️  Ukjent tast: {key}. Tilgjengelige: {KEYS}")
            return
        self.client.publish(TOPICS["send_key"], key)
        print(f"🎮 Sendte tast: {key}")
    
    def power_off(self):
        """Sett TV i standby"""
        self.send_key("KEY_POWER")
    
    def get_tv_state(self):
        """Hent TV-status"""
        self.client.publish(TOPICS["tv_state"], "")
        print("📺 Henter TV-status...")
    
    def get_sources(self):
        """Hent liste over kilder"""
        self.client.publish(TOPICS["source_list"], "")
        print("📋 Henter kildeliste...")
    
    def get_apps(self):
        """Hent liste over apper"""
        self.client.publish(TOPICS["app_list"], "")
        print("📱 Henter appliste...")
    
    def get_volume(self):
        """Hent nåværende volum"""
        self.client.publish(TOPICS["get_volume"], "")
        print("🔊 Henter volum...")
    
    def set_volume(self, level: int):
        """Sett volum (0-100)"""
        if 0 <= level <= 100:
            self.client.publish(TOPICS["change_volume"], str(level))
            print(f"🔊 Satte volum til: {level}")
        else:
            print("⚠️  Volum må være mellom 0 og 100")
    
    def change_source(self, source_id: str, source_name: str = ""):
        """Bytt kilde"""
        payload = json.dumps({"sourceid": source_id, "sourcename": source_name})
        self.client.publish(TOPICS["change_source"], payload)
        print(f"📺 Byttet til kilde: {source_id}")
    
    def launch_app(self, app_name: str, url: str):
        """Start en app"""
        payload = json.dumps({
            "name": app_name,
            "urlType": 37,
            "storeType": 0,
            "url": url
        })
        self.client.publish(TOPICS["launch_app"], payload)
        print(f"🚀 Starter app: {app_name}")
    
    def launch_youtube(self):
        """Start YouTube"""
        self.launch_app("YouTube", "youtube")
    
    def launch_netflix(self):
        """Start Netflix"""
        self.launch_app("Netflix", "netflix")
    
    def launch_amazon_prime(self):
        """Start Amazon Prime Video"""
        self.launch_app("Amazon", "amazon")


def main():
    """Interaktiv demo"""
    print("=" * 50)
    print("   HISENSE TV MQTT CONTROLLER")
    print("=" * 50)
    
    # Sjekk at IP er konfigurert
    if "XXX" in TV_IP:
        print("\n⚠️  Du må konfigurere TV_IP øverst i filen!")
        print("   Finn TV-ens IP-adresse i nettverksinnstillingene.")
        return
    
    tv = HisenseTV(TV_IP, use_ssl=True)
    
    if not tv.connect():
        print("\n💡 Prøver uten SSL...")
        tv = HisenseTV(TV_IP, use_ssl=False)
        if not tv.connect():
            print("❌ Kunne ikke koble til TV-en.")
            return
    
    print("\n📺 Tilgjengelige kommandoer:")
    print("   1. Hent TV-status")
    print("   2. Hent kilder")
    print("   3. Hent apper")
    print("   4. Hent volum")
    print("   5. Start YouTube")
    print("   6. Start Netflix")
    print("   7. Send tast (f.eks. KEY_UP)")
    print("   8. Autentiser (hvis påkrevd)")
    print("   0. Avslutt")
    
    try:
        while True:
            time.sleep(0.5)
            choice = input("\nVelg (0-8): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                tv.get_tv_state()
            elif choice == "2":
                tv.get_sources()
            elif choice == "3":
                tv.get_apps()
            elif choice == "4":
                tv.get_volume()
            elif choice == "5":
                tv.launch_youtube()
            elif choice == "6":
                tv.launch_netflix()
            elif choice == "7":
                key = input("Tast (f.eks. KEY_UP): ").strip().upper()
                tv.send_key(key)
            elif choice == "8":
                code = input("4-sifret kode fra TV-skjermen: ").strip()
                tv.authenticate(code)
            
            time.sleep(1)  # Vent på svar
    
    except KeyboardInterrupt:
        print("\n")
    finally:
        tv.disconnect()
        print("👋 Avsluttet")


if __name__ == "__main__":
    main()
