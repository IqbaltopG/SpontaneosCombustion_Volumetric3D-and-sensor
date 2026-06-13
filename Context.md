# 🚀 ANTIGRAVITY CLI: KIDECO VOLUMETRIC MVP
**Project:** Spatio-Temporal Stockpile Coal Combustion Simulator
**Phase:** Core Volumetric Logic (Hardware-in-the-Loop)

> "Pijakan darurat. Fokus ke matriks Z-axis dulu, dashboard urusan nanti, Sir!"

---

## 🛠️ 1. ENVIRONMENT & TECH STACK
* **Role:** Edge Vision Processing.
* **Hardware:** OAK-D Lite (Hardware-accelerated Stereo Depth via Myriad X VPU).
* **Mock Sensors:** Thermal & Gas MQ-7 (Data fisik belum ada, generate dummy payload).
* **Core Libraries:** `depthai`, `numpy`, `cv2`.

```bash
# Bikin dan masuk ke Virtual Environment
python -m venv kic_env
source kic_env/bin/activate

# Install dependencies inti
pip install depthai numpy opencv-python

🧠 2. CORE DETECTION LOGIC (Z-AXIS DIFFERENTIAL)

Alur pemrosesan matriks kedalaman (Depth Map) untuk deteksi swabakar:

    Baseline Calibration: Tangkap matriks Z-axis statis saat awal script jalan.

    Real-time Ingestion: Stream data spasial kontinu dari OAK-D Lite.

    Differential Processing: Subtraksi matriks: Real-time Z dikurang Baseline Z.

    Threshold Trigger: Jika Real-time Z > Baseline Z (permukaan amblas), set Volumetric_Anomaly = True.

    Sensor Fusion (Mock): Agregasi boolean anomali dengan dummy data Suhu (Tinggi) & CO (Tinggi).

    Data Serialization: Bungkus jadi JSON siap kirim.

⚠️ 3. STRICT RULES & UNIT TESTING

[!] FATAL ERROR RISK: OAK-D Lite HARUS STATIS (dilakban ke monitor atau dijepit stand). JANGAN dipegang tangan. Micro-tremors sekecil apa pun bakal ngacak-ngacak kalibrasi matriks baseline!
Test Scenario A: "The Book Drop" (Solid Object Validation)

    Sorot meja datar, tunggu kalibrasi baseline.

    Taruh buku tebal di tengah (Z-distance mengecil).

    Reset baseline ke permukaan buku.

    Tarik bukunya mendadak (Z-distance membesar/amblas). Sistem harus ngetrigger anomali.

Test Scenario B: "The Coffee Collapse" (Granular Physics Validation)

    Bikin tumpukan ampas kopi basah di meja (gunakan takaran ampas sisa ekstraksi 80ml per cup biar tingkat kelembapan dan kepadatan gundukannya ideal buat disendok).

    Arahkan kamera statis, dapatkan baseline permukaannya.

    Keruk perlahan bagian tengah ampas kopinya pakai sendok (simulasi Volume Loss batu bara).

    Terminal harus teriak Volumetric_Anomaly = True akibat deteksi subsidence.

⚙️ 4. EXECUTION COMMAND

Jalanin engine volumetriknya secara terisolasi (tanpa web/dashboard).
Bash

# Eksekusi pipeline DepthAI (pastikan kabel USB-C tertancap sempurna)
python volumetric_core.py