Perfect 👌 — kamu sudah punya arsitektur teknis dan code dasar yang matang.
Sekarang mari kita **formalkan menjadi dokumen PRD (Product Requirements Document)** + **Technical Requirements** biar bisa dijadikan dasar pengembangan (hardware dan software) sistem **Ground Station Rotator berbasis Raspberry Pi 4B**.

---

## 📘 **Product Requirements Document (PRD)**

### 🚀 Project Name

**Open Ground Station Rotator Controller (OGRC)**
Open-source ground station controller untuk antena satelit, menggunakan Raspberry Pi 4B, motor stepper, dan IMU WT901C-RS485 sebagai feedback sistem, kompatibel dengan Gpredict + Hamlib (rotctld).

---

### 🎯 **Objective**

Membangun **rotator antena otomatis** dengan **azimuth dan elevasi** yang:

1. Mampu melacak posisi satelit secara real-time menggunakan Gpredict.
2. Dapat dikendalikan secara penuh oleh **Hamlib/rotctld (protokol GS-232)**.
3. Menggunakan **feedback sensor IMU (WT901C-RS485)** untuk closed-loop posisi aktual.
4. Menggunakan **Raspberry Pi 4B** sebagai pengendali utama tanpa mikrokontroler tambahan.
5. Bersifat **modular dan open-source** (mudah dikembangkan untuk SatNOGS atau sistem radio lainnya).

---

### 💡 **Key Features**

| Fitur                   | Deskripsi                                                                              |
| ----------------------- | -------------------------------------------------------------------------------------- |
| 🔁 Dual-axis control    | Azimuth & Elevation dikontrol independen via stepper motor                             |
| ⚙️ Closed-loop feedback | WT901C-RS485 IMU membaca sudut aktual untuk koreksi posisi                             |
| 🧠 GS-232 emulator      | Python TCP server emulasi protokol GS-232 untuk kompatibilitas Hamlib/Gpredict         |
| 🌐 Integration-ready    | Kompatibel dengan `rotctld`, Gpredict, SatNOGS                                         |
| 🧩 Modular Hardware     | Support berbagai driver stepper (A4988, DRV8825, DM542, TMC2209, dsb.)                 |
| 🪫 Safety & calibration | Dukungan limit switch, homing, serta toleransi error posisi                            |
| 🪄 Simple deployment    | Cukup jalankan `python3 rotator.py` di Raspberry Pi                                    |
| 🔧 Expandable           | Bisa dikembangkan untuk rotasi pan-tilt kamera, dish antena, atau radio telescope mini |

---

### 📊 **User Scenarios**

1. **Satellite Tracking Mode**

   * Gpredict menghitung az/el posisi satelit.
   * rotctld mengirim perintah ke `rotator.py` via TCP.
   * Python script menggerakkan stepper sesuai target.
   * IMU memberikan feedback aktual → script koreksi error posisi.
   * Posisi dikembalikan ke Gpredict untuk visualisasi.

2. **Manual Mode (Testing / Calibration)**

   * User kirim perintah GS-232 manual via telnet:

     ```
     AZ180
     EL45
     p
     ```
   * Stepper bergerak ke posisi tersebut dan mengembalikan feedback.

---

### 📈 **Success Metrics**

| Metric                         | Target                   |
| ------------------------------ | ------------------------ |
| Error posisi az/el             | < ±0.5°                  |
| Latency command → motion start | < 0.3 detik              |
| Tracking continuity            | 100% selama pass satelit |
| Kompatibilitas Hamlib/Gpredict | 100% (GS-232A protocol)  |
| Stabilitas IMU feedback        | < ±0.2° jitter           |

---

## ⚙️ **Technical Requirements**

### 1. **Hardware Components**

