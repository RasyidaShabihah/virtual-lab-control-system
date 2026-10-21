# Virtual Laboratory — Sistem Kontrol dan Motor DC

Aplikasi Streamlit edukasi untuk disematkan sebagai tautan pada PPT MOOC. Termasuk:
- Asesmen 1: respons motor DC terhadap tegangan step.
- Asesmen 2: kontroler P, PI, PD, PID.
- Asesmen 3: studi kasus edukasi dan kuis.
- Animasi rotor 2D, grafik, metrik respons, skor latihan, unduh CSV.

## 1. Jalankan lokal (opsional)

Persyaratan: Python 3.10+.

```bash
python -m venv .venv
```

Aktifkan virtual environment:
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install paket dan jalankan:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi lokal biasanya terbuka di `http://localhost:8501`. Ini **bukan** URL publik.

## 2. Deploy publik ke Streamlit Community Cloud

### A. Buat repository GitHub
1. Login ke https://github.com
2. Klik **New repository**.
3. Nama repository: `virtual-lab-motor-dc`.
4. Untuk proses yang mudah, pilih **Public**.
5. Klik **Create repository**.

### B. Upload file proyek
Unggah `app.py`, `requirements.txt`, dan `README.md` ke root repository (folder utama). Pastikan nama file tepat.

Cara termudah tanpa Git:
1. Pada repository GitHub, pilih **Add file → Upload files**.
2. Seret ketiga file tersebut.
3. Klik **Commit changes**.

### C. Deploy
1. Buka https://share.streamlit.io/
2. Pilih **Continue with GitHub** dan berikan izin yang diminta.
3. Klik **Create app** / **Deploy an app**.
4. Pilih repository `virtual-lab-motor-dc`.
5. Branch: `main`.
6. Main file path: `app.py`.
7. Klik **Deploy**.
8. Tunggu instalasi paket selesai. Jika berhasil, dashboard akan menunjukkan aplikasi dan URL publik berbentuk `https://<nama-aplikasi>.streamlit.app`.
9. Salin URL aktual yang diberikan Streamlit. Jangan menggunakan URL contoh sebagai tautan final.

### D. Tes akses publik
1. Buka URL pada jendela Incognito/Private atau ponsel dengan jaringan seluler.
2. Pastikan aplikasi terbuka tanpa login.
3. Uji ketiga modul, tombol simulasi, kuis, dan unduh CSV.
4. Uji pada ukuran layar laptop dan ponsel.
5. Jika gagal, buka **Manage app / Logs** di dashboard Streamlit, lalu periksa pesan error.

## 3. Masukkan tautan ke PPT MOOC
1. Buka PowerPoint dan pilih slide asesmen.
2. Tambahkan teks: **Buka Virtual Laboratory Motor DC**.
3. Pilih teks tersebut lalu tekan `Ctrl+K` (Insert → Link).
4. Tempel URL publik aktual.
5. Klik OK.
6. Uji tautan dengan `Ctrl+klik`, atau jalankan Slide Show dan klik teks.
7. Jika PPT diubah menjadi PDF, ekspor dengan opsi yang mempertahankan hyperlink dan uji tautan PDF-nya.

Saran: gunakan satu URL aplikasi untuk semua asesmen karena mahasiswa memilih modul dari menu navigasi di sidebar.

## 4. Model matematis yang digunakan

Model armature-controlled DC motor:

`L di/dt = V - R i - Ke omega`

`J d omega/dt = Kt i - B omega - T_load`

dengan:
- `V`: tegangan armatur (V)
- `i`: arus armatur (A)
- `R`: resistansi (Ω)
- `L`: induktansi (H)
- `Ke`: konstanta back-EMF
- `J`: inersia rotor (kg·m²)
- `B`: koefisien gesekan viskos
- `Kt`: konstanta torsi
- `T_load`: torsi beban (N·m)
- `omega`: kecepatan sudut (rad/s), dikonversi ke RPM

Integrasi Euler dipakai untuk demo pengajaran. Untuk asesmen formal, validasi numerik dan kesesuaian parameter dengan materi kuliah terlebih dahulu.

## 5. Batasan penting untuk MOOC
- Kode demo menampilkan skor latihan, tetapi tidak menyimpan nama, identitas, jawaban, atau nilai di server.
- Unduhan CSV berisi data simulasi, bukan catatan nilai mahasiswa.
- Jika nilai harus direkap, gunakan LMS atau tambahkan backend yang aman dan autentikasi. Jangan menaruh API key atau kata sandi di repository.
- Model infusion pump hanya studi kasus edukatif; tidak divalidasi untuk penggunaan klinis atau alat medis nyata.
- Simulasi ini memakai model motor DC sederhana dengan tegangan kendali dibatasi 0–12 V.
