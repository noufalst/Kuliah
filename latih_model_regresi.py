import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import itertools # Untuk membuat kombinasi grid search

print("Script dimulai")
# --- 1. Memuat Data dari File Excel ---
try:
    nama_file_excel = 'fitur_area_terang_hasil_ekstraksi.xlsx' # Pastikan nama file ini benar
    # Pastikan juga nama sheet benar, atau hapus sheet_name jika hanya ada satu sheet default
    df = pd.read_excel(nama_file_excel, sheet_name='Sheet1') 
    print("Data berhasil dimuat dari Excel.")
    print("Jumlah baris data awal:", len(df))
    print("Nama kolom:", df.columns.tolist())
except FileNotFoundError:
    print(f"Error: File '{nama_file_excel}' tidak ditemukan. Pastikan path dan nama file benar.")
    exit()
except Exception as e:
    print(f"Error saat memuat data: {e}")
    exit()

# --- 2. Eksplorasi Data Awal ---
print("\n## Eksplorasi Data Awal ##")
print("Beberapa baris pertama data Anda:")
print(df.head())
print("\nInformasi mengenai kolom data:")
df.info()
print("\nStatistik deskriptif data numerik:")
print(df.describe())

# --- 3. Pemilihan Fitur (X) dan Target (y) ---
kolom_fitur_cahaya = [
    'pusat_x_norm', 
    'pusat_y_norm', 
    'area_norm'
    # Tambahkan fitur lain jika ada dan relevan, misal: 'bbox_w_norm', 'bbox_h_norm'
]
nama_kolom_tegangan = 'Tegangan' # PASTIKAN NAMA KOLOM INI SESUAI DENGAN FILE EXCEL ANDA

# Validasi kolom
kolom_yang_diperlukan = kolom_fitur_cahaya + [nama_kolom_tegangan]
for kolom in kolom_yang_diperlukan:
    if kolom not in df.columns:
        print(f"\nError: Kolom '{kolom}' tidak ditemukan dalam file Excel Anda.")
        print("Kolom yang tersedia adalah:", df.columns.tolist())
        exit()

# Hapus baris dengan nilai NaN
df_bersih = df.dropna(subset=kolom_yang_diperlukan).copy() # Gunakan .copy() untuk menghindari SettingWithCopyWarning
if len(df_bersih) < len(df):
    print(f"\n{len(df) - len(df_bersih)} baris data dengan nilai kosong (NaN) telah dihapus.")
if len(df_bersih) < 10: # Butuh cukup data untuk split dan train yang berarti
    print(f"Error: Tidak cukup data (hanya {len(df_bersih)} baris) setelah menghapus nilai kosong. Model mungkin tidak bisa dilatih dengan baik.")
    # Anda mungkin ingin keluar di sini jika datanya terlalu sedikit, atau setidaknya waspada
    if len(df_bersih) < 2: exit()


X = df_bersih[kolom_fitur_cahaya]
y = df_bersih[nama_kolom_tegangan]

print(f"\nJumlah sampel data yang akan digunakan untuk pelatihan: {len(X)}")
if len(X) == 0:
    print("Tidak ada data untuk dilatih. Skrip berhenti.")
    exit()

# --- 4. Pembagian Data ---
# Pastikan ada cukup data untuk dibagi
if len(X) < 5: # Misalnya, minimal 5 sampel untuk bisa dibagi
    print("Jumlah data terlalu sedikit untuk dibagi menjadi training dan testing set.")
    # Jika sangat sedikit, mungkin gunakan semua data untuk training dan evaluasi secara kualitatif
    # atau pertimbangkan cross-validation jika datanya sedikit lebih banyak.
    # Untuk contoh ini, kita akan lanjutkan, tapi ini adalah peringatan.
    X_train, X_test, y_train, y_test = X, X, y, y # Gunakan semua data jika sangat sedikit
else:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Jumlah data latih: {len(X_train)}")
print(f"Jumlah data uji: {len(X_test)}")

# --- 5. Pemilihan dan Pelatihan Model Regresi ---

# A. Model Regresi Linear
print("\n\n## OUTPUT 1: Interpretasi Model Regresi Linear ##")
model_linear = LinearRegression()
model_linear.fit(X_train, y_train)

if X_train.shape[1] == 1:
    k_linear = model_linear.coef_[0]
    intercept_linear = model_linear.intercept_
    print(f"Koefisien (k) dari Regresi Linear: {k_linear:.4f}")
    print(f"Intercept (c) dari Regresi Linear: {intercept_linear:.4f}")
    print(f"Persamaan: Tegangan ≈ {k_linear:.4f} * [{X_train.columns[0]}] + {intercept_linear:.4f}")
else:
    print("Koefisien (bobot fitur) dari Regresi Linear:")
    for fitur, koef in zip(kolom_fitur_cahaya, model_linear.coef_):
        print(f"  - Fitur '{fitur}': {koef:.4f}")
    print(f"Intercept (c) dari Regresi Linear: {model_linear.intercept_:.4f}")

