import paho.mqtt.client as mqtt
import json

# --- KONFIGURASI (SESUAIKAN DI SINI) ---
# GANTI dengan IP Address LOKAL dari komputer yang menjalankan broker
# Untuk mencari IP: ketik 'ipconfig' (Windows) atau 'ifconfig' (Mac/Linux) di terminal
MQTT_BROKER_HOST = '192.168.205.248' # CONTOH! GANTI DENGAN IP ANDA
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = 'projek/data_cahaya' # Harus sama persis dengan di bridge

# --- FUNGSI CALLBACK ---
def on_connect(client, userdata, flags, rc):
    """Callback yang dipanggil saat berhasil terhubung ke broker."""
    if rc == 0:
        print("Berhasil terhubung ke MQTT Broker!")
        print(f"Berlangganan (subscribing) ke topik: '{MQTT_TOPIC}'")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Gagal terhubung, kode: {rc}")

def on_message(client, userdata, msg):
    """Callback yang dipanggil saat ada pesan baru di topik yang dilanggani."""
    print("\n--- Pesan Baru Diterima ---")
    try:
        # Decode pesan dari bytes menjadi string, lalu parse sebagai JSON
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)

        # Tampilkan data dengan rapi menggunakan metode .get() untuk keamanan
        print(f"  Koordinat X  : {data.get('koordinat_x', 'N/A'):.4f}")
        print(f"  Koordinat Y  : {data.get('koordinat_y', 'N/A'):.4f}")
        print(f"  Tegangan     : {data.get('tegangan_v', 'N/A'):.2f} V")
        print(f"  Sudut Azimuth: {data.get('rotasi_azimuth_deg', 'N/A'):.1f}°")
        print(f"  Sudut Elevasi: {data.get('rotasi_elevasi_deg', 'N/A'):.1f}°")

    except Exception as e:
        print(f"Gagal memproses pesan. Error: {e}")
        print(f"Payload mentah: {msg.payload}")


# --- INISIALISASI DAN LOOP ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "laptop_subscriber")
client.on_connect = on_connect
client.on_message = on_message

print(f"Mencoba terhubung ke MQTT Broker di {MQTT_BROKER_HOST}...")
try:
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
except Exception as e:
    print(f"GAGAL terhubung. Error: {e}")
    print("Pastikan IP Broker sudah benar dan kedua komputer berada di jaringan WiFi yang sama.")
    exit()

# loop_forever() akan menahan program agar terus berjalan dan mendengarkan pesan
client.loop_forever()
