import static_ffmpeg
static_ffmpeg.add_paths()

import streamlit as st
import os
import time
from pydub import AudioSegment
from pedalboard import Pedalboard, Compressor, Reverb, Limiter, HighpassFilter, Chorus, NoiseGate, LowShelfFilter, HighShelfFilter, Gain, Delay
from pedalboard.io import AudioFile
import numpy as np
import io # Byte verileri yönetmek için gerekli

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="FKRed AI Studio",
    page_icon="🔥",
    layout="wide"
)

# --- ÖZEL TASARIM (CSS) ---
st.markdown("""
<style>
    .stApp { background-image: linear-gradient(to bottom, #0E1117, #161B22); }
    h1 {
        text-align: center;
        background: -webkit-linear-gradient(#FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        font-weight: 800;
    }
    .premium-box {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: black; padding: 20px; border-radius: 15px; text-align: center;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.4); margin-bottom: 20px;
    }
    .free-box {
        background-color: #1F2937; border: 1px solid #FF4B4B;
        color: white; padding: 20px; border-radius: 15px; text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 10px; font-weight: bold; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- AYARLAR ---
REKLAM_LINKI = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
ODEME_LINKI = "https://shopier.com/linkin" 

# --- HAFIZA (Session State) ---
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'output_path' not in st.session_state:
    st.session_state.output_path = None
if 'download_ready' not in st.session_state:
    st.session_state.download_ready = False
if 'file_ext' not in st.session_state: # Yeni: Orijinal uzantıyı tutar
    st.session_state.file_ext = 'wav'

# --- BAŞLIK ---
st.markdown("<h1>🔥 FKRed AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>İçerik Üreticileri İçin Akıllı Ses Stüdyosu</p>", unsafe_allow_html=True)

# --- ARAYÜZ ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 Dosya Yükleme")
    uploaded_file = st.file_uploader("Dosya Seçin", type=["wav", "mp3", "mp4", "mov", "m4a"], label_visibility="collapsed")

    st.markdown("### 🎛️ Mod Seçimi")
    processing_mode = st.radio("Sesin modu ne olsun?", ("🎤 VLOG (Temiz & Net)", "🎸 MÜZİK (Akustik & Sıcak)", "🎙️ PODCAST (Tok & Radyo)"))

# --- YARDIMCI FONKSİYONLAR ---

def get_mime_type(ext):
    # İndirme butonunun doğru formatı görmesi için
    if ext == 'mp3': return 'audio/mpeg'
    if ext == 'm4a': return 'audio/m4a'
    if ext in ['mp4', 'mov']: return 'video/mp4' # Video formatı için
    return 'audio/wav'

def convert_wav_to_target_format(wav_path, target_ext):
    # WAV'dan orijinal formata geri çevirme
    audio = AudioSegment.from_wav(wav_path)
    output_buffer = io.BytesIO()
    
    # MP4 ve MOV formatları için sadece sesi dışa aktar (m4a formatında)
    export_format = 'm4a' if target_ext in ['mp4', 'mov', 'm4a'] else target_ext
    if export_format == 'mp3':
        audio.export(output_buffer, format="mp3", parameters=['-q:a', '0']) # Yüksek kaliteli MP3
    else:
        audio.export(output_buffer, format=export_format)
        
    return output_buffer.getvalue()

# --- İŞLEM FONKSİYONU ---
def process_audio_logic():
    if uploaded_file is None:
        st.error("⚠️ Lütfen dosya yükleyin!")
        return
    
    # ⚠️ DOSYA UZANTISINI HAFIZAYA KAYDET ⚠️
    file_extension = uploaded_file.name.split('.')[-1].lower()
    st.session_state.file_ext = file_extension
    # Video/M4A yüklenirse, çıktı M4A/MP4 olmalı.
    st.session_state.output_name = f"FKRed_Master.{file_extension}"

    progress = st.progress(0)
    status = st.empty()
    status.info("⏳ Yapay Zeka Çalışıyor...")

    try:
        # ... (Processing Logic - Remains the same) ...
        os.makedirs("temp", exist_ok=True)
        input_path = os.path.join("temp", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        progress.progress(30)

        # Sese Çevir
        audio = AudioSegment.from_file(input_path)
        if "MÜZİK" in processing_mode and audio.channels == 1:
            audio = audio.set_channels(2)
        
        wav_path = os.path.join("temp", "temp_input.wav")
        audio.export(wav_path, format="wav")

        with AudioFile(wav_path) as f:
            audio_data = f.read(f.frames)
            samplerate = f.samplerate

        progress.progress(60)

        # Efekt Zincirleri (Aynı kalır)
        board = None
        if "VLOG" in processing_mode:
            board = Pedalboard([NoiseGate(threshold_db=-35, ratio=3), HighpassFilter(cutoff_frequency_hz=90), Compressor(threshold_db=-16, ratio=3), Gain(gain_db=2.0), Limiter(threshold_db=-1.0)])
        elif "MÜZİK" in processing_mode:
            board = Pedalboard([HighpassFilter(cutoff_frequency_hz=50), HighShelfFilter(cutoff_frequency_hz=7000, gain_db=3.0), Compressor(threshold_db=-12, ratio=2.0), Delay(delay_seconds=0.15, feedback=0.1, mix=0.10), Reverb(room_size=0.4, damping=0.7, wet_level=0.20), Limiter(threshold_db=-1.0)])
        elif "PODCAST" in processing_mode:
            board = Pedalboard([HighpassFilter(cutoff_frequency_hz=50), LowShelfFilter(cutoff_frequency_hz=120, gain_db=5.0), Compressor(threshold_db=-18, ratio=4), Limiter(threshold_db=-1.0)])

        effected_audio = board(audio_data, samplerate)
        
        # Çıktı (WAV olarak kaydet)
        output_path = os.path.join("temp", "FKRed_Processed_WAV.wav") # Geçici WAV dosyası
        with AudioFile(output_path, 'w', samplerate, effected_audio.shape[0]) as f:
            f.write(effected_audio)

        # HAFIZAYA KAYDET
        st.session_state.processed = True
        st.session_state.output_path = output_path # Hafızada WAV dosyası duruyor

        progress.progress(100)
        status.success("✅ İşlem Tamamlandı!")
        time.sleep(1)
        progress.empty()
        status.empty()

    except Exception as e:
        status.error(f"Hata: {e}")

# --- İNDİRME FONKSİYONU ---
def get_download_data(output_path, target_ext):
    if not os.path.exists(output_path):
        return None
    
    # WAV olarak işlenen dosyayı tekrar çevir
    if target_ext in ['mp3', 'm4a', 'flac', 'mp4', 'mov']:
        output_buffer = io.BytesIO()
        try:
            audio = AudioSegment.from_wav(output_path)
            export_format = 'mp4' if target_ext in ['mp4', 'mov', 'm4a'] else target_ext
            
            # MP3 kalitesini artır
            if export_format == 'mp3':
                audio.export(output_buffer, format="mp3", parameters=['-q:a', '0']) # Yüksek kaliteli MP3
            else:
                audio.export(output_buffer, format=export_format)
                
            return output_buffer.getvalue()
        except Exception as e:
            st.error(f"Dönüştürme Hatası: {e}")
            return None
    
    # WAV ise direkt dosyayı oku
    with open(output_path, "rb") as f:
        return f.read()

# --- BAŞLAT BUTONU ---
with col1:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 SESİ GÜZELLEŞTİR", use_container_width=True):
        st.session_state.download_ready = False # Yeniden işlem başlatınca kilidi sıfırla
        process_audio_logic()

# --- SONUÇ VE İNDİRME ALANI (SAĞ KOLON) ---
with col2:
    if st.session_state.processed:
        st.markdown("### 🎁 Sonuç Hazır")
        st.audio(st.session_state.output_path)
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["💎 PREMIUM ($10)", "🆓 BEDAVA (10 Sn Bekle)"])
        
        # --- PREMIUM ---
        with tab1:
            st.markdown("""
            <div class='premium-box'>
                <h3>🚀 HIZLI İNDİRME</h3>
                <p>Bekleme yok. Reklam yok. Orijinal formatınızda (Hata olursa WAV)</p>
                <h2>$10.00</h2>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("💳 HEMEN SATIN AL & İNDİR", ODEME_LINKI, use_container_width=True)

        # --- BEDAVA (GİZLİ SAYAÇLI) ---
        with tab2:
            download_data = get_download_data(st.session_state.output_path, st.session_state.file_ext)
            final_filename = f"FKRed_Master.{st.session_state.file_ext}"
            final_mime = get_mime_type(st.session_state.file_ext)
            
            st.markdown("""
            <div class='free-box'>
                <h3>📺 SPONSOR DESTEĞİ</h3>
                <p>İndirme butonu videoyu izledikten sonra açılır.</p>
            </div>
            """, unsafe_allow_html=True)

            st.video(REKLAM_LINKI)
            
            # 1. Kilidi Aç
            if not st.session_state.download_ready:
                if st.button("⏱️ Süreyi Başlat (Video Oynuyor...)", use_container_width=True):
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(10, 0, -1):
                        status_text.warning(f"⏳ Kontrol ediliyor... {i} saniye")
                        progress_bar.progress((10 - i) * 10)
                        time.sleep(1)
                    
                    status_text.success("🔓 Onaylandı!")
                    st.session_state.download_ready = True
                    st.rerun()

            # 2. İndirme Butonu
            if st.session_state.download_ready and download_data:
                st.success(f"✅ Dosyanız hazır ({final_filename}).")
                st.download_button(
                    label=f"⬇️ {st.session_state.file_ext.upper()} OLARAK İNDİR",
                    data=download_data,
                    file_name=final_filename,
                    mime=final_mime,
                    use_container_width=True
                )