# B. Model Random Forest Regressor
print("\n\n## OUTPUT 2: Pentingnya Fitur dari Model Random Forest ##")
model_rf = RandomForestRegressor(n_estimators=100, random_state=42, oob_score=True, n_jobs=-1)
model_rf.fit(X_train, y_train)
print(f"Random Forest OOB Score (mirip R^2 pada data training): {model_rf.oob_score_:.4f}")

if hasattr(model_rf, 'feature_importances_'):
    print("Pentingnya Fitur dari Random Forest:")
    importances = sorted(zip(kolom_fitur_cahaya, model_rf.feature_importances_), key=lambda x: x[1], reverse=True)
    for fitur, importansi in importances:
        print(f"  - Fitur '{fitur}': {importansi:.4f}")

# --- 6. Evaluasi Model ---

# Evaluasi Model Linear
y_pred_linear_train = model_linear.predict(X_train)
y_pred_linear_test = model_linear.predict(X_test)
mse_linear_train = mean_squared_error(y_train, y_pred_linear_train)
r2_linear_train = r2_score(y_train, y_pred_linear_train)
mse_linear_test = mean_squared_error(y_test, y_pred_linear_test) if len(X_test)>0 else np.nan
r2_linear_test = r2_score(y_test, y_pred_linear_test) if len(X_test)>0 else np.nan

print("\n\n## OUTPUT 3: Evaluasi Model Regresi Linear ##")
print(f"  Training - RMSE: {np.sqrt(mse_linear_train):.4f}, R^2: {r2_linear_train:.4f}")
if len(X_test) > 0:
    print(f"  Testing  - RMSE: {np.sqrt(mse_linear_test):.4f}, R^2: {r2_linear_test:.4f}")
else:
    print("  Testing  - Tidak ada data uji untuk evaluasi.")


# Evaluasi Model Random Forest
y_pred_rf_train = model_rf.predict(X_train)
y_pred_rf_test = model_rf.predict(X_test)
mse_rf_train = mean_squared_error(y_train, y_pred_rf_train)
r2_rf_train = r2_score(y_train, y_pred_rf_train)
mse_rf_test = mean_squared_error(y_test, y_pred_rf_test) if len(X_test)>0 else np.nan
r2_rf_test = r2_score(y_test, y_pred_rf_test) if len(X_test)>0 else np.nan

print("\n\n## OUTPUT 4: Evaluasi Model Random Forest Regressor ##")
print(f"  Training - RMSE: {np.sqrt(mse_rf_train):.4f}, R^2: {r2_rf_train:.4f}")
if len(X_test) > 0:
    print(f"  Testing  - RMSE: {np.sqrt(mse_rf_test):.4f}, R^2: {r2_rf_test:.4f}")
else:
    print("  Testing  - Tidak ada data uji untuk evaluasi.")

# --- 7. Visualisasi (Opsional, tapi berguna) ---
if len(X_test) > 0:
    model_terbaik_untuk_plot = model_rf # Asumsi RF lebih baik, bisa diganti
    pred_terbaik_untuk_plot = y_pred_rf_test
    nama_model_plot = "Random Forest"
    
    # Jika model linear lebih baik (berdasarkan R^2 test), gunakan itu untuk plot
    if r2_linear_test > r2_rf_test:
        model_terbaik_untuk_plot = model_linear
        pred_terbaik_untuk_plot = y_pred_linear_test
        nama_model_plot = "Regresi Linear"

    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, pred_terbaik_untuk_plot, alpha=0.7, edgecolors='k', label='Prediksi vs Aktual')
    min_val = min(y_test.min(), pred_terbaik_untuk_plot.min())
    max_val = max(y_test.max(), pred_terbaik_untuk_plot.max())
    plt.plot([min_val, max_val], [min_val, max_val], '--k', lw=2, label='Prediksi Sempurna (y=x)')
    plt.xlabel("Tegangan Aktual (Volt) - Data Uji")
    plt.ylabel(f"Tegangan Prediksi ({nama_model_plot}) (Volt)")
    plt.title(f"Perbandingan Tegangan Aktual vs. Prediksi ({nama_model_plot})")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("\nVisualisasi tidak ditampilkan karena tidak ada data uji.")

# --- BARU: Mencari Titik Penghasil Tegangan Maksimal ---
print("\n\n## OUTPUT 5: Mencari Titik Penghasil Tegangan Maksimal ##")

# Pendekatan 1: Berdasarkan Data Aktual yang Diobservasi
print("\n--- A. Berdasarkan Data Aktual ---")
if not df_bersih.empty:
    idx_max_tegangan_aktual = df_bersih[nama_kolom_tegangan].idxmax()
    data_optimal_aktual = df_bersih.loc[idx_max_tegangan_aktual]
    
    print(f"Tegangan aktual maksimum yang terobservasi: {data_optimal_aktual[nama_kolom_tegangan]:.4f} Volt")
    print("Pada kondisi fitur cahaya (aktual):")
    for fitur in kolom_fitur_cahaya:
        print(f"  - {fitur}: {data_optimal_aktual[fitur]:.4f}")
