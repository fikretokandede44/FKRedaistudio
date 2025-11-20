import streamlit as st
import os
import time
import io
from pydub import AudioSegment
from pedalboard import Pedalboard, Compressor, Reverb, Limiter, HighpassFilter, Chorus, NoiseGate, LowShelfFilter, HighShelfFilter, Gain, Delay
from pedalboard.io import AudioFile
import numpy as np

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="FKRed AI Studio",
    page_icon="🔥",
    layout="wide"
)

# --- CSS TASARIMI (NEON BLACK & RED) ---
NEON_RED = "#FF3366" 
DARK_GRAY = "#1A1A1A" 

st.markdown(f"""
<style>
    /* Arka Plan */
    .stApp {{
        background-image: linear-gradient(to bottom, #000000, #050505); 
        color: #E0E0E0;
    }}
    
    /* Başlık */
    h1 {{
        text-align: center;
        background: -webkit-linear-gradient(90deg, #FF6666, #FF0066);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem !important;
        font-weight: 900;
        text-shadow: 0 0 15px {NEON_RED};
        margin-bottom: 0px; 
    }}
    
    /* MFN Production Yazısı */
    .mfn-production {{
        text-align: center;
        color: #FF3333;
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: -10px;
        letter-spacing: 3px;
        opacity: 0.8;
    }}

    /* Alt Başlık */
    .subtitle {{
        text-align: center;
        color: #888;
        font-size: 1rem;
        margin-bottom: 30px;
    }}

    /* Yükleme Kutuları */
    .stFileUploader {{
        border: 1px solid {NEON_RED} !important;
        border-radius: 10px;
        padding: 10px;
    }}
    
    /* Butonlar */
    .stButton>button {{
        background: linear-gradient(90deg, #FF0066 0%, #990033 100%);
        color: white;
        border: none;
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(255, 0, 102, 0.4);
        transition: all 0.3s ease;
        width: 100%;
    }}
    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 0 25px rgba(255, 0, 102, 0.8);
    }}

    /* Footer */
    .footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #000000; color: #444; text-align: center;
        padding: 10px; font-size: 0.8rem; border-top: 1px solid #222;
    }}
</style>
""", unsafe_allow_html=True)

# --- AYARLAR ---
REKLAM_LINKI = "https://www.youtube.com/watch?v=sgWLgb5-aJY" 

# --- HAFIZA ---
if 'processed' not in st.session_state: st.session_state.processed = False
if 'output_path' not in st.session_state: st.session_state.output_path = None
if 'download_ready' not in st.session_state: st.session_state.download_ready = False
if 'file_ext' not in st.session_state: st.session_state.file_ext = 'wav'

# --- FONKSİYONLAR ---
def convert_wav_to_target_format(wav_path, target_ext):
    output_buffer = io.BytesIO()
    try:
        audio = AudioSegment.from_wav(wav_path)
        export_format = 'mp4' if target_ext in ['mp4', 'mov', 'm4a'] else target_ext
        if export_format == 'mp3':
            audio.export(output_buffer, format="mp3", parameters=['-q:a', '0'])
        else:
            audio.export(output_buffer, format=export_format)
        return output_buffer.getvalue()
    except:
        with open(wav_path, "rb") as f: return f.read()

def get_mime(ext):
    if ext == 'mp3': return 'audio/mpeg'
    if ext in ['mp4', 'mov', 'm4a']: return 'video/mp4'
    return 'audio/wav'

def process_audio_logic():
    if uploaded_file is None:
        st.error("⚠️ Dosya yok!")
        return

    st.session_state.file_ext = uploaded_file.name.split('.')[-1].lower()
    
    status = st.empty()
    status.info("⏳ İşleniyor...")
    
    try:
        os.makedirs("temp", exist_ok=True)
        input_path = os.path.join("temp", uploaded_file.name)
        with open(input_path, "wb") as f: f.write(uploaded_file.getbuffer())
        
        audio = AudioSegment.from_file(input_path)
        if "MÜZİK" in processing_mode and audio.channels == 1: audio = audio.set_channels(2)
        if "MÜZİK" in processing_mode: audio = audio.set_sample_width(2)
        
        wav_path = os.path.join("temp", "temp_input.wav")
        audio.export(wav_path, format="wav")

        with AudioFile(wav_path) as f:
            audio_data = f.read(f.frames)
            samplerate = f.samplerate

        # EFEKT ZİNCİRLERİ
        board = None
        if "VLOG" in processing_mode:
            board = Pedalboard([
                NoiseGate(threshold_db=-30, ratio=4),
                HighpassFilter(cutoff_frequency_hz=80),
                Compressor(threshold_db=-16, ratio=3),
                Gain(gain_db=2.0),
                Limiter(threshold_db=-1.0)
            ])
        elif "MÜZİK" in processing_mode:
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=40),
                HighShelfFilter(cutoff_frequency_hz=7500, gain_db=2.0),
                Compressor(threshold_db=-12, ratio=2.5),
                Chorus(rate_hz=1.0, depth=0.02, mix=0.1),
                Delay(delay_seconds=0.2, feedback=0.1, mix=0.15),
                Reverb(room_size=0.5, damping=0.6, wet_level=0.20),
                Limiter(threshold_db=-1.0)
            ])
        elif "PODCAST" in processing_mode:
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=60),
                LowShelfFilter(cutoff_frequency_hz=100, gain_db=4.0),
                Compressor(threshold_db=-18, ratio=4),
                Limiter(threshold_db=-1.0)
            ])

        effected = board(audio_data, samplerate)
        output_path = os.path.join("temp", "processed.wav")
        
        # Hata Düzeltildi: Tek satırda yazma işlemi
        with AudioFile(output_path, 'w', samplerate, effected.shape[0]) as f:
            f.write(effected)

        st.session_state.processed = True
        st.session_state.output_path = output_path
        st.session_state.download_ready = False
        status.success("✅ Tamamlandı!")

    except Exception as e:
        status.error(f"Hata: {e}")

# --- ARAYÜZ ---
st.markdown("<h1>🔥 FKRed AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='mfn-production'>MFN PRODUCTION</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Profesyonel İçerik Üretici Stüdyosu</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 Yükle")
    uploaded_file = st.file_uploader("Dosya", type=["wav", "mp3", "mp4", "mov", "m4a"], label_visibility="collapsed")
    st.markdown("### 🎛️ Mod")
    processing_mode = st.radio("Seçim", ("🎤 VLOG", "🎸 MÜZİK (Akustik)", "🎙️ PODCAST"))
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 SİHRİ BAŞLAT"):
        process_audio_logic()

with col2:
    if st.session_state.processed:
        st.markdown("### 🎧 Sonuç")
        st.audio(st.session_state.output_path)
        st.markdown("---")
        
        st.info("📢 İndirmek için aşağıdaki videoyu izleyiniz (10 sn).")
        st.video(REKLAM_LINKI)
        
        if not st.session_state.download_ready:
            if st.button("⏱️ İndirmeyi Başlat"):
                bar = st.progress(0)
                for i in range(10):
                    time.sleep(1)
                    bar.progress((i+1)*10)
                st.session_state.download_ready = True
                st.rerun()
        
        if st.session_state.download_ready:
            data = convert_wav_to_target_format(st.session_state.output_path, st.session_state.file_ext)
            mime = get_mime(st.session_state.file_ext)
            st.download_button(f"⬇️ İNDİR ({st.session_state.file_ext.upper()})", data, f"FKRed_Master.{st.session_state.file_ext}", mime)

st.markdown("<div class='footer'>© 2025 FKRed AI Studio | Fikret Okan Dede</div>", unsafe_allow_html=True)
