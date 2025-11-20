
import streamlit as st
import os
import time
from pydub import AudioSegment
from pedalboard import Pedalboard, Compressor, Reverb, Limiter, HighpassFilter, Chorus, NoiseGate, LowShelfFilter, HighShelfFilter, Gain, Delay
from pedalboard.io import AudioFile
import numpy as np

# --- SAYFA AYARLARI (GENİŞ MOD) ---
st.set_page_config(
    page_title="FKRed AI Studio",
    page_icon="🔥",
    layout="wide"
)

# --- ÖZEL CSS TASARIMI (BÜYÜ BURADA) ---
st.markdown("""
<style>
    /* Arka planı ve genel fontu güzelleştir */
    .stApp {
        background-image: linear-gradient(to bottom, #0E1117, #161B22);
    }
    
    /* Başlık Stili */
    h1 {
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
        background: -webkit-linear-gradient(#FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        font-weight: 800;
        margin-bottom: 0px;
    }
    
    /* Alt Başlık */
    .subtitle {
        text-align: center;
        color: #AAAAAA;
        font-size: 1.2rem;
        margin-bottom: 40px;
    }

    /* Buton Tasarımı (NEON EFEKT) */
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF0000 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 18px;
        font-weight: bold;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.7);
    }

    /* Bilgi Kutuları */
    .info-box {
        background-color: #1F2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 20px;
    }
    
    /* Yükleme Alanı Çerçevesi */
    [data-testid="stFileUploader"] {
        background-color: #161B22;
        border: 1px dashed #FF4B4B;
        border-radius: 10px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK BÖLÜMÜ ---
st.markdown("<h1>🔥 FKRed AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>İçerik Üreticileri İçin Yeni Nesil Ses Mühendisliği</p>", unsafe_allow_html=True)

# --- AYARLAR ---
REKLAM_LINKI = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Buraya kendi videonu koy

# --- ANA ARAYÜZ (KARTLAR HALİNDE) ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 1. Dosya Yükleme Merkezi")
    st.markdown("<div style='color: #888; margin-bottom: 10px;'>Videonuzun veya ses dosyanızın kalitesini artırmak için aşağıya bırakın.</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Dosya Seçin", type=["wav", "mp3", "mp4", "mov", "m4a"], label_visibility="collapsed")

    st.markdown("---")
    
    st.markdown("### 🎛️ 2. Atmosfer Seçimi")
    processing_mode = st.radio(
        "Sesin modu ne olsun?",
        ("🎤 VLOG (Temiz & Net)", "🎸 MÜZİK (Akustik & Sıcak)", "🎙️ PODCAST (Tok & Radyo)"),
        index=0
    )
    
    # Mod Bilgi Kartları (Custom HTML)
    if "VLOG" in processing_mode:
        st.markdown("""
        <div class='info-box'>
            <b>🎥 Vlog Modu:</b><br>
            Dip sesleri siler, rüzgarı keser ve sesi yüzüne yaklaştırır. Reverb yoktur, çok nettir.
        </div>
        """, unsafe_allow_html=True)
    elif "MÜZİK" in processing_mode:
        st.markdown("""
        <div class='info-box'>
            <b>🎵 Müzik Modu:</b><br>
            Akustik bir stüdyo hissi verir. Hafif 'Delay' ve sıcak 'Reverb' ekler.
        </div>
        """, unsafe_allow_html=True)
    elif "PODCAST" in processing_mode:
        st.markdown("""
        <div class='info-box'>
            <b>🎙️ Podcast Modu:</b><br>
            Radyocu gibi tok bir ses. Bass frekanslarını güçlendirir ve patlamaları önler.
        </div>
        """, unsafe_allow_html=True)

# --- İŞLEM FONKSİYONU ---
def process_audio_logic():
    if uploaded_file is None:
        st.error("⚠️ Lütfen önce işlenecek bir dosya yükleyin!")
        return

    # Progress Bar ve Durum
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.markdown("**⏳ Yapay Zeka Isınıyor...**")
    time.sleep(0.5)

    try:
        # 1. Hazırlık
        os.makedirs("temp", exist_ok=True)
        input_path = os.path.join("temp", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        progress_bar.progress(20)
        status_text.markdown("**🔄 Ses Ayrıştırılıyor...**")

        # 2. Sese Çevir
        audio = AudioSegment.from_file(input_path)
        if "MÜZİK" in processing_mode and audio.channels == 1:
            audio = audio.set_channels(2)
        
        wav_path = os.path.join("temp", "temp_input.wav")
        audio.export(wav_path, format="wav")

        with AudioFile(wav_path) as f:
            audio_data = f.read(f.frames)
            samplerate = f.samplerate

        progress_bar.progress(50)
        status_text.markdown(f"**🎛️ {processing_mode} Efekt Zinciri Uygulanıyor...**")

        # 3. Efekt Zincirleri
        board = None
        if "VLOG" in processing_mode:
            board = Pedalboard([
                NoiseGate(threshold_db=-35, ratio=3, release_ms=200),
                HighpassFilter(cutoff_frequency_hz=90),
                Compressor(threshold_db=-16, ratio=3),
                Gain(gain_db=2.0),
                Limiter(threshold_db=-1.0)
            ])
        elif "MÜZİK" in processing_mode:
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=50), 
                HighShelfFilter(cutoff_frequency_hz=7000, gain_db=3.0),
                Compressor(threshold_db=-12, ratio=2.0),
                Delay(delay_seconds=0.15, feedback=0.1, mix=0.10), 
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
        
        output_path = "FKRed_Output.wav"
        with AudioFile(output_path, 'w', samplerate, effected_audio.shape[0]) as f:
            f.write(effected_audio)

        progress_bar.progress(100)
        status_text.success("✅ İŞLEM TAMAMLANDI!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        # --- SONUÇ ALANI (SAĞ KOLON) ---
        with col2:
            st.markdown("### 🎁 Stüdyo Çıktısı Hazır")
            st.markdown("<div class='info-box' style='border-left: 5px solid #4CAF50;'>Dosyanız hazırlandı! İndirme kilidini açmak için aşağıdaki sponsorumuza göz atın.</div>", unsafe_allow_html=True)
            
            # Video
            st.video(REKLAM_LINKI)
            
            # Sayaç
            sayac_placeholder = st.empty()
            for i in range(10, 0, -1):
                sayac_placeholder.warning(f"🔒 İndirme butonu {i} saniye sonra açılacak...")
                time.sleep(1)
            
            sayac_placeholder.success("🔓 Kilit Açıldı! Dosyanızı İndirebilirsiniz.")
            
            # Audio Player & Download
            st.audio(output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ MASTER WAV İNDİR (Yüksek Kalite)",
                    data=f,
                    file_name="FKRed_Master.wav",
                    mime="audio/wav",
                    help="Stüdyo kalitesinde WAV dosyası"
                )

    except Exception as e:
        status_text.error(f"Hata oluştu: {e}")

# --- BAŞLAT BUTONU (Sol Kolonun Altına) ---
with col1:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 SİHRİ BAŞLAT", use_container_width=True):
        process_audio_logic()
