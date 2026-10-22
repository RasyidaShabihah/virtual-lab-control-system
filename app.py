import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="BME Control Lab", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

# ----------------- visual style -----------------
st.markdown("""
<style>
.block-container {padding-top: 1.3rem; padding-bottom: 2rem; max-width: 1450px;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(120,120,120,.18);}
.hero {padding: 1.35rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#10243a,#1d4961); color: #fff; margin-bottom: 1rem;}
.hero h1 {color:#fff; margin:0; font-size:2rem;}
.hero p {color:#d9e8f0; margin:.4rem 0 0 0;}
.small-muted {font-size:.88rem; opacity:.75;}
.block-card {border:1px solid rgba(120,120,120,.25); padding:1rem; border-radius:14px;}
</style>
""", unsafe_allow_html=True)

# ----------------- model -----------------
def simulate_motor(duration=5.0, dt=0.005, R=2.0, L=0.5, J=0.02, B=0.2,
                   Ke=0.02, Kt=0.02, Vstep=6.0, target_rpm=None,
                   controller="PID", kp=0.02, ki=0.02, kd=0.001, load_torque=0.0):
    t = np.arange(0, duration + dt, dt)
    i = np.zeros_like(t); w = np.zeros_like(t); v = np.zeros_like(t)
    integ = 0.0; prev_e = 0.0
    for k in range(1, len(t)):
        if target_rpm is None:
            u = Vstep
        else:
            rpm_now = w[k-1] * 60 / (2*np.pi)
            e = target_rpm - rpm_now
            integ += e * dt
            deriv = (e - prev_e) / dt
            u = kp * e
            if controller in ("PI", "PID"): u += ki * integ
            if controller in ("PD", "PID"): u += kd * deriv
            prev_e = e
        u = float(np.clip(u, 0.0, 12.0))
        v[k-1] = u
        di = (u - R*i[k-1] - Ke*w[k-1]) / L
        dw = (Kt*i[k-1] - B*w[k-1] - load_torque) / J
        i[k] = i[k-1] + dt*di
        w[k] = max(0.0, w[k-1] + dt*dw)
    v[-1] = v[-2]
    return t, w*60/(2*np.pi), i, v

def calc_metrics(t, y, target=None):
    final = float(y[-1])
    ref = final if target is None else float(target)
    if abs(ref) < 1e-9:
        return {"Nilai akhir": final, "Rise time 10–90% (s)": np.nan,
                "Overshoot (%)": np.nan, "Settling time ±2% (s)": np.nan,
                "Error tunak (RPM)": abs(ref-final)}
    i10 = np.where(y >= .1*ref)[0]; i90 = np.where(y >= .9*ref)[0]
    rise = t[i90[0]]-t[i10[0]] if len(i10) and len(i90) else np.nan
    os = max(0.0, (np.max(y)-ref)/abs(ref)*100)
    outside = np.where(np.abs(y-ref) > .02*abs(ref))[0]
    settle = t[outside[-1]+1] if len(outside) and outside[-1]+1 < len(t) else (0.0 if not len(outside) else np.nan)
    return {"Nilai akhir (RPM)": final, "Rise time 10–90% (s)": float(rise),
            "Overshoot (%)": float(os), "Settling time ±2% (s)": float(settle),
            "Error tunak (RPM)": float(abs(ref-final))}

