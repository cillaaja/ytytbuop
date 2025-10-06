import sys
import subprocess
import threading
import os
import time
import shutil
import streamlit.components.v1 as components

# Pastikan Streamlit terpasang
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st


# ======================== #
#  🔹 Fungsi FFmpeg Stream #
# ======================== #
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""

    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv"
    ]
    if scale:
        cmd += scale.split()
    cmd.append(output_url)

    log_callback(f"Menjalankan: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("⚠️ Streaming selesai atau dihentikan.")


# ====================== #
#  🔹 Fungsi Utama App  #
# ====================== #
def main():
    st.set_page_config(page_title="Streaming YouTube Live", page_icon="🎥", layout="wide")

    # Naikkan limit upload ke 16000 MB (16 GB)
    st.config.set_option("server.maxUploadSize", 16000)

    st.title("🎥 Live Streaming ke YouTube")

    # Folder upload video
    upload_dir = "uploaded_videos"
    os.makedirs(upload_dir, exist_ok=True)

    # Bersihkan file lebih dari 1 hari
    now = time.time()
    for f in os.listdir(upload_dir):
        fp = os.path.join(upload_dir, f)
        if os.path.isfile(fp) and now - os.path.getmtime(fp) > 86400:
            os.remove(fp)

    # Iklan opsional
    if st.checkbox("Tampilkan Iklan", value=True):
        st.subheader("Iklan Sponsor")
        components.html("""
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript' src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
                <p style="color:#888">Iklan akan muncul di sini</p>
            </div>
        """, height=300)

    # Pilih video
    local_videos = [f for f in os.listdir(upload_dir) if f.endswith(('.mp4', '.flv'))]
    selected_video = st.selectbox("Pilih video yang tersedia:", local_videos) if local_videos else None

    uploaded_file = st.file_uploader(
        "Atau upload video baru (mp4/flv - codec H264/AAC)",
        type=['mp4', 'flv']
    )

    video_path = None
    if uploaded_file:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)
        st.success(f"✅ Video '{uploaded_file.name}' berhasil diupload!")
        video_path = file_path
    elif selected_video:
        video_path = os.path.join(upload_dir, selected_video)

    stream_key = st.text_input("Masukkan YouTube Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        log_placeholder.text("\n".join(logs[-25:]))

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    # Jalankan streaming
    if st.button("▶️ Jalankan Streaming"):
        if not video_path or not stream_key:
            st.error("❌ Harap pilih video dan isi Stream Key!")
        else:
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg, args=(video_path, stream_key, is_shorts, log_callback), daemon=True
            )
            st.session_state['ffmpeg_thread'].start()
            st.success("✅ Streaming dimulai ke YouTube!")

    # Stop streaming
    if st.button("⏹️ Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("⚠️ Streaming dihentikan secara manual.")
        log_callback("Streaming dihentikan oleh pengguna.")

    log_placeholder.text("\n".join(logs[-25:]))


if __name__ == "__main__":
    main()
