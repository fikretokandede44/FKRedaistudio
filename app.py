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

# --- ÖZEL CSS TASARIMI (ATEŞ VE KIZIL ODAK) ---
st.markdown("""
<style>
    /* Global App Background */
    .stApp {
        background-image: linear-gradient(to bottom, #0F0F0F, #161616);
        color: #E0E0E0;
    }
    
    /* Ana Başlık Stili - Alev Geçişi */
    h1 {
        text-align: center;
        background: -webkit-linear-gradient(90deg, #FF3333, #FF9933);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem !important; 
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255, 51, 51, 0.5);
        margin-bottom: 0px; 
    }
    
    /* MFN Production Alt Başlığı */
    .mfn-production {
        text-align: center;
        background: -webkit-linear-gradient(90deg, #FF3333, #FF9933);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 5px;
    }

    /* Streamlit Alt Başlığı */
    .subtitle {
        text-align: center;
        color: #FFC0C0;
        font-size: 1.3rem;
        margin-bottom: 40px;
        margin-top: 15px;
    }

    /* Ana Çalışma Butonu (Launch Button) */
    .stButton>button {
        background: linear-gradient(90deg, #FF0000 0%, #CC0000 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(255, 0, 0, 0.5); 
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 25px rgba(255, 0, 0, 0.8);
    }
    
    /* İndirme Kilit Kutusu */
    .free-box {
        background-color: #262626; 
        border: 1px solid #FF4B4B; 
        color: white; 
        padding: 20px; 
        border-radius: 15px;
    }

    /* Alt Bilgi (Footer) */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0F0F0F;
        color: #555;
        text-align: right;
        padding: 5px 15px;
        font-size: 0.8rem;
        z-index: 100;
        border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

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
            samplerate = f.samplerate

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
                Chorus(rate_hz=0.8, depth=0.015, wet_level=0.15), 
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
        with AudioFile(output_path, 'w', samplerate, effected_audio.shape[0]) as f:
            f.write(effected_audio)

        # HAFIZAYA KAYDET
        st.session_state.processed = True
        st.session_state.output_path = output_path 
        st.session_state.download_ready = False
        
        progress.progress(100)
        status.success("✅ İşlem Tamamlandı!")
        time.sleep(1)
        progress.empty()
        status.empty()

    except Exception as e:
        status.error(f"Hata: {e}")

# --- BAŞLIKLAR ---
st.markdown("<h1>🔥 FKRed AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='mfn-production'>MFN Production</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>İçerik Üreticileri İçin Akıllı Ses Stüdyosu</p>", unsafe_allow_html=True)


# --- ARAYÜZ ---
col1, col2 = st.columns([1, 1], gap="large")

# GİRİŞ ALANI
with col1:
    st.markdown("### 📤 Dosya Yükleme")
    uploaded_file = st.file_uploader("Dosya Seçin", type=["wav", "mp3", "mp4", "mov", "m4a"], label_visibility="collapsed")

    st.markdown("### 🎛️ Mod Seçimi")
    processing_mode = st.radio("Sesin modu ne olsun?", ("🎤 VLOG & KONUŞMA (Temiz & Net)", "🎸 MÜZİK & AKUSTİK (Sıcak & Doğal)", "🎙️ PODCAST (Tok & Radyo)"))

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 SİHRİ BAŞLAT", use_container_width=True):
        process_audio_logic()

# SONUÇ VE İNDİRME ALANI
with col2:
    if st.session_state.processed:
        st.markdown("### 🎁 Sonuç Hazır - Farkı Gör!")
        
        # --- A/B KARŞILAŞTIRMA ---
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.markdown("<p class='comparison-title'>🔴 Ham Kayıt</p>", unsafe_allow_html=True)
            if 'video' in st.session_state.original_mime:
                st.video(st.session_state.original_data, format=st.session_state.original_mime)
            else:
                st.audio(st.session_state.original_data, format=st.session_state.original_mime)

        with comp_col2:
            st.markdown("<p class='comparison-title'>🟢 FKRed İşlemi</p>", unsafe_allow_html=True)
            st.audio(st.session_state.output_path, format="audio/wav")

        st.markdown("---")
        
        # --- MONETİZASYON BÖLÜMÜ ---
        tab1 = st.tabs(["🆓 İNDİRME GÖREVİ"])
        
        with tab1[0]:
            st.markdown("""
            <div class='free-box'>
                <h3>📺 ÜCRETSİZ İNDİRME GÖREVİ</h3>
                <p>İndirme butonunun açılması için aşağıdaki videonun süresi dolana kadar bekleyin.</p>
            </div>
            """, unsafe_allow_html=True)

            st.video(REKLAM_LINKI)
            
            # Geri Sayım ve Kilit
            if not st.session_state.download_ready:
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 10 saniye bekle
                for i in range(10, 0, -1):
                    status_text.warning(f"⏳ Lütfen bekleyin... İndirme {i} saniye sonra açılacak.")
                    progress_bar.progress((10 - i) * 10)
                    time.sleep(1)
                
                status_text.success("🔓 Kilit Açıldı!")
                st.session_state.download_ready = True
                st.rerun() # Sayfayı yenile ve butonu göster

            # İndirme Butonu (Süre bittiyse görünür)
            if st.session_state.download_ready:
                free_data = convert_wav_to_target_format(st.session_state.output_path, st.session_state.file_ext)
                free_filename = f"FKRed_Master.{st.session_state.file_ext}"
                free_mime = get_mime_type(st.session_state.file_ext)
                
                st.success("✅ Dosyanız hazır.")
                st.download_button(
                    label=f"⬇️ {st.session_state.file_ext.upper()} OLARAK İNDİR",
                    data=free_data,
                    file_name=free_filename,
                    mime=free_mime,
                    use_container_width=True
                )

# --- SAYFANIN EN ALTINA KALICI FOOTER (Fikret Okan Dede İmzası) ---
st.markdown("""
<div class="footer">
    © 2025 FKRed AI Studio | Geliştirici: Fikret Okan Dede
</div>
""", unsafe_allow_html=True)
