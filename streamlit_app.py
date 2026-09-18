"""
streamlit_app.py — Bodhan Hindi ASR front-end
Deploy to Streamlit Cloud.
Set ASR_SERVER_URL in st.secrets (the Cloudflare tunnel URL).
"""

import io
import httpx
import streamlit as st

st.set_page_config(
    page_title="Bodhan Hindi ASR",
    page_icon="🎙️",
    layout="centered",
)

# ── Config ────────────────────────────────────────────────────────────────────
ASR_URL = st.secrets.get("ASR_SERVER_URL", "http://localhost:8765").rstrip("/")

# ── Helpers ───────────────────────────────────────────────────────────────────
def send_to_server(audio_bytes: bytes, filename: str) -> dict:
    with httpx.Client(timeout=180) as client:
        resp = client.post(
            f"{ASR_URL}/transcribe",
            files={"file": (filename, audio_bytes, "audio/wav")},
        )
        resp.raise_for_status()
        return resp.json()

def show_results(result: dict):
    duration = result.get("audio_duration_seconds", 0)
    rtt = result.get("rtt_seconds", 0)
    rtf = rtt / max(duration, 0.01)

    c1, c2, c3 = st.columns(3)
    c1.metric("Audio length", f"{duration:.1f}s")
    c2.metric("Processing time", f"{rtt:.2f}s")
    c3.metric("RTF", f"{rtf:.2f}x")

    st.subheader("Hindi transcript")
    hindi = result.get("hindi_text", "N/A")
    st.text_area("hindi_out", hindi, height=120, label_visibility="collapsed")

    st.subheader("English translation")
    english = result.get("english_translation", "N/A")
    st.text_area("english_out", english, height=120, label_visibility="collapsed")

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🎙️ Bodhan Hindi ASR")
st.caption("Upload or record Hindi audio → Hindi transcript + English translation")

tab_upload, tab_record = st.tabs(["📁 Upload audio", "🎤 Record"])

# Upload tab
with tab_upload:
    uploaded = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
    )
    if uploaded:
        st.audio(uploaded)
        if st.button("Transcribe", key="btn_upload"):
            with st.spinner("Sending to ASR server…"):
                try:
                    result = send_to_server(uploaded.read(), uploaded.name)
                    show_results(result)
                except httpx.HTTPStatusError as e:
                    st.error(f"Server error {e.response.status_code}: {e.response.text}")
                except httpx.ConnectError:
                    st.error(f"Could not connect to server at {ASR_URL}. Is the tunnel running?")
                except Exception as e:
                    st.error(f"Error: {e}")

# Record tab
with tab_record:
    st.info("Click **Start recording**, speak, then **Stop** and hit **Transcribe**.")
    audio_data = st.audio_input("Record audio", key="recorder")
    if audio_data:
        st.audio(audio_data)
        if st.button("Transcribe", key="btn_record"):
            with st.spinner("Sending to ASR server…"):
                try:
                    result = send_to_server(audio_data.read(), "recording.wav")
                    show_results(result)
                except httpx.HTTPStatusError as e:
                    st.error(f"Server error {e.response.status_code}: {e.response.text}")
                except httpx.ConnectError:
                    st.error(f"Could not connect to server at {ASR_URL}. Is the tunnel running?")
                except Exception as e:
                    st.error(f"Error: {e}")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
**ASR**: [bodhan-ai/indic-transcribe-flex](https://huggingface.co/bodhan-ai/indic-transcribe-flex)
1.2B FastConformer · 27 Indian languages

**Translation**: [bodhan-ai/indic-translate](https://huggingface.co/bodhan-ai/indic-translate)
7.94B Gemma 4 E4B · 22 Indian languages ↔ English

**Server**: O-Health DGX Spark (GB10 Grace-Blackwell)
    """)
    st.divider()
    st.caption(f"Server: `{ASR_URL}`")
    if st.button("🔍 Health check"):
        try:
            r = httpx.get(f"{ASR_URL}/health", timeout=10)
            st.success(r.json())
        except Exception as e:
            st.error(str(e))
