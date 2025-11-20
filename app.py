import streamlit as st
import os
import time
import io
from pydub import AudioSegment
from pedalboard import Pedalboard, Compressor, Reverb, Limiter, HighpassFilter, Chorus, NoiseGate, LowShelfFilter, LowPassFilter, HighShelfFilter, Gain, Delay
from pedalboard.io import AudioFile
import numpy as np

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="FKRed AI Studio",
    page_icon="🔥",
    layout="wide"
)

# --- ÖZEL CSS TASARIMI (PITCH BLACK & NEON) ---
NEON_RED = "#FF3366" 
DARK_GRAY = "#1A1A1A" 

st.markdown(f"""
<style>
    /* Global App Background - TAMAMEN SİYAH */
    .stApp {{
        background-image: linear-gradient(to bottom, #000000, #000000); 
        color: #E0E0E0;
    }}
    
    /* Ana Başlık Stili - NEON VURGU */
    h1 {{
        text-align: center;
        background: -webkit-linear-gradient(90deg, #FF6666, #FF0066);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem !important;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px {NEON_RED};
        margin-bottom: 0px; 
    }}
    
    /* MFN Production Alt Başlığı */
    .mfn-production {{
        text-align: center;
        background: -webkit-linear-gradient(90deg, #FF6666, #FF0066);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 5px;
    }}

    /* Streamlit Alt Başlığı */
    .subtitle {{
        text-align: center;
        color: #FFC0C0;
        font-size: 1.3rem;
        margin-bottom: 40px;
        margin-top: 15px;
    }}

    /* Input/Box Tasarımı - NEON KONTUR */
    .stFileUploader, [data-testid="stTextInput"], [data-testid="stSelectbox"] {{
        background-color: {DARK_GRAY};
        border: 1px solid {NEON_RED} !important;
        border-radius: 8px;
        padding: 10px;
        color: #E0E0E0;
    }}
    
    /* Ana Çalışma Butonu - NEON Gradient */
    .stButton>button {{
        background: linear-gradient(90deg, #FF0066 0%, #CC0066 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        box-shadow: 0 4px 25px rgba(255, 0, 102, 0.7);
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        transform: scale(1.03);
    }}
    
    /* İndirme Kilit Kutusu */
    .free-box {{
        background-color: #262626; 
        border: 1px solid {NEON_RED};
        color: white; 
        padding: 20px; 
        border-radius: 15px;
    }}

    /* Alt Bilgi (Footer) */
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000;
        color: #555;
        text-align: right;
        padding: 5px 15px;
        font-size: 0.8rem;
        z-index: 100;
        border-top: 1px solid #333;
    }}
</style>
""".format(NEON_RED=NEON_RED, DARK_GRAY=DARK_GRAY), unsafe_allow_html=True)


# --- AYARLAR ---
REKLAM_LINKI = "https://www.youtube.com/watch?v=sgWLgb5-aJY" 

# --- HAFIZA (Session State) ---
if 'processed' not in st.session_state: st.session_state.processed = False
if 'output_path' not in st.session_state: st.session_state.output_path = None
if 'download_ready' not in st.session_state: st.session_state.download_ready = False
if 'file_ext' not in st.session_state: st.session_state.file_ext = 'wav'
if 'original_data' not in st.session_state: st.session_state.original_data = None
if 'original_mime' not in st.session_state: st.session_state.original_mime = None

# --- YARDIMCI FONKSİYONLAR ---
def get_mime_type(ext):
    if ext == 'mp3': return 'audio/mpeg'
    if ext in ['mp4', 'mov', 'm4a']: return 'video/mp4'
    return 'audio/wav'

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
    except Exception as e:
        st.warning(f"Dönüştürme Hatası ({target_ext}). WAV olarak indiriliyor.")
        with open(wav_path, "rb") as f:
            return f.read()

def process_audio_logic():
    if uploaded_file is None:
        st.error("⚠️ Lütfen dosya yükleyin!")
        return

    st.session_state.original_data = uploaded_file.getvalue()
    st.session_state.original_mime = uploaded_file.type
    st.session_state.file_ext = uploaded_file.name.split('.')[-1].lower()

    progress = st.progress(0)
    status = st.empty()
    status.info("⏳ Yapay Zeka Çalışıyor...")

    try:
        os.makedirs("temp", exist_ok=True)
        input_path = os.path.join("temp", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        progress.progress(30)
        
        # Dosyayı yükle
        audio = AudioSegment.from_file(input_path)
        
        # Mono ise stereo yap
        if audio.channels == 1:
            audio = audio.set_channels(2)
        
        # Müzik modunda, başlangıçta 16-bit'e çevirerek kalite kaybını önle
        if "MÜZİK" in processing_mode:
             audio = audio.set_sample_width(2)

        wav_path = os.path.join("temp", "temp_input.wav")
        audio.export(wav_path, format="wav")

        with AudioFile(wav_path) as f:
            audio_data = f.read(f.frames)
            samplerate = f.sample_rate

        progress.progress(60)

        # Efekt Zincirleri
        board = None
        if "VLOG" in processing_mode: 
            board = Pedalboard([
                NoiseGate(threshold_db=-35, ratio=3), 
                HighpassFilter(cutoff_frequency_hz=90), 
                Compressor(threshold_db=-16, ratio=3), 
                Gain(gain_db=2.0), 
                Limiter(threshold_db=-1.0)
            ])
        
        elif "MÜZİK" in processing_mode: 
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=50), 
                HighShelfFilter(cutoff_frequency_hz=7000, gain_db=2.0),
                Compressor(threshold_db=-14, ratio=2.5),
                Chorus(rate_hz=0.8, depth=0.015, mix=0.15), 
                Delay(delay_seconds=0.15, feedback=0.1, mix=0.15), 
                Reverb(room_size=0.4, damping=0.7, wet_level=0.20), 
                Limiter(threshold_db=-1.0)
            ])
        elif "PODCAST" in processing_mode: 
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=50), 
                LowShelfFilter(cutoff_frequency_hz=120, gain_db=5.0), 
                Compressor(threshold_db=-18, ratio=4), 
                Limiter(threshold_db=-1.0)
            ])

        effected_audio = board(audio_data, samplerate)
        output_path = os.path.join("temp", "FKRed_Processed_WAV.wav")
        with AudioFile(output_path