def block_diagram(target=True, controller="PID"):
    fig = go.Figure()
    # Draw blocks and connectors using shapes/annotations
    blocks = [
        (0.02, .38, .17, .68, "Target / Setpoint", "#dceaf7"),
        (.27, .38, .42, .68, f"Controller<br>{controller}", "#d7eee8"),
        (.50, .38, .65, .68, "Motor DC<br>G(s)", "#f7e8cf"),
        (.74, .38, .89, .68, "Sensor / Output", "#eadff5"),
    ]
    for x0,y0,x1,y1,label,color in blocks:
        fig.add_shape(type="rect",x0=x0,y0=y0,x1=x1,y1=y1,xref="paper",yref="paper",
                      line=dict(color="#526779",width=1.5),fillcolor=color)
        fig.add_annotation(x=(x0+x1)/2,y=(y0+y1)/2,xref="paper",yref="paper",text=label,
                           showarrow=False,font=dict(size=13,color="#172b3a"))
    for x0,x1 in [(.17,.27),(.42,.50),(.65,.74)]:
        fig.add_annotation(x=x1,y=.53,xref="paper",yref="paper",ax=x0,ay=.53,axref="paper",ayref="paper",
                           text="",showarrow=True,arrowhead=3,arrowsize=1.2,arrowwidth=1.7,arrowcolor="#526779")
    # feedback return line
    fig.add_shape(type="line",x0=.815,y0=.38,x1=.815,y1=.18,xref="paper",yref="paper",line=dict(color="#526779",width=1.5))
    fig.add_shape(type="line",x0=.815,y0=.18,x1=.095,y1=.18,xref="paper",yref="paper",line=dict(color="#526779",width=1.5))
    fig.add_shape(type="line",x0=.095,y0=.18,x1=.095,y1=.38,xref="paper",yref="paper",line=dict(color="#526779",width=1.5))
    fig.add_annotation(x=.46,y=.12,xref="paper",yref="paper",text="Umpan balik kecepatan",showarrow=False,font=dict(size=11))
    fig.update_layout(height=250,margin=dict(l=5,r=5,t=5,b=5),showlegend=False,
                      xaxis=dict(visible=False,range=[0,1]),yaxis=dict(visible=False,range=[0,1]))
    return fig

def motor_3d_figure(angle_deg=0):
    # Stylized 3D motor shell and shaft using Plotly surfaces + rotating shaft indicator.
    theta = np.linspace(0, 2*np.pi, 48)
    z = np.linspace(-1.2, 1.2, 20)
    T,Z = np.meshgrid(theta,z)
    X = .8*np.cos(T); Y=.8*np.sin(T)
    fig = go.Figure()
    fig.add_surface(x=X,y=Y,z=Z,colorscale=[[0,"#426b83"],[1,"#89b5c9"]],showscale=False,
                    opacity=.78,lighting=dict(ambient=.55,diffuse=.8,specular=.5),name="Housing")
    # end rings
    for zz in [-1.2,1.2]:
        fig.add_trace(go.Scatter3d(x=.8*np.cos(theta),y=.8*np.sin(theta),z=np.full_like(theta,zz),
            mode="lines",line=dict(color="#16364a",width=5),showlegend=False,hoverinfo="skip"))
    # shaft direction rotates around z axis visually
    a=np.deg2rad(angle_deg)
    x0,y0=.95*np.cos(a),.95*np.sin(a)
    fig.add_trace(go.Scatter3d(x=[0,x0],y=[0,y0],z=[0,0],mode="lines",
        line=dict(color="#e47c36",width=12),name="Rotor / shaft"))
    fig.add_trace(go.Scatter3d(x=[x0],y=[y0],z=[0],mode="markers",
        marker=dict(size=5,color="#f4b183"),showlegend=False,hoverinfo="skip"))
    fig.update_layout(height=390,margin=dict(l=0,r=0,t=5,b=0),scene=dict(
        xaxis=dict(visible=False,range=[-1.35,1.35]),yaxis=dict(visible=False,range=[-1.35,1.35]),
        zaxis=dict(visible=False,range=[-1.4,1.4]),aspectmode="cube",
        camera=dict(eye=dict(x=1.5,y=1.6,z=1.15))),
        legend=dict(orientation="h",yanchor="bottom",y=0.01,xanchor="left",x=0.02))
    return fig

