// KODE UNTUK ESP32-CAM (MODIFIKASI: MENGIRIM SETIAP 10 DETIK)

#include "esp_camera.h"
#include <Arduino.h> 

// --- (Definisi Pin Kamera & Fungsi initCamera, findLightCentroid TETAP SAMA seperti sebelumnya) ---
// Pastikan initCamera menggunakan PIXFORMAT_GRAYSCALE dan FRAMESIZE_QQVGA
// Pastikan findLightCentroid sudah dituning dan bekerja dengan baik
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1 
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

int frameWidth = 0;
int frameHeight = 0;

bool initCamera() { /* ... salin dari kode sebelumnya ... */ 
    camera_config_t config;
    // ...
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.frame_size = FRAMESIZE_QQVGA; 
    config.pixel_format = PIXFORMAT_GRAYSCALE; 
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location = CAMERA_FB_IN_PSRAM; 
    config.jpeg_quality = 12; 
    config.fb_count = 1;     

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) { return false; }
    sensor_t * s = esp_camera_sensor_get();
    frameWidth = resolution[config.frame_size].width;
    frameHeight = resolution[config.frame_size].height;
    return true;
}
bool findLightCentroid(camera_fb_t *fb, float &cx_norm, float &cy_norm, float &area_norm) { /* ... salin dari kode sebelumnya ... */ 
    if (!fb || !fb->buf || fb->format != PIXFORMAT_GRAYSCALE) {
        return false;
    }
    uint8_t *pixels = (uint8_t *)fb->buf;
    long sum_x = 0; 
    long sum_y = 0;
    int bright_pixel_count = 0;
    uint8_t threshold_terang = 220; 

    for (int y = 0; y < fb->height; y++) {
        for (int x = 0; x < fb->width; x++) {
            if (pixels[y * fb->width + x] > threshold_terang) {
                sum_x += x;
                sum_y += y;
                bright_pixel_count++;
            }
        }
    }
    int min_pixels_needed = (fb->width * fb->height) * 0.0005; 
    int max_pixels_allowed = (fb->width * fb->height) * 0.25;  

    if (bright_pixel_count > min_pixels_needed && bright_pixel_count < max_pixels_allowed) {
        cx_norm = (float)sum_x / (float)bright_pixel_count / (float)fb->width;
        cy_norm = (float)sum_y / (float)bright_pixel_count / (float)fb->height;
        area_norm = (float)bright_pixel_count / (float)(fb->width * fb->height);
        return true;
    }
    return false; 
}


void setup() {
    Serial.begin(9600); // Gunakan baud rate yang stabil
    if (!initCamera()) {
        delay(3000);
        ESP.restart();
    }
}

void loop() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) { delay(100); return; }

    float p_x_norm, p_y_norm, area_norm;
    bool terdeteksi = findLightCentroid(fb, p_x_norm, p_y_norm, area_norm);
    
    esp_camera_fb_return(fb);

    String dataToSend;
    if (terdeteksi) {
        dataToSend = "<" + String(p_x_norm, 4) + "," + String(p_y_norm, 4) + ">";
    } else {
        dataToSend = "<-1.0,-1.0>"; // Placeholder
    }
    
    Serial.println(dataToSend);
    
    // PERUBAHAN UTAMA: Jeda 10 detik sebelum mengirim paket data berikutnya
    delay(5000); 
}