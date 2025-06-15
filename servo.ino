// KODE UNTUK ARDUINO UNO (DENGAN TAMBAHAN UNTUK PENGIRIMAN DATA JSON)

// ======================= LIBRARY =======================
#include <Servo.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h> // <-- Pastikan library ini sudah diinstal via Library Manager

// ======================= KONSTANTA & PIN =======================
// --- KONSTANTA SENSOR TEGANGAN ---
const int sensorPin = A0;
const float VREF = 5.0; // Sesuaikan jika menggunakan Arduino 3.3V
const float voltageDividerFactor = 2.291566667; // Sesuaikan berdasarkan kalibrasi Anda

// --- PIN SERVO DAN KOMUNIKASI ---
const int SERVO_ELEVASI_PIN = 2;   // Servo Sumbu Y (Vertikal)
const int SERVO_AZIMUTH_PIN = 3;   // Servo Sumbu X (Horizontal)
const int ESP32CAM_RX_PIN = 10;
const int ESP32CAM_TX_PIN = 11;
SoftwareSerial espSerial(ESP32CAM_RX_PIN, ESP32CAM_TX_PIN);

// --- Objek Servo ---
Servo servoAzimuth;
Servo servoElevasi;

// --- Variabel Global ---
float currentAngleAzimuth = 80.0;
float currentAngleElevasi = 80.0;
float targetAngleAzimuth = 80.0;
float targetAngleElevasi = 80.0;
const float MIN_ANGLE_AZ = 45;
const float MAX_ANGLE_AZ = 135;
const float MIN_ANGLE_EL = 45;
const float MAX_ANGLE_EL = 135;
const float TARGET_OPTIMAL_X_NORM = 0.4597;
const float TARGET_OPTIMAL_Y_NORM = 0.0994;
const float KP_X = 25.0; // Gain kontroler, perlu di-tuning
const float KP_Y = 25.0; // Gain kontroler, perlu di-tuning
const float SERVO_STEP_SIZE = 1.0;
const int SERVO_MOVE_DELAY = 15;
const byte numChars = 64;
char receivedChars[numChars];
boolean newData = false;
float light_cx_from_esp = -1.0;
float light_cy_from_esp = -1.0;
float currentMeasuredVoltage = 0.0;

// ======================= FUNGSI-FUNGSI ASLI ANDA =======================
// (Tidak ada yang diubah di sini, semua fungsi asli Anda tetap utuh)

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (espSerial.available() > 0 && newData == false) {
        rc = espSerial.read();
        if (recvInProgress == true) {
            if (rc != endMarker) {
                if (ndx < numChars - 1) {
                    receivedChars[ndx] = rc;
                    ndx++;
                }
            } else {
                receivedChars[ndx] = '\0';
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        } else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

void readAndPrintVoltage() {
    int currentAnalogValue = analogRead(sensorPin);
    float currentVoltageAtADC = (float)currentAnalogValue * (VREF / 1023.0);
    currentMeasuredVoltage = currentVoltageAtADC * voltageDividerFactor;
}

void moveServosSmoothly() {
    while (abs(targetAngleAzimuth - currentAngleAzimuth) > SERVO_STEP_SIZE / 2) {
        if (targetAngleAzimuth > currentAngleAzimuth) currentAngleAzimuth += SERVO_STEP_SIZE;
        else currentAngleAzimuth -= SERVO_STEP_SIZE;
        currentAngleAzimuth = constrain(currentAngleAzimuth, MIN_ANGLE_AZ, MAX_ANGLE_AZ);
        servoAzimuth.write(currentAngleAzimuth);
        delay(SERVO_MOVE_DELAY);
    }
    servoAzimuth.write(targetAngleAzimuth);
    currentAngleAzimuth = targetAngleAzimuth;

    while (abs(targetAngleElevasi - currentAngleElevasi) > SERVO_STEP_SIZE / 2) {
        if (targetAngleElevasi > currentAngleElevasi) currentAngleElevasi += SERVO_STEP_SIZE;
        else currentAngleElevasi -= SERVO_STEP_SIZE;
        currentAngleElevasi = constrain(currentAngleElevasi, MIN_ANGLE_EL, MAX_ANGLE_EL);
        servoElevasi.write(currentAngleElevasi);
        delay(SERVO_MOVE_DELAY);
    }
    servoElevasi.write(targetAngleElevasi);
    currentAngleElevasi = targetAngleElevasi;
}

void parseAndControl() {
    if (newData == true) {
        char tempChars[numChars];
        strcpy(tempChars, receivedChars);
        char* strtokIndx;
        strtokIndx = strtok(tempChars, ",");
        if (strtokIndx == NULL) { newData = false; return; }
        light_cx_from_esp = atof(strtokIndx);
        strtokIndx = strtok(NULL, ",");
        if (strtokIndx == NULL) { newData = false; return; }
        light_cy_from_esp = atof(strtokIndx);
        if (light_cx_from_esp == -1.0 && light_cy_from_esp == -1.0) {
            targetAngleAzimuth = 80.0;
            targetAngleElevasi = 80.0;
        } else if (light_cx_from_esp >= 0.0 && light_cx_from_esp <= 1.0 && light_cy_from_esp >= 0.0 && light_cy_from_esp <= 1.0) {
            float error_x = light_cx_from_esp - TARGET_OPTIMAL_X_NORM;
            float error_y = light_cy_from_esp - TARGET_OPTIMAL_Y_NORM;
            float newTargetAzimuth = currentAngleAzimuth - (KP_X * error_x);
            float newTargetElevasi = currentAngleElevasi - (KP_Y * error_y);
            targetAngleAzimuth = constrain(newTargetAzimuth, MIN_ANGLE_AZ, MAX_ANGLE_AZ);
            targetAngleElevasi = constrain(newTargetElevasi, MIN_ANGLE_EL, MAX_ANGLE_EL);
        }
        newData = false;
    }
}
// ======================= FUNGSI BARU UNTUK MQTT =======================
void kirimDataKePC() {
    StaticJsonDocument<256> doc;

    // Masukkan semua data yang relevan ke dalam dokumen JSON
    doc["koordinat_x"] = light_cx_from_esp;
    doc["koordinat_y"] = light_cy_from_esp;
    doc["tegangan_v"] = currentMeasuredVoltage;
    doc["rotasi_azimuth_deg"] = currentAngleAzimuth;
    doc["rotasi_elevasi_deg"] = currentAngleElevasi;

    // Kirim data JSON yang sudah diformat ke port Serial (USB)
    serializeJson(doc, Serial);
    Serial.println(); // Beri newline sebagai penanda akhir pesan
}

// ======================= FUNGSI SETUP DAN LOOP =======================
void setup() {
    Serial.begin(9600);
    espSerial.begin(9600);
    servoAzimuth.attach(SERVO_AZIMUTH_PIN);
    servoElevasi.attach(SERVO_ELEVASI_PIN);
    servoAzimuth.write(80);
    servoElevasi.write(80);
    currentAngleAzimuth = 80.0;
    currentAngleElevasi = 80.0;
    targetAngleAzimuth = 80.0;
    targetAngleElevasi = 80.0;
    Serial.println("Arduino UNO Siap. Mengirim JSON ke PC.");
}

void loop() {
    // 1. Baca sensor lokal
    readAndPrintVoltage();
    // 2. Terima data dari ESP dan proses
    recvWithStartEndMarkers();
    parseAndControl();
    // 3. Gerakkan motor
    moveServosSmoothly();
    // 4. Kirim semua status terakhir ke PC untuk MQTT
    kirimDataKePC();
    // 5. Beri jeda singkat
    delay(5000);
}