def response_chart(t, y, target=None, play=False):
    # Animated trace with Play/Pause and a time slider, plus hover inspection.
    fig = go.Figure(
        data=[go.Scatter(x=t[:1], y=y[:1], mode="lines",
                         name="Kecepatan (RPM)", line=dict(width=3, color="#168aad"))],
        frames=[go.Frame(
            data=[go.Scatter(x=t[:k+1], y=y[:k+1])],
            name=str(k)
        ) for k in range(1, len(t), max(1, len(t)//100))]
    )
    if target is not None:
        fig.add_hline(y=target, line_dash="dash", line_color="#e07a3f",
                      annotation_text=f"Target {target} RPM")
    steps = []
    frame_indices = list(range(1, len(t), max(1, len(t)//100)))
    for k in frame_indices:
        steps.append(dict(method="animate", args=[[str(k)], {"mode":"immediate",
            "frame":{"duration":20,"redraw":False}, "transition":{"duration":0}}],
            label=f"{t[k]:.1f}s"))
    fig.update_layout(
        height=390, margin=dict(l=15,r=15,t=20,b=20), xaxis_title="Waktu (s)",
        yaxis_title="Kecepatan (RPM)", hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(130,150,170,.06)",
        updatemenus=[dict(type="buttons", showactive=False, x=0, y=1.14,
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, {"frame":{"duration":25,"redraw":False},
                                  "fromcurrent":True,"transition":{"duration":0}}]),
                dict(label="Ⅱ Pause", method="animate",
                     args=[[None], {"mode":"immediate","frame":{"duration":0,"redraw":False},
                                    "transition":{"duration":0}}])
            ])],
        sliders=[dict(active=0, steps=steps, x=0.08, y=-0.12, len=0.9,
            currentvalue={"prefix":"Waktu: "}, pad={"t":25})]
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor")
    return fig

def parameter_panel(prefix):
    c1,c2,c3=st.columns(3)
    with c1:
        R=st.slider("R · Resistansi (Ω)",.5,10.0,2.0,.1,key=f"{prefix}R")
        L=st.slider("L · Induktansi (H)",.05,2.0,.5,.05,key=f"{prefix}L")
    with c2:
        J=st.slider("J · Inersia (kg·m²)",.005,.1,.02,.005,key=f"{prefix}J")
        B=st.slider("B · Gesekan viskos",.01,1.0,.2,.01,key=f"{prefix}B")
    with c3:
        Ke=st.slider("Ke · Back-EMF",.005,.1,.02,.005,key=f"{prefix}Ke")
        Kt=st.slider("Kt · Konstanta torsi",.005,.1,.02,.005,key=f"{prefix}Kt")
    return dict(R=R,L=L,J=J,B=B,Ke=Ke,Kt=Kt)

# ----------------- session / role prototype -----------------
if "role" not in st.session_state:
    st.session_state.role = "Praktikan"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

with st.sidebar:
    st.markdown("## BME Control Lab")
    st.caption("Virtual laboratory • MOOC")
    role = st.selectbox("Masuk sebagai (demo)", ["Praktikan","Dosen","Admin"],
                        index=["Praktikan","Dosen","Admin"].index(st.session_state.role))
    st.session_state.role = role
    st.divider()
    pages = ["Dashboard utama","1 · Respons sistem","2 · Belajar tuning PID","3 · Studi kasus","Panduan & model"]
    page = st.radio("Menu",pages,index=0)
    st.divider()
    st.caption("Role di sini hanya simulasi antarmuka. Belum ada autentikasi atau penyimpanan akun.")

if page == "Dashboard utama":
    st.markdown('<div class="hero"><h1>Virtual Laboratory Sistem Kontrol</h1><p>Eksplorasi model motor DC, pahami respons transien, dan latih tuning PID melalui simulasi interaktif.</p></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("Modul pembelajaran","3")
    c2.metric("Model","Motor DC")
    c3.metric("Role aktif",role)
    st.subheader("Mulai dari sini")
    cards=st.columns(3)
    with cards[0]:
        st.markdown("### 01 · Respons sistem")
        st.write("Ubah tegangan dan parameter motor, lalu baca rise time, overshoot, dan settling time.")
        if st.button("Buka respons sistem",use_container_width=True): st.session_state.goto="1 · Respons sistem"; st.rerun()
    with cards[1]:
        st.markdown("### 02 · Belajar tuning PID")
        st.write("Pelajari fungsi P, I, D; ubah gain satu per satu dan bandingkan hasilnya.")
        if st.button("Belajar PID",use_container_width=True): st.session_state.goto="2 · Belajar tuning PID"; st.rerun()
    with cards[2]:
        st.markdown("### 03 · Studi kasus")
        st.write("Terapkan konsep kontroler pada skenario motor DC untuk mekanisme pompa.")
        if st.button("Buka studi kasus",use_container_width=True): st.session_state.goto="3 · Studi kasus"; st.rerun()
    if "goto" in st.session_state:
        st.info(f"Pilih menu **{st.session_state.goto}** pada sidebar untuk membuka modul.")
    st.subheader("Blok diagram sistem kontrol")
    st.plotly_chart(block_diagram(controller="PID"),use_container_width=True,config={"displayModeBar":False})
    st.caption("Diagram closed-loop generik: setpoint → controller → motor DC → sensor, dengan umpan balik kecepatan.")

elif page == "1 · Respons sistem":
    st.title("01 · Analisis respons sistem")
    st.write("**Tujuan:** memahami hubungan tegangan masukan dan parameter fisik dengan respons kecepatan motor.")
    p=parameter_panel("m1")
    c1,c2=st.columns([1,1])
    with c1: vin=st.select_slider("Tegangan step (V)",[0,3,6,9,12],value=6)
    with c2: duration=st.slider("Durasi (s)",1.0,10.0,5.0,.5,key="dur1")
    if st.button("▶ Jalankan simulasi",type="primary",key="sim1"):
        t,rpm,current,voltage=simulate_motor(duration=duration,Vstep=vin,**p)
        st.session_state.last_result={"t":t,"rpm":rpm,"current":current,"voltage":voltage,"target":None}
    if st.session_state.last_result is not None:
        res=st.session_state.last_result
        left,right=st.columns([1.4,1])
        with left:
            st.plotly_chart(response_chart(res["t"],res["rpm"]),use_container_width=True)
            st.caption("Grafik interaktif: arahkan kursor ke kurva untuk membaca nilai pada waktu tertentu.")
        with right:
            st.plotly_chart(motor_3d_figure(angle_deg=float(res["rpm"][-1])%360),use_container_width=True,config={"displayModeBar":False})
        met=calc_metrics(res["t"],res["rpm"])
        cols=st.columns(4)
        for col,key in zip(cols,["Nilai akhir (RPM)","Rise time 10–90% (s)","Settling time ±2% (s)","Overshoot (%)"]):
            val=met[key]; col.metric(key,"—" if not np.isfinite(val) else f"{val:.2f}")
        df=pd.DataFrame({"time_s":res["t"],"speed_RPM":res["rpm"],"current_A":res["current"],"voltage_V":res["voltage"]})
        st.download_button("Unduh data CSV",df.to_csv(index=False).encode(),"respons_motor_dc.csv","text/csv")
    st.subheader("Cek pemahaman")
    q1=st.radio("Jika tegangan input naik, kecepatan tunak motor idealnya cenderung…",["Naik","Turun","Tidak berubah"],key="m1q1")
    q2=st.radio("Parameter J merepresentasikan…",["Inersia rotor","Resistansi armatur","Konstanta back-EMF"],key="m1q2")
    if st.button("Periksa jawaban",key="m1check"):
        score=int(q1=="Naik")+int(q2=="Inersia rotor")
        st.success(f"Skor latihan: {score}/2")

elif page == "2 · Belajar tuning PID":
    st.title("02 · Belajar tuning PID")
    st.write("Ikuti urutan pembelajaran. Ubah satu gain setiap kali agar pengaruhnya lebih mudah diamati.")
    with st.expander("Langkah 1 — Pahami peran tiap komponen",expanded=True):
        st.markdown("""
        - **P — Proportional:** memberi aksi berdasarkan error saat ini; dapat mempercepat respons, tetapi gain berlebihan dapat meningkatkan overshoot.
        - **I — Integral:** mengakumulasi error sehingga dapat mengurangi error tunak; terlalu besar dapat menambah overshoot dan memperlambat settling.
        - **D — Derivative:** merespons laju perubahan error; dapat membantu meredam perubahan cepat, tetapi sensitif terhadap noise pada sistem nyata.

        Bentuk paralel: `u(t) = Kp e(t) + Ki ∫e(t)dt + Kd de(t)/dt`.
        """)
    p=parameter_panel("pid")
    st.subheader("Langkah 2 — Atur target dan gain")
    a,b=st.columns(2)
    with a:
        target=st.slider("Target kecepatan (RPM)",100,2000,800,50,key="pidtarget")
        mode=st.selectbox("Mode kontroler",["P","PI","PD","PID"],index=3)
        duration=st.slider("Durasi simulasi (s)",1.0,10.0,5.0,.5,key="pidduration")
    with b:
        kp=st.slider("Kp",0.0,.2,.02,.002,format="%.3f")
        ki=st.slider("Ki",0.0,.2,.02,.002,format="%.3f")
        kd=st.slider("Kd",0.0,.02,.001,.0005,format="%.4f")
    st.subheader("Blok diagram closed-loop")
    st.plotly_chart(block_diagram(controller=mode),use_container_width=True,config={"displayModeBar":False})
    if st.button("▶ Simulasikan tuning ini",type="primary",key="pidsim"):
        t,rpm,current,voltage=simulate_motor(duration=duration,controller=mode,target_rpm=target,kp=kp,ki=ki,kd=kd,**p)
        st.session_state.pid_result={"t":t,"rpm":rpm,"current":current,"voltage":voltage,"target":target,"mode":mode,"kp":kp,"ki":ki,"kd":kd}
    if "pid_result" in st.session_state:
        res=st.session_state.pid_result
        l,r=st.columns([1.35,1])
        with l: st.plotly_chart(response_chart(res["t"],res["rpm"],res["target"]),use_container_width=True)
        with r: st.plotly_chart(motor_3d_figure(angle_deg=float(res["rpm"][-1])%360),use_container_width=True,config={"displayModeBar":False})
        met=calc_metrics(res["t"],res["rpm"],res["target"])
        st.subheader("Ringkasan performa")
        cols=st.columns(5)
        for col,(key,val) in zip(cols,met.items()):
            col.metric(key,"—" if not np.isfinite(val) else f"{val:.2f}")
        st.info("Latihan tuning: ubah hanya satu parameter gain, jalankan kembali, lalu bandingkan metrik. Ini membantu mengisolasi pengaruh gain.")
        st.download_button("Unduh data tuning CSV",pd.DataFrame({"time_s":res["t"],"target_RPM":res["target"],"speed_RPM":res["rpm"],"voltage_V":res["voltage"]}).to_csv(index=False).encode(),"pid_tuning.csv","text/csv")
    st.subheader("Langkah 3 — Kuis")
    q1=st.radio("Gain mana yang mengakumulasi error dari waktu ke waktu?",["Kp","Ki","Kd"],key="pidq1")
    q2=st.radio("Apa praktik yang baik saat belajar tuning?",["Ubah satu gain setiap percobaan","Ubah semua gain sekaligus","Nilai dari tampilan animasi saja"],key="pidq2")
    q3=st.radio("Metrik apa yang membantu menilai osilasi melewati target?",["Overshoot","Warna motor","Nama kontroler"],key="pidq3")
    if st.button("Nilai kuis PID",key="pidcheck"):
        score=int(q1=="Ki")+int(q2=="Ubah satu gain setiap percobaan")+int(q3=="Overshoot")
        st.success(f"Skor kuis: {score}/3")
        if score<3: st.write("Tinjau kembali peran integral dan metrik respons, lalu coba lagi.")

elif page == "3 · Studi kasus":
    st.title("03 · Studi kasus: motor DC pada mekanisme pompa")
    st.warning("Skenario edukasi. Simulasi ini bukan model tervalidasi untuk infusion pump klinis.")
    st.markdown("""
    **Tantangan:** pilih pengaturan kontroler yang mengejar target kecepatan dengan error tunak dan overshoot yang rendah.
    Anda harus menggunakan grafik dan metrik sebagai bukti, bukan hanya mengandalkan animasi.
    """)
    p=parameter_panel("case")
    a,b=st.columns(2)
    with a:
        target=st.slider("Target RPM",100,1800,700,50,key="casetarget")
        mode=st.selectbox("Kontroler",["P","PI","PD","PID"],index=3,key="casemode")
    with b:
        kp=st.slider("Kp studi kasus",0.0,.2,.02,.002,key="casekp")
        ki=st.slider("Ki studi kasus",0.0,.2,.02,.002,key="caseki")
        kd=st.slider("Kd studi kasus",0.0,.02,.001,.0005,key="casekd")
    st.plotly_chart(block_diagram(controller=mode),use_container_width=True,config={"displayModeBar":False})
    if st.button("Jalankan studi kasus",type="primary"):
        t,rpm,current,voltage=simulate_motor(controller=mode,target_rpm=target,kp=kp,ki=ki,kd=kd,**p)
        st.session_state.case_result=(t,rpm,current,voltage,target)
    if "case_result" in st.session_state:
        t,rpm,current,voltage,target=st.session_state.case_result
        x,y=st.columns([1.3,1])
        with x: st.plotly_chart(response_chart(t,rpm,target),use_container_width=True)
        with y: st.plotly_chart(motor_3d_figure(angle_deg=float(rpm[-1])%360),use_container_width=True,config={"displayModeBar":False})
        st.write("Metrik respons:")
        st.dataframe(pd.DataFrame([calc_metrics(t,rpm,target)]),use_container_width=True)
    st.subheader("Asesmen")
    q1=st.radio("1. Jika error tunak masih besar, komponen mana yang dapat membantu menguranginya?",["Integral (I)","Derivative (D)","Tidak ada"],key="caseq1")
    q2=st.radio("2. Jika overshoot terlalu tinggi, langkah ilmiah yang tepat adalah…",["Tuning ulang dan bandingkan metrik","Menaikkan semua gain","Mengabaikan target"],key="caseq2")
    q3=st.radio("3. Apakah RPM saja membuktikan akurasi laju aliran klinis?",["Ya","Tidak, perlu model pompa dan kalibrasi/validasi"],key="caseq3")
    if st.button("Kirim jawaban latihan"):
        score=int(q1=="Integral (I)")+int(q2=="Tuning ulang dan bandingkan metrik")+int(q3=="Tidak, perlu model pompa dan kalibrasi/validasi")
        st.success(f"Skor latihan: {score}/3")
        st.caption("Skor demo tidak tersimpan ke server.")

else:
    st.title("Panduan & model matematis")
    st.markdown("""
    ### Model armature-controlled DC motor
    `L di/dt = V - R i - Ke ω`

    `J dω/dt = Kt i - B ω - T_load`

    - `V`: tegangan armatur (V)
    - `i`: arus armatur (A)
    - `R`, `L`: resistansi dan induktansi armatur
    - `Ke`: konstanta back-EMF
    - `J`: inersia rotor
    - `B`: koefisien gesekan viskos
    - `Kt`: konstanta torsi
    - `ω`: kecepatan sudut (rad/s), dikonversi menjadi RPM

    ### Keterbatasan versi demo
    - Pemilih role Mahasiswa/Dosen/Admin hanya demo tampilan, **bukan autentikasi dan otorisasi sungguhan**.
    - Skor tidak tersimpan ke database atau LMS.
    - Animasi 3D adalah ilustrasi visual rotor/housing, bukan simulasi CAD atau dinamika 3D tervalidasi.
    - Integrasi numerik Euler dan parameter perlu divalidasi sebelum digunakan sebagai asesmen sumatif.
    - Studi kasus pompa hanya edukatif; bukan alat medis dan bukan model laju aliran klinis.
    """)
    st.plotly_chart(block_diagram(),use_container_width=True,config={"displayModeBar":False})