| Komponen                | Spesifikasi                 | Catatan                           |
| ----------------------- | --------------------------- | --------------------------------- |
| Raspberry Pi 4B         | 4GB RAM, 40-pin GPIO        | Controller utama                  |
| Stepper Motor           | 2x NEMA34 (1.8°/step)       | Untuk azimuth & elevasi           |
| Stepper Driver          | 2x DM542 atau TMC5160       | Support microstepping 1/16–1/128  |
| Power Supply            | 24V DC 10A                  | Untuk motor dan driver            |
| WT901C-RS485            | IMU 9DOF (yaw, pitch, roll) | Feedback absolute angle           |
| RS485 Adapter           | MAX485 → USB/TTL            | Koneksi IMU ke Raspberry Pi       |
| Limit Switch (opsional) | 2–4 buah                    | Untuk homing dan keamanan         |
| Mechanical System       | Worm gear ratio 1:40        | Untuk torsi tinggi dan stabilitas |
| Antena mount            | Custom DIY                  | Dudukan antena sesuai desain      |

---

### 2. **Software Stack**

| Layer          | Komponen                                      | Fungsi                            |
| -------------- | --------------------------------------------- | --------------------------------- |
| OS             | Raspberry Pi OS / Debian Bookworm             | Sistem dasar                      |
| Middleware     | Hamlib (rotctld)                              | Bridge komunikasi dengan Gpredict |
| Script         | Python 3                                      | Kontrol stepper dan IMU           |
| Library Python | `pyserial`, `RPi.GPIO`, `socket`, `threading` | Komunikasi dan kontrol            |
| Protocol       | GS-232 / Easycomm II                          | Standar komunikasi Gpredict       |
| IMU Protocol   | Modbus RTU via RS485                          | Baca yaw & pitch dari WT901C      |

---

### 3. **Communication Architecture**

```
         Gpredict
             │
        [rotctld TCP]
             │
 ┌─────────────────────────┐
 │ Raspberry Pi 4B         │
 │  ├─ rotator.py (TCP 4533)│  ← GS-232 Emulator
 │  ├─ Stepper Control      │
 │  ├─ IMU Reader (RS485)   │
 │  └─ Feedback Loop        │
 └─────────────────────────┘
        │            │
   [Stepper Driver]  [WT901C IMU]
        │                 │
   [Az/El Motor]      [Angle Feedback]
```

---

### 4. **Control Loop Design**

1. Gpredict → rotctld → rotator.py (`AZxxx`, `ELxxx`)
2. rotator.py → konversi target → jumlah langkah stepper
3. Stepper digerakkan → baca IMU yaw/pitch
4. Jika error > 0.02° → lakukan koreksi kecil
5. rotator.py → kirim balik posisi aktual (`p` response)

---

### 5. **Performance Targets**

| Parameter                        | Target                       |
| -------------------------------- | ---------------------------- |
| Stepper movement smoothness      | ≤ 1 ms pulse accuracy        |
| Closed-loop refresh rate         | 10 Hz                        |
| TCP response latency             | < 100 ms                     |
| Mechanical backlash compensation | Software offset configurable |
| Position resolution              | ≤ 0.1°                       |

---

### 6. **Safety & Calibration**

* Limit switch di posisi 0° dan max° az/el.
* Homing otomatis saat boot.
* IMU auto-calibration setiap startup.
* Soft-limit posisi untuk mencegah over-rotation.

---

### 7. **Future Enhancements**

* 🛰️ SatNOGS-compatible firmware mode.
* 🧭 PID closed-loop tuning berbasis IMU.
* 🪶 Lightweight web dashboard untuk monitoring posisi real-time (Flask/Vue).
* 🔌 OTA update firmware via WiFi.
* 📡 Integrasi radio transceiver (rigctld) dalam satu board.

---

### 🧾 **Deliverables**

| Item                | Output                                            |
| ------------------- | ------------------------------------------------- |
| Hardware schematic  | Raspberry Pi GPIO → Driver → Stepper → IMU wiring |
| Python firmware     | `rotator.py` (TCP GS-232 emulator)                |
| Configuration guide | Dokumen `setup.md` untuk Hamlib + Gpredict        |
| 3D mechanical CAD   | Mounting antena + worm gear system (optional)     |
| Test logs           | Accuracy & stability test results                 |

---

Kalau kamu mau, saya bisa lanjutkan dengan:
✅ **(1)** Gambar **wiring diagram lengkap** (GPIO → DM542 → NEMA34 + WT901 via MAX485)
✅ **(2)** Dokumen **setup Gpredict & rotctld (step-by-step)** supaya tracking satelit langsung jalan.

Kamu mau saya lanjutkan ke **wiring diagram** atau **setup Gpredict-nya dulu**?