else:
    print("Tidak ada data bersih untuk dianalisis.")

# Pendekatan 2: Berdasarkan Prediksi Model AI Terbaik (misalnya Random Forest)
print("\n--- B. Berdasarkan Prediksi Model AI Terbaik (Random Forest) ---")
# Kita akan membuat grid sederhana dari nilai fitur dan mencari prediksi tertinggi
# Tentukan model terbaik (misalnya, berdasarkan R^2 pada data test)
model_terbaik = model_rf
nama_model_terbaik = "Random Forest"
if len(X_test)>0 and r2_linear_test > r2_rf_test: # Hanya bandingkan jika ada data test
    model_terbaik = model_linear
    nama_model_terbaik = "Regresi Linear"
print(f"Menggunakan model terbaik: {nama_model_terbaik} (berdasarkan R^2 test jika ada, jika tidak default ke RF)")

# Buat rentang nilai untuk setiap fitur untuk dijelajahi
# Gunakan min dan max dari data aktual sebagai batas, dan bagi menjadi beberapa titik
# Jumlah titik per fitur (N_POINTS) bisa disesuaikan. Semakin banyak, semakin lama tapi detail.
N_POINTS_PER_FEATURE = 5 # Kurangi jika ingin lebih cepat, tambah jika ingin lebih detail

grid_search_values = []
for fitur in kolom_fitur_cahaya:
    if X[fitur].nunique() > 1: # Hanya buat linspace jika ada lebih dari 1 nilai unik
        grid_search_values.append(np.linspace(X[fitur].min(), X[fitur].max(), N_POINTS_PER_FEATURE))
    else: # Jika hanya satu nilai unik, gunakan nilai itu saja
        grid_search_values.append(np.array([X[fitur].unique()[0]]))

# Buat semua kombinasi fitur dari grid
kombinasi_fitur = list(itertools.product(*grid_search_values))
df_grid_search = pd.DataFrame(kombinasi_fitur, columns=kolom_fitur_cahaya)

print(f"Melakukan prediksi pada {len(df_grid_search)} kombinasi fitur (grid search)...")

# Prediksi menggunakan model terbaik
prediksi_tegangan_grid = model_terbaik.predict(df_grid_search)
df_grid_search['prediksi_tegangan'] = prediksi_tegangan_grid

# Cari baris dengan prediksi tegangan tertinggi
idx_max_prediksi = df_grid_search['prediksi_tegangan'].idxmax()
data_optimal_prediksi = df_grid_search.loc[idx_max_prediksi]

print(f"Prediksi tegangan maksimum oleh model ({nama_model_terbaik}): {data_optimal_prediksi['prediksi_tegangan']:.4f} Volt")
print(f"Pada kondisi fitur cahaya (prediksi model {nama_model_terbaik}):")
for fitur in kolom_fitur_cahaya:
    print(f"  - {fitur}: {data_optimal_prediksi[fitur]:.4f}")


# --- Contoh Penggunaan Model untuk Prediksi Baru (Bagian ini sudah ada sebelumnya) ---
print("\n\n--- Contoh Prediksi untuk Data Cahaya Baru (Menggunakan model terlatih) ---")
if len(kolom_fitur_cahaya) == X_train.shape[1]: # Pastikan jumlah fitur benar
    # Buat contoh data baru dengan nilai tengah untuk posisi dan area sedang
    contoh_input_dict = {}
    for i, fitur in enumerate(kolom_fitur_cahaya):
        if X[fitur].nunique() > 1:
             contoh_input_dict[fitur] = (X[fitur].min() + X[fitur].max()) / 2 # Nilai tengah dari data asli
        else:
             contoh_input_dict[fitur] = X[fitur].unique()[0]
        if 'area' in fitur: # Jika area, mungkin nilai yang lebih kecil
            contoh_input_dict[fitur] = contoh_input_dict[fitur] * 0.5 


    data_cahaya_baru_list = [list(contoh_input_dict.values())]
    data_cahaya_baru = pd.DataFrame(data_cahaya_baru_list, columns=kolom_fitur_cahaya)
    
    prediksi_linear_baru = model_linear.predict(data_cahaya_baru)
    prediksi_rf_baru = model_rf.predict(data_cahaya_baru)
    
    print(f"Data Input Baru: {data_cahaya_baru.iloc[0].to_dict()}")
    print(f"  Prediksi Tegangan (Regresi Linear): {prediksi_linear_baru[0]:.2f} Volt")
    print(f"  Prediksi Tegangan (Random Forest): {prediksi_rf_baru[0]:.2f} Volt")
else:
    print("Jumlah fitur untuk contoh prediksi baru tidak sesuai dengan model yang dilatih.")

print("\nScript selesai.")