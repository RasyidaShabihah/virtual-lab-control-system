# BME Control Lab — Virtual Laboratory Motor DC v2

## Fitur
- Dashboard utama dan navigasi modul
- Pemilih role demo: Praktikan, Dosen, Admin (belum autentikasi)
- Respons motor DC dengan grafik Plotly interaktif
- Ilustrasi motor 3D berbasis Plotly
- Blok diagram closed-loop
- Pembelajaran tuning PID bertahap, metrik respons, kuis skor otomatis
- Unduh data simulasi CSV

## Deploy publik
1. Unduh ZIP dan ekstrak.
2. Unggah `app.py`, `requirements.txt`, `README.md` ke repository GitHub (root folder).
3. Buka https://share.streamlit.io/ dan login dengan GitHub.
4. Klik Create app; pilih repository, branch `main`, main file path `app.py`.
5. Deploy dan salin URL `.streamlit.app` yang diberikan.
6. Uji URL dari jendela Incognito/perangkat lain.
7. Di PPT, pilih teks tombol, tekan Ctrl+K, tempel URL publik.

## Jalankan lokal
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Model
L di/dt = V - R i - Ke omega
J d omega/dt = Kt i - B omega - T_load

## Catatan
Role adalah pemilih tampilan saja. Tidak ada login, role permissions, database nilai, atau sinkronisasi LMS. Skor latihan hanya ditampilkan di browser. Untuk asesmen resmi, tambahkan autentikasi dan backend aman atau integrasi LMS. Motor 3D adalah ilustrasi visual; grafik respons menggunakan model edukasi sederhana dengan integrasi Euler. Studi kasus infusion pump bukan model klinis tervalidasi.
