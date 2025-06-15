import cv2
import os
import numpy as np
import pandas as pd

def ekstrak_fitur_area_terang(path_gambar):
    """
    Mengekstrak fitur ukuran dan posisi area terang dari sebuah gambar.

    Args:
        path_gambar (str): Path ke file gambar.

    Returns:
        dict: Dictionary berisi fitur-fitur yang diekstrak (nama_file, area_norm,
              pusat_x_norm, pusat_y_norm, bbox_x_norm, bbox_y_norm,
              bbox_w_norm, bbox_h_norm, area_terang_ditemukan)
              atau None jika gambar tidak dapat diproses.
    """
    img = cv2.imread(path_gambar)
    if img is None:
        print(f"Error: Tidak dapat membaca gambar {path_gambar}")
        return None

    tinggi_img, lebar_img = img.shape[:2]
    nama_file = os.path.basename(path_gambar)

    # 1. Konversi ke Grayscale
    gambar_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Thresholding (Otsu's Binarization untuk menentukan ambang batas otomatis)
    # Ini akan memisahkan piksel terang (objek) dari piksel gelap (latar belakang)
    # Piksel di atas ambang batas akan menjadi putih (255), di bawahnya hitam (0)
    ret, gambar_thresh = cv2.threshold(gambar_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Operasi Morfologi (Opsional, untuk membersihkan noise)
    # Anda bisa uncomment dan menyesuaikan kernel jika diperlukan
    # kernel = np.ones((5,5), np.uint8)
    # gambar_thresh = cv2.morphologyEx(gambar_thresh, cv2.MORPH_OPEN, kernel) # Menghilangkan noise kecil
    # gambar_thresh = cv2.morphologyEx(gambar_thresh, cv2.MORPH_CLOSE, kernel) # Menutup lubang kecil pada objek

    # 4. Deteksi Kontur
    # Mencari bentuk-bentuk (kontur) pada gambar hasil thresholding
    # cv2.RETR_EXTERNAL hanya mengambil kontur terluar
    # cv2.CHAIN_APPROX_SIMPLE menyederhanakan titik-titik kontur
    kontur, hirarki = cv2.findContours(gambar_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    fitur = {
        'nama_file': nama_file,
        'area_norm': 0.0,
        'pusat_x_norm': 0.5, # Default ke tengah jika tidak ada kontur
        'pusat_y_norm': 0.5, # Default ke tengah jika tidak ada kontur
        'bbox_x_norm': 0.0,
        'bbox_y_norm': 0.0,
        'bbox_w_norm': 0.0,
        'bbox_h_norm': 0.0,
        'area_terang_ditemukan': 0 # 0 jika tidak ditemukan, 1 jika ditemukan
    }

    if not kontur:
        print(f"Info: Tidak ada kontur signifikan ditemukan di {nama_file}")
        return fitur # Mengembalikan nilai default

    # 5. Identifikasi Area Terang Utama (berdasarkan kontur dengan area terbesar)
    kontur_utama_terang = max(kontur, key=cv2.contourArea)
    fitur['area_terang_ditemukan'] = 1

    # --- Ekstraksi Fitur Numerik dari Kontur Utama ---

    # A. Ukuran Area
    area_piksel = cv2.contourArea(kontur_utama_terang)
    fitur['area_norm'] = area_piksel / (lebar_img * tinggi_img)  # Normalisasi area (0-1)

    # B. Posisi Pusat (Centroid)
    M = cv2.moments(kontur_utama_terang)
    if M["m00"] != 0:
        pusat_x = M["m10"] / M["m00"]
        pusat_y = M["m01"] / M["m00"]
        fitur['pusat_x_norm'] = pusat_x / lebar_img    # Normalisasi posisi x (0-1)
        fitur['pusat_y_norm'] = pusat_y / tinggi_img   # Normalisasi posisi y (0-1)
    # else: (nilai default sudah diatur di atas)

    # C. Bounding Box (Kotak Pembatas)
    x, y, w, h = cv2.boundingRect(kontur_utama_terang)
    fitur['bbox_x_norm'] = x / lebar_img      # Normalisasi x_min bounding box
    fitur['bbox_y_norm'] = y / tinggi_img     # Normalisasi y_min bounding box
    fitur['bbox_w_norm'] = w / lebar_img      # Normalisasi lebar bounding box
    fitur['bbox_h_norm'] = h / tinggi_img     # Normalisasi tinggi bounding box

    return fitur

# --- Program Utama ---
if __name__ == "__main__":
    folder_input_gambar = "D:\\Kuliah\\SMV Matkupil\\Tubes\\Data benar\\Data"

    # Cek apakah folder input valid
    if not os.path.isdir(folder_input_gambar):
        print(f"Error: Folder input '{folder_input_gambar}' tidak valid atau belum diatur.")
        print("Silakan ganti 'PATH_FOLDER_GAMBAR_ANDA' dengan path yang benar ke folder gambar Anda.")
        exit()

    # Tentukan nama file CSV untuk output
    file_csv_output = "fitur_area_terang_hasil_ekstraksi.csv"
    # Selalu simpan file CSV di folder tempat script dijalankan
    path_output_csv = os.path.join(os.getcwd(), file_csv_output)
    # Jika ingin menyimpan di direktori yang sama dengan folder gambar, gunakan baris di bawah ini (commented):
    # path_output_csv = os.path.join(os.path.dirname(folder_input_gambar), file_csv_output)


    ekstensi_gambar_diizinkan = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif')
    kumpulan_semua_fitur = []

    print(f"Memulai pemrosesan gambar di folder: {folder_input_gambar}")
    # Iterasi semua file dalam folder yang ditentukan
    for nama_file_gambar in os.listdir(folder_input_gambar):
        if nama_file_gambar.lower().endswith(ekstensi_gambar_diizinkan):
            path_lengkap_gambar = os.path.join(folder_input_gambar, nama_file_gambar)
            print(f"  Memproses: {nama_file_gambar}...")

            hasil_fitur = ekstrak_fitur_area_terang(path_lengkap_gambar)

            if hasil_fitur:
                kumpulan_semua_fitur.append(hasil_fitur)
            else:
                # Jika ada error pembacaan gambar, buat entri default agar jumlah baris tetap sama jika diperlukan
                kumpulan_semua_fitur.append({
                    'nama_file': nama_file_gambar, 'area_norm': 0.0,
                    'pusat_x_norm': 0.5, 'pusat_y_norm': 0.5,
                    'bbox_x_norm': 0.0, 'bbox_y_norm': 0.0,
                    'bbox_w_norm': 0.0, 'bbox_h_norm': 0.0,
                    'area_terang_ditemukan': -1 # -1 untuk menandakan error baca gambar
                })


    if not kumpulan_semua_fitur:
        print("Tidak ada gambar yang diproses atau tidak ada fitur yang dapat diekstrak.")
        exit()

    # Konversi list of dictionaries ke Pandas DataFrame untuk kemudahan analisis dan penyimpanan
    df_hasil_fitur = pd.DataFrame(kumpulan_semua_fitur)

    # Tampilkan beberapa baris pertama dari DataFrame
    print("\n--- Hasil Ekstraksi Fitur (Beberapa Baris Awal) ---")
    print(df_hasil_fitur.head())

    # Simpan DataFrame ke file CSV
    try:
        df_hasil_fitur.to_csv(path_output_csv, index=False)
        print(f"\nFitur berhasil diekstrak dan disimpan ke file CSV: {path_output_csv}")
    except Exception as e:
        print(f"\nTerjadi error saat menyimpan file CSV: {e}")
        print("Pastikan Anda memiliki izin tulis di lokasi tersebut.")
        print("DataFrame yang akan disimpan:")
        print(df_hasil_fitur)