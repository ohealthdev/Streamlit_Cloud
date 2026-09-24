import streamlit as st
import requests
import json

# ─── Config ──────────────────────────────────────────────────────────────────
LANGUAGE_ENDPOINTS = {
    "Hindi":   "http://49.200.100.22:5009/convertSpeechToText",
    "English": "http://49.200.100.22:5003/convertSpeechToText",
    "Telugu":  "http://49.200.100.22:5012/convertSpeechToText",
    "Marathi": "http://49.200.100.22:5013/convertSpeechToText",
    "Kannada": "http://49.200.100.22:5015/convertSpeechToText",
    "Dogri":   "http://49.200.100.22:5014/convertSpeechToText",
}

# Keys that may appear in the result depending on language
NATIVE_TEXT_KEYS = [
    "corrected_hindi", "corrected_kannada", "corrected_english",
    "corrected_telugu", "corrected_marathi", "corrected_dogri",
    "raw_transcription",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_native_text(result: dict) -> str | None:
    """Return the best native-language transcription field from a result dict."""
    for key in NATIVE_TEXT_KEYS:
        if result.get(key):
            return result[key], key
    return None, None


def call_asr(filename: str, language: str) -> dict:
    url = LANGUAGE_ENDPOINTS[language]
    payload = {"audioFileName": filename.strip()}
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (>120 s)"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    except Exception as e:
        return {"error": str(e)}


def copy_button(label: str, text: str, key: str):
    """Render a text-area + copy-to-clipboard button pair."""
    st.text_area(label, value=text, height=120, key=f"ta_{key}")
    st.button(
        f"📋 Copy {label}",
        key=f"btn_{key}",
        on_click=lambda: st.session_state.update({f"copied_{key}": True}),
    )
    # JS clipboard trick via st.components
    if st.session_state.get(f"copied_{key}"):
        st.components.v1.html(
            f"""
            <script>
              navigator.clipboard.writeText({json.dumps(text)})
                .then(() => console.log('copied'))
                .catch(err => console.error(err));
            </script>
            """,
            height=0,
        )
        st.toast(f"✅ {label} copied!", icon="📋")
        st.session_state[f"copied_{key}"] = False


# ─── Page setup ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASR Transcription",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Speech-to-Text Transcription")
st.caption("Paste audio filenames, pick a language, and transcribe.")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    language = st.selectbox(
        "Language",
        options=list(LANGUAGE_ENDPOINTS.keys()),
        index=0,
        help="All files in this batch will be transcribed using the selected language model.",
    )

    raw_input = st.text_area(
        "Audio filenames",
        placeholder="1790231110373-290388.wav, 1790231116476-177747.wav",
        height=120,
        help="Comma-separated list of filenames (no path needed).",
    )

    run = st.button("🚀 Transcribe", use_container_width=True, type="primary")

# ─── State ───────────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = {}          # filename → api response dict
if "file_list" not in st.session_state:
    st.session_state.file_list = []

# ─── Run transcription ───────────────────────────────────────────────────────
if run:
    if not raw_input.strip():
        st.sidebar.error("Please enter at least one filename.")
    else:
        filenames = [f.strip() for f in raw_input.split(",") if f.strip()]
        st.session_state.file_list = filenames
        st.session_state.results = {}

        progress = st.sidebar.progress(0, text="Transcribing…")
        for i, fname in enumerate(filenames):
            with st.spinner(f"Processing **{fname}** …"):
                st.session_state.results[fname] = call_asr(fname, language)
            progress.progress((i + 1) / len(filenames), text=f"{i+1}/{len(filenames)} done")
        progress.empty()
        st.sidebar.success(f"Done — {len(filenames)} file(s) processed.")

# ─── Display results ─────────────────────────────────────────────────────────
if st.session_state.file_list:
    tabs = st.tabs([f"📄 {fn}" for fn in st.session_state.file_list])

    for tab, fname in zip(tabs, st.session_state.file_list):
        with tab:
            data = st.session_state.results.get(fname)

            if data is None:
                st.info("Not yet transcribed.")
                continue

            # ── Error ──
            if "error" in data:
                st.error(f"❌ API error: {data['error']}")
                continue

            # ── Metadata strip ──
            results_list = data.get("results", [])
            if not results_list:
                st.warning("API returned no results.")
                with st.expander("Raw API response"):
                    st.json(data)
                continue

            result = results_list[0]  # one file per call

            col1, col2, col3 = st.columns(3)
            col1.metric("Status", result.get("status", "—").upper())
            col2.metric("Duration", f"{result.get('audio_duration_seconds', 0):.2f} s")
            col3.metric("File", result.get("file", fname))

            st.divider()

            # ── Native-language transcription ──
            native, native_key = get_native_text(result)
            english = result.get("english_translation") or data.get("transcription")

            left, right = st.columns(2)

            with left:
                label = native_key.replace("_", " ").title() if native_key else "Native Transcription"
                if native:
                    st.subheader(f"🗣️ {label}")
                    st.text_area(
                        label,
                        value=native,
                        height=200,
                        key=f"native_ta_{fname}",
                        label_visibility="collapsed",
                    )
                    if st.button(f"📋 Copy", key=f"copy_native_{fname}"):
                        st.components.v1.html(
                            f"<script>navigator.clipboard.writeText({json.dumps(native)})</script>",
                            height=0,
                        )
                        st.toast("✅ Native text copied!")
                else:
                    st.info("No native-language transcription in response.")

            with right:
                if english:
                    st.subheader("🌐 English Translation")
                    st.text_area(
                        "English Translation",
                        value=english,
                        height=200,
                        key=f"eng_ta_{fname}",
                        label_visibility="collapsed",
                    )
                    if st.button(f"📋 Copy", key=f"copy_eng_{fname}"):
                        st.components.v1.html(
                            f"<script>navigator.clipboard.writeText({json.dumps(english)})</script>",
                            height=0,
                        )
                        st.toast("✅ English translation copied!")
                else:
                    st.info("No English translation in response.")

            # ── Raw JSON toggle ──
            with st.expander("🔍 Raw API response"):
                st.json(data)

else:
    st.info("👈 Enter filenames in the sidebar and click **Transcribe** to begin.")
