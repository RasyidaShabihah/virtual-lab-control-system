import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Virtual Lab Motor DC", page_icon="⚙️", layout="wide")
st.title("⚙️ Virtual Laboratory — Sistem Kontrol dan Motor DC")
st.caption("Untuk pembelajaran dan asesmen MOOC. Model edukasi, bukan pengendali perangkat medis.")

# ---------- Model matematis ----------
# L di/dt = V - R i - Ke omega
# J d omega/dt = Kt i - B omega - T_load
def simulate_motor(
    voltage_fn, duration=5.0, dt=0.002,
    R=2.0, L=0.5, J=0.02, B=0.2, Ke=0.02, Kt=0.02,
    load_torque=0.0, controller=None
):
    t = np.arange(0.0, duration + dt, dt)
    i = np.zeros_like(t)
    omega = np.zeros_like(t)
    voltage = np.zeros_like(t)
    error = np.zeros_like(t)
    integral = 0.0
    prev_error = 0.0

    for k in range(1, len(t)):
        if controller is None:
            v = float(voltage_fn(t[k - 1]))
        else:
            target_rpm, mode, kp, ki, kd = controller
            rpm_now = omega[k - 1] * 60.0 / (2.0 * np.pi)
            e = target_rpm - rpm_now
            integral += e * dt
            derivative = (e - prev_error) / dt
            u = kp * e
            if mode in ("PI", "PID"):
                u += ki * integral
            if mode in ("PD", "PID"):
                u += kd * derivative
            v = float(np.clip(u, 0.0, 12.0))
            error[k] = e
            prev_error = e

        v = float(np.clip(v, 0.0, 12.0))
        voltage[k - 1] = v

        di = (v - R * i[k - 1] - Ke * omega[k - 1]) / L
        domega = (Kt * i[k - 1] - B * omega[k - 1] - load_torque) / J
        i[k] = i[k - 1] + dt * di
        omega[k] = max(0.0, omega[k - 1] + dt * domega)

    voltage[-1] = voltage[-2]
    rpm = omega * 60.0 / (2.0 * np.pi)
    return t, rpm, i, voltage, error

def metrics(t, y, target=None):
    final = float(y[-1])
    ref = final if target is None else float(target)
    if abs(ref) < 1e-9:
        return {"Nilai akhir (RPM)": final, "Rise time 10–90% (s)": np.nan,
                "Overshoot (%)": np.nan, "Settling time ±2% (s)": np.nan,
                "Steady-state error (RPM)": abs(ref-final)}
    idx10 = np.where(y >= 0.1 * ref)[0]
    idx90 = np.where(y >= 0.9 * ref)[0]
    rise = float(t[idx90[0]] - t[idx10[0]]) if len(idx10) and len(idx90) else np.nan
    overshoot = max(0.0, (float(np.max(y)) - ref) / abs(ref) * 100.0)
    outside = np.where(np.abs(y - ref) > 0.02 * abs(ref))[0]
    settling = float(t[outside[-1] + 1]) if len(outside) and outside[-1] + 1 < len(t) else (0.0 if not len(outside) else np.nan)
    return {"Nilai akhir (RPM)": final, "Rise time 10–90% (s)": rise,
            "Overshoot (%)": overshoot, "Settling time ±2% (s)": settling,
            "Steady-state error (RPM)": abs(ref-final)}

def show_metrics(t, y, target=None):
    m = metrics(t, y, target)
    cols = st.columns(len(m))
    for col, (label, value) in zip(cols, m.items()):
        col.metric(label, "—" if not np.isfinite(value) else f"{value:.2f}")

