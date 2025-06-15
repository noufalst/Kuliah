import serial
import paho.mqtt.client as mqtt
import time
import json

# --- KONFIGURASI (SESUAIKAN DI SINI) ---
# Temukan port ini di Device Manager (Windows) atau dengan 'ls /dev/tty.*' (Mac/Linux)
SERIAL_PORT = 'COM13'  # CONTOH: 'COM3' atau '/dev/ttyUSB0' atau '/dev/tty.usbmodem14201'
BAUD_RATE = 9600

# Jika broker (Mosquitto) ada di komputer ini, biarkan 'localhost'.
MQTT_BROKER_HOST = '192.168.28.10'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = 'projek/data_cahaya' # Topik yang akan digunakan

# --- INISIALISASI ---
print("Memulai MQTT Bridge...")

# Inisialisasi Koneksi Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print(f"Berhasil terhubung ke port serial {SERIAL_PORT}")
    time.sleep(2) # Beri waktu agar koneksi stabil
except serial.SerialException as e:
    print(f"GAGAL terhubung ke port serial {SERIAL_PORT}. Error: {e}")
    print("Pastikan Arduino terhubung, port sudah benar, dan tidak ada program lain yang menggunakannya.")
    exit()

# Inisialisasi MQTT Client
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Berhasil terhubung ke MQTT Broker!")
    else:
        print(f"Gagal terhubung ke MQTT Broker. Kode: {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "arduino_bridge_publisher")
client.on_connect = on_connect
try:
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
except Exception as e:
    print(f"GAGAL terhubung ke MQTT Broker di {MQTT_BROKER_HOST}. Error: {e}")
    print("Pastikan Mosquitto atau broker lain sudah berjalan.")
    exit()

client.loop_start()

# --- LOOP UTAMA ---
try:
    while True:
        if ser.in_waiting > 0:
            # Baca satu baris data dari Arduino
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if line:
                print(f"Diterima dari Arduino: {line}")
                # Kirim data mentah (yang sudah berupa JSON) ke broker
                result = client.publish(MQTT_TOPIC, line)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"   -> Gagal mempublikasikan pesan.")
                else:
                    print(f"   -> Dipublikasikan ke topik '{MQTT_TOPIC}'")

except KeyboardInterrupt:
    print("\nProgram dihentikan.")
finally:
    # Membersihkan koneksi
    ser.close()
    client.loop_stop()
    client.disconnect()
    print("Koneksi serial dan MQTT ditutup.")