def plot_response(t, rpm, target=None, title="Respons kecepatan motor DC"):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, rpm, label="Kecepatan motor")
    if target is not None:
        ax.axhline(target, linestyle="--", label=f"Target {target:.0f} RPM")
    ax.set_xlabel("Waktu (s)")
    ax.set_ylabel("Kecepatan (RPM)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def motor_animation(rpm):
    # CSS animation speed is illustrative, not a real-time mechanical display.
    seconds_per_turn = max(0.25, min(4.0, 60.0 / max(float(rpm), 15.0)))
    html = f"""
    <div style="display:flex;align-items:center;gap:18px;font-family:Arial;padding:12px;border:1px solid #ddd;border-radius:12px;">
      <svg width="150" height="150" viewBox="0 0 150 150" role="img" aria-label="Ilustrasi rotor motor DC">
        <circle cx="75" cy="75" r="60" fill="#f1f5f9" stroke="#64748b" stroke-width="5"/>
        <circle cx="75" cy="75" r="44" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
        <g style="transform-origin:75px 75px;animation:spin {seconds_per_turn:.3f}s linear infinite">
          <rect x="68" y="29" width="14" height="92" rx="5" fill="#ea580c"/>
          <rect x="29" y="68" width="92" height="14" rx="5" fill="#ea580c"/>
          <circle cx="75" cy="75" r="13" fill="#334155" stroke="#fff" stroke-width="2"/>
        </g>
        <circle cx="75" cy="75" r="5" fill="#fff"/>
      </svg>
      <div><div style="color:#64748b;font-size:14px">Kecepatan akhir simulasi</div>
      <div style="font-size:28px;font-weight:700">{float(rpm):.1f} RPM</div>
      <div style="color:#64748b;font-size:12px">Animasi edukatif; laju visual diskalakan agar putaran mudah diamati.</div></div>
    </div>
    <style>@keyframes spin {{from {{transform:rotate(0deg)}} to {{transform:rotate(360deg)}}}}</style>
    """
    components.html(html, height=180)

def motor_controls(key):
    c1, c2, c3 = st.columns(3)
    with c1:
        R = st.slider("R — Resistansi armatur (Ω)", 0.5, 10.0, 2.0, 0.1, key=f"{key}_R")
        L = st.slider("L — Induktansi armatur (H)", 0.05, 2.0, 0.5, 0.05, key=f"{key}_L")
    with c2:
        J = st.slider("J — Inersia rotor (kg·m²)", 0.005, 0.1, 0.02, 0.005, key=f"{key}_J")
        B = st.slider("B — Gesekan viskos (N·m·s/rad)", 0.01, 1.0, 0.2, 0.01, key=f"{key}_B")
    with c3:
        Ke = st.slider("Ke — Konstanta back-EMF", 0.005, 0.1, 0.02, 0.005, key=f"{key}_Ke")
        Kt = st.slider("Kt — Konstanta torsi", 0.005, 0.1, 0.02, 0.005, key=f"{key}_Kt")
    return dict(R=R, L=L, J=J, B=B, Ke=Ke, Kt=Kt)

with st.sidebar:
    st.header("Navigasi")
    page = st.radio("Pilih modul", [
        "Asesmen 1 — Respons sistem",
        "Asesmen 2 — Kontroler PID",
        "Asesmen 3 — Studi kasus",
        "Petunjuk & model",
    ])
    st.divider()
    st.caption("Model: L di/dt = V − Ri − Keω")
    st.caption("Model: J dω/dt = Kt i − Bω − Tₗ")

if page == "Petunjuk & model":
    st.subheader("Petunjuk penggunaan")
    st.markdown("""
    1. Pilih modul di menu sebelah kiri.
    2. Ubah parameter motor atau kontroler, lalu jalankan simulasi.
    3. Amati grafik respons, animasi rotor, dan metrik performa.
    4. Kerjakan soal latihan; skor akan ditampilkan pada halaman.
    5. Unduh data simulasi dalam format CSV bila diperlukan.

    **Model matematis:** `L di/dt = V − R i − Ke ω` dan
    `J dω/dt = Kt i − B ω − T_load`. Kecepatan sudut dikonversi ke RPM.
    Integrasi Euler digunakan untuk demonstrasi pembelajaran; parameter dan hasil
    tidak boleh digunakan untuk mengendalikan perangkat medis nyata.

    **Catatan asesmen:** aplikasi demo ini tidak menyimpan identitas atau nilai mahasiswa
    di server. Untuk nilai resmi, hubungkan dengan LMS/formulir resmi atau tambahkan
    backend dengan autentikasi dan kebijakan perlindungan data.
    """)
    st.latex(r"L\frac{di}{dt}=V-Ri-K_e\omega")
    st.latex(r"J\frac{d\omega}{dt}=K_t i-B\omega-T_L")

elif page == "Asesmen 1 — Respons sistem":
    st.subheader("Asesmen 1 — Analisis respons sistem")
    st.write("Uji pengaruh tegangan input dan parameter motor terhadap kecepatan.")
    p = motor_controls("a1")
    c1, c2 = st.columns(2)
    with c1:
        vin = st.select_slider("Tegangan step input (V)", options=[0, 3, 6, 9, 12], value=6)
    with c2:
        duration = st.slider("Durasi simulasi (s)", 1.0, 10.0, 5.0, 0.5, key="a1_duration")
    if st.button("Jalankan simulasi", type="primary", key="run1"):
        t, rpm, current, voltage, _ = simulate_motor(lambda _: vin, duration=duration, **p)
        motor_animation(rpm[-1])
        plot_response(t, rpm, title=f"Respons motor DC terhadap step {vin} V")
        show_metrics(t, rpm)
        df = pd.DataFrame({"time_s": t, "voltage_V": voltage, "current_A": current, "speed_RPM": rpm})
        st.download_button("Unduh CSV hasil simulasi", df.to_csv(index=False).encode(), "asesmen1_motor_dc.csv", "text/csv")
    st.markdown("#### Pertanyaan latihan")
    q1 = st.radio("1. Jika tegangan input dinaikkan, apa yang umumnya terjadi pada kecepatan tunak?", [
        "Kecepatan tunak cenderung meningkat", "Kecepatan tunak selalu nol", "Parameter R otomatis menjadi nol"], key="a1q1")
    q2 = st.radio("2. Parameter yang merepresentasikan inersia mekanis adalah…", ["R", "J", "Ke"], key="a1q2")
    q3 = st.radio("3. Back-EMF pada model ini direpresentasikan oleh…", ["Keω", "Kt i", "Bω saja"], key="a1q3")
    if st.button("Periksa skor latihan", key="check1"):
        score = int(q1 == "Kecepatan tunak cenderung meningkat") + int(q2 == "J") + int(q3 == "Keω")
        st.success(f"Skor latihan: {score}/3")
        st.caption("Skor hanya ditampilkan pada sesi ini; belum dikirim atau disimpan ke server.")

elif page == "Asesmen 2 — Kontroler PID":
    st.subheader("Asesmen 2 — Pengendalian kecepatan motor DC")
    st.write("Pilih kontroler dan ubah gain untuk melihat perubahan tracking kecepatan.")
    p = motor_controls("a2")
    c1, c2 = st.columns(2)
    with c1:
        mode = st.selectbox("Kontroler", ["P", "PI", "PD", "PID"], index=3)
        target = st.slider("Target kecepatan (RPM)", 100, 2000, 800, 50)
        duration = st.slider("Durasi simulasi (s)", 1.0, 10.0, 5.0, 0.5, key="a2_duration")
    with c2:
        kp = st.slider("Kp", 0.0, 0.2, 0.02, 0.005, format="%.3f")
        ki = st.slider("Ki", 0.0, 0.2, 0.02, 0.005, format="%.3f")
        kd = st.slider("Kd", 0.0, 0.02, 0.001, 0.0005, format="%.4f")
    if st.button("Jalankan simulasi", type="primary", key="run2"):
        t, rpm, current, voltage, _ = simulate_motor(lambda _: 0, duration=duration,
            controller=(target, mode, kp, ki, kd), **p)
        motor_animation(rpm[-1])
        plot_response(t, rpm, target=target, title=f"Respons kontroler {mode}")
        show_metrics(t, rpm, target)
        st.write(f"Tegangan kendali maksimum: **{np.max(voltage):.2f} V** (dibatasi 0–12 V).")
        df = pd.DataFrame({"time_s": t, "target_RPM": target, "speed_RPM": rpm,
                           "error_RPM": target-rpm, "voltage_V": voltage, "current_A": current})
        st.download_button("Unduh CSV hasil simulasi", df.to_csv(index=False).encode(), "asesmen2_pid.csv", "text/csv")
    st.markdown("#### Pertanyaan latihan")
    q1 = st.radio("1. Komponen PID yang biasanya membantu mengurangi error tunak adalah…", ["P", "I", "D"], key="a2q1")
    q2 = st.radio("2. Jika kontroler terlalu agresif, respons dapat menunjukkan…", ["Overshoot lebih besar", "Selalu tanpa overshoot", "Arus pasti nol"], key="a2q2")
    q3 = st.radio("3. Mengapa tegangan kendali perlu dibatasi?", ["Agar mewakili batas aktuator", "Agar grafik hilang", "Agar target berubah sendiri"], key="a2q3")
    if st.button("Periksa skor latihan", key="check2"):
        score = int(q1 == "I") + int(q2 == "Overshoot lebih besar") + int(q3 == "Agar mewakili batas aktuator")
        st.success(f"Skor latihan: {score}/3")
        st.caption("Skor hanya ditampilkan pada sesi ini; belum dikirim atau disimpan ke server.")

else:
    st.subheader("Asesmen 3 — Studi kasus motor DC pada infusion pump")
    st.warning("Kasus edukasi saja. Tidak tervalidasi untuk mengendalikan infusion pump nyata.")
    st.markdown("""
    **Skenario:** pilih kontroler agar kecepatan motor mengikuti target dengan error tunak
    dan overshoot yang rendah. Hubungan RPM dengan laju aliran harus ditentukan melalui
    model pompa dan kalibrasi yang sesuai; simulasi ini tidak mengklaim akurasi klinis.
    """)
    p = motor_controls("a3")
    c1, c2 = st.columns(2)
    with c1:
        mode = st.selectbox("Kontroler", ["P", "PI", "PD", "PID"], index=3, key="a3_mode")
        target = st.slider("Target kecepatan (RPM)", 100, 2000, 800, 50, key="a3_target")
    with c2:
        kp = st.slider("Kp", 0.0, 0.2, 0.02, 0.005, key="a3_kp")
        ki = st.slider("Ki", 0.0, 0.2, 0.02, 0.005, key="a3_ki")
        kd = st.slider("Kd", 0.0, 0.02, 0.001, 0.0005, key="a3_kd")
    if st.button("Jalankan simulasi studi kasus", type="primary", key="run3"):
        t, rpm, current, voltage, _ = simulate_motor(lambda _: 0, controller=(target, mode, kp, ki, kd), **p)
        motor_animation(rpm[-1])
        plot_response(t, rpm, target=target, title=f"Studi kasus — kontroler {mode}")
        show_metrics(t, rpm, target)
        df = pd.DataFrame({"time_s": t, "target_RPM": target, "speed_RPM": rpm,
                           "voltage_V": voltage, "current_A": current})
        st.download_button("Unduh CSV hasil studi kasus", df.to_csv(index=False).encode(), "asesmen3_studi_kasus.csv", "text/csv")
    st.markdown("#### Pertanyaan latihan")
    q1 = st.radio("1. Untuk mengurangi error tunak pada banyak sistem, komponen mana yang dapat membantu?", ["Integral (I)", "Derivative (D)", "Tidak ada"], key="a3q1")
    q2 = st.radio("2. Jika overshoot terlalu tinggi, tindakan yang tepat adalah…", [
        "Tuning ulang gain dan evaluasi respons", "Menaikkan semua gain tanpa uji", "Mengabaikan grafik"], key="a3q2")
    q3 = st.radio("3. Apakah model kecepatan motor saja menjamin laju aliran infusion pump akurat?", [
        "Ya", "Tidak, perlu model pompa dan kalibrasi/validasi"], key="a3q3")
    if st.button("Periksa skor latihan", key="check3"):
        score = int(q1 == "Integral (I)") + int(q2 == "Tuning ulang gain dan evaluasi respons") + int(q3 == "Tidak, perlu model pompa dan kalibrasi/validasi")
        st.success(f"Skor latihan: {score}/3")
        st.caption("Skor hanya ditampilkan pada sesi ini; belum dikirim atau disimpan ke server.")
