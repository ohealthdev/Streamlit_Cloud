import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL = "https://prod.o-health.in/api/v2"
AUTH = {"user_name": "s.h", "password": "2580"}

REPORT_FIELDS = [
    "specialist",
    "symptom_duration",
    "symptoms",
    "initial_symptom",
    "past_history",
    "symptoms_SLM",
    "past_history_SLM",
]

st.set_page_config(
    page_title="O-Health API Automator",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #1c2333;
    --border: #30363d;
    --accent: #2ea4ff;
    --accent2: #3dd68c;
    --warn: #f0883e;
    --danger: #f85149;
    --text: #e6edf3;
    --text2: #8b949e;
    --text3: #6e7681;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.stApp { background-color: var(--bg); }

/* ── Header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 0 28px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.app-header .logo {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.app-header h1 {
    margin: 0; font-size: 1.4rem; font-weight: 600; color: var(--text);
    letter-spacing: -0.02em;
}
.app-header p { margin: 0; font-size: 0.8rem; color: var(--text2); }

/* ── Section labels ── */
.section-label {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--text3);
    margin-bottom: 8px;
}

/* ── Step chip ── */
.step-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 6px 14px;
    font-size: 0.78rem; color: var(--text2); margin-bottom: 12px;
}
.step-chip .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent2);
}
.step-chip.running .dot { background: var(--warn); animation: pulse 1s infinite; }
.step-chip.done .dot { background: var(--accent2); }
.step-chip.error .dot { background: var(--danger); }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

/* ── Field card ── */
.field-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.field-card .field-name {
    font-size: 0.72rem; font-weight: 600; color: var(--accent);
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;
}
.field-card .field-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: var(--text);
    line-height: 1.5;
}

/* ── Conversation turn ── */
.conv-turn {
    display: flex; gap: 10px; margin-bottom: 14px;
    align-items: flex-start;
}
.conv-turn .avatar {
    min-width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700;
    flex-shrink: 0;
}
.conv-turn.patient .avatar { background: #21262d; color: var(--text2); }
.conv-turn.ai .avatar { background: linear-gradient(135deg,var(--accent),var(--accent2)); color: #fff; }
.conv-turn .bubble {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 10px 14px;
    font-size: 0.83rem; line-height: 1.5; color: var(--text); flex: 1;
}
.conv-turn.ai .bubble { border-color: #1d3a5f; background: #0d1f33; }
.conv-turn .cat-badge {
    font-size: 0.68rem; color: var(--text3); margin-bottom: 4px;
    font-weight: 500;
}

/* ── Diff table ── */
.diff-match { color: var(--accent2); }
.diff-change { color: var(--warn); font-weight: 600; }

/* ── Progress log ── */
.log-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem; color: var(--text2);
    padding: 3px 0;
    border-bottom: 1px solid #1c1c1c;
}
.log-line.ok { color: var(--accent2); }
.log-line.err { color: var(--danger); }
.log-line.info { color: var(--accent); }

/* ── JSON viewer ── */
.json-block {
    background: #0a0e13;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #adbac7;
    overflow-x: auto;
    line-height: 1.6;
    max-height: 420px;
    overflow-y: auto;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown { color: var(--text2); }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1a6faa, #0d5490) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.01em !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Input ── */
.stNumberInput input, .stTextInput input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 6px 6px 0 0 !important;
    color: var(--text2) !important;
    font-size: 0.82rem !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* expanders */
details { border: 1px solid var(--border) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fetch_report(assessment_id: int) -> dict:
    payload = {"assessment_id": assessment_id, **AUTH}
    r = requests.post(
        f"{BASE_URL}/temp/admin/getCompleteReportDirect",
        json=payload, timeout=30
    )
    r.raise_for_status()
    return r.json()


def start_primary_conversation(transcription: str) -> dict:
    r = requests.post(
        f"{BASE_URL}/assessment/primaryConversationWrapper",
        json={"transcription": transcription}, timeout=30
    )
    r.raise_for_status()
    return r.json()


def send_followup(assessment_id: int, transcription: str) -> dict:
    r = requests.post(
        f"{BASE_URL}/assessment/followupConversationWrapper",
        json={"assessment_id": assessment_id, "transcription": transcription},
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def extract_fields(report: dict) -> dict:
    fr = report.get("final_report", report)
    return {f: fr.get(f) for f in REPORT_FIELDS}


def is_session_end(response: dict) -> bool:
    return "token_number" in response or "doctor_name" in response


# ─────────────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def field_card(name: str, value):
    if value is None:
        disp = "<span style='color:#6e7681'>—</span>"
    elif isinstance(value, (dict, list)):
        disp = f"<pre style='margin:0'>{json.dumps(value, indent=2)}</pre>"
    else:
        disp = str(value)
    st.markdown(f"""
    <div class="field-card">
        <div class="field-name">{name}</div>
        <div class="field-val">{disp}</div>
    </div>
    """, unsafe_allow_html=True)


def render_old_fields(fields: dict, label="OLD REPORT FIELDS"):
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    for k, v in fields.items():
        field_card(k, v)


def render_conversation(conv_history: list):
    if not conv_history:
        st.info("No conversation history available.")
        return
    for i, turn in enumerate(conv_history):
        if "user" in turn:
            st.markdown(f"""
            <div class="conv-turn patient">
                <div class="avatar">P</div>
                <div class="bubble">
                    <div class="cat-badge">Initial complaint</div>
                    {turn['user']}
                </div>
            </div>""", unsafe_allow_html=True)
        elif "followup_question_en" in turn:
            st.markdown(f"""
            <div class="conv-turn ai">
                <div class="avatar">AI</div>
                <div class="bubble">
                    <div class="cat-badge">{turn.get('category','')}</div>
                    <strong>{turn['followup_question_en']}</strong>
                </div>
            </div>""", unsafe_allow_html=True)
            if turn.get("response"):
                st.markdown(f"""
                <div class="conv-turn patient">
                    <div class="avatar">P</div>
                    <div class="bubble">{turn['response']}</div>
                </div>""", unsafe_allow_html=True)


def render_json_block(data: dict):
    pretty = json.dumps(data, indent=2)
    st.markdown(f'<div class="json-block"><pre style="margin:0">{pretty}</pre></div>',
                unsafe_allow_html=True)


def compare_fields(old: dict, new: dict):
    rows = []
    for k in REPORT_FIELDS:
        ov = old.get(k)
        nv = new.get(k)
        changed = ov != nv
        rows.append({"Field": k,
                     "Old Value": json.dumps(ov) if isinstance(ov,(dict,list)) else str(ov),
                     "New Value": json.dumps(nv) if isinstance(nv,(dict,list)) else str(nv),
                     "Changed": "✅ Same" if not changed else "🔄 Changed"})
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "step": 0,
        "logs": [],
        "old_report": None,
        "old_fields": None,
        "new_report": None,
        "new_fields": None,
        "conv_history": [],
        "new_assessment_id": None,
        "replay_turns": [],
        "session_end_response": None,
        "running": False,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────────────────────
# LOG HELPER
# ─────────────────────────────────────────────────────────────────────────────

def log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({"ts": ts, "msg": msg, "level": level})


# ─────────────────────────────────────────────────────────────────────────────
# AUTOMATION CORE
# ─────────────────────────────────────────────────────────────────────────────

def run_automation(assessment_id: int, log_placeholder, status_placeholder):

    def update_status(msg, level="info"):
        log(msg, level)
        with log_placeholder:
            render_live_log()

    def render_live_log():
        lines = "".join(
            f'<div class="log-line {e["level"]}">[{e["ts"]}] {e["msg"]}</div>'
            for e in st.session_state.logs[-30:]
        )
        st.markdown(f'<div style="max-height:280px;overflow-y:auto;background:#0a0e13;border:1px solid #30363d;border-radius:8px;padding:12px">{lines}</div>',
                    unsafe_allow_html=True)

    try:
        # ── STEP 1: Fetch old report ──────────────────────────────────────
        update_status(f"📥 Fetching report for assessment_id={assessment_id}...")
        old_report = fetch_report(assessment_id)
        st.session_state.old_report = old_report
        st.session_state.old_fields = extract_fields(old_report)
        fr = old_report.get("final_report", old_report)
        conv_history = fr.get("conversation_history", [])
        st.session_state.conv_history = conv_history
        update_status(f"✅ Report fetched. {len(conv_history)} conversation turns found.", "ok")
        st.session_state.step = 1

        # ── STEP 2: Extract first user message ───────────────────────────
        first_msg = None
        for turn in conv_history:
            if "user" in turn and turn["user"]:
                first_msg = turn["user"]
                break

        if not first_msg:
            update_status("❌ No initial user message found in conversation history.", "err")
            st.session_state.error = "No initial user message found."
            return

        update_status(f"💬 Initial complaint: \"{first_msg[:80]}...\"")

        # ── STEP 3: Primary conversation ─────────────────────────────────
        update_status("🚀 Starting new assessment via primaryConversationWrapper...")
        primary_resp = start_primary_conversation(first_msg)
        new_aid = primary_resp.get("assessment_id")
        st.session_state.new_assessment_id = new_aid
        update_status(f"✅ New assessment created: ID={new_aid}", "ok")
        st.session_state.step = 2

        # Build response list from conv_history (index-matched)
        # responses[i] = answer to followup question at index i
        followup_turns = [t for t in conv_history if "followup_question_en" in t]
        responses = [t.get("response", "") or "" for t in followup_turns]

        # ── STEP 4: Replay followup conversation ─────────────────────────
        replay_turns = []
        current_question = primary_resp.get("result", primary_resp)
        turn_idx = 0
        max_turns = max(len(responses) + 2, 15)

        update_status(f"🔄 Replaying {len(responses)} followup responses...")

        while turn_idx < max_turns:
            # Get the question text
            if isinstance(current_question, dict):
                q_en = current_question.get("en", "")
                q_cat = current_question.get("category", "")
            else:
                q_en = str(current_question)
                q_cat = ""

            # Pick answer
            if turn_idx < len(responses) and responses[turn_idx]:
                answer = responses[turn_idx]
            elif turn_idx < len(responses):
                answer = responses[turn_idx] if responses[turn_idx] else "no"
            else:
                answer = "no further symptoms"

            update_status(f"  [{turn_idx+1}] Q: \"{q_en[:60]}\" → A: \"{answer[:50]}\"")

            replay_turns.append({
                "turn": turn_idx + 1,
                "question_category": q_cat,
                "question_en": q_en,
                "answer_sent": answer,
            })

            # Send followup
            try:
                followup_resp = send_followup(new_aid, answer)
            except Exception as e:
                update_status(f"❌ Followup API error: {e}", "err")
                break

            # Check if session ended
            if is_session_end(followup_resp):
                update_status("🏁 Session ended by server.", "ok")
                st.session_state.session_end_response = followup_resp
                replay_turns[-1]["session_end"] = True
                break

            current_question = followup_resp
            turn_idx += 1
            time.sleep(0.3)  # polite rate limiting

        st.session_state.replay_turns = replay_turns
        st.session_state.step = 3

        # ── STEP 5: Fetch new report ──────────────────────────────────────
        update_status(f"📥 Fetching new report for assessment_id={new_aid}...")
        time.sleep(1)
        new_report = fetch_report(new_aid)
        st.session_state.new_report = new_report
        st.session_state.new_fields = extract_fields(new_report)
        update_status("✅ New report fetched successfully.", "ok")
        st.session_state.step = 4

        update_status("🎉 Automation complete!", "ok")
        st.session_state.running = False

    except requests.exceptions.HTTPError as e:
        err = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        update_status(f"❌ {err}", "err")
        st.session_state.error = err
        st.session_state.running = False
    except Exception as e:
        update_status(f"❌ Unexpected error: {e}", "err")
        st.session_state.error = str(e)
        st.session_state.running = False


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px 0;">
        <div style="font-size:1.1rem;font-weight:700;color:#e6edf3;letter-spacing:-0.02em;">🩺 O-Health</div>
        <div style="font-size:0.72rem;color:#6e7681;margin-top:2px;">API Automation Suite</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Assessment Input</div>', unsafe_allow_html=True)

    assessment_id_input = st.number_input(
        "Assessment ID",
        min_value=1,
        value=41023,
        step=1,
        help="Enter the assessment ID to fetch and replay"
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    run_btn = st.button("▶ Run Automation", use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-label">Pipeline Steps</div>', unsafe_allow_html=True)

    steps = [
        ("1", "Fetch Original Report"),
        ("2", "Start New Assessment"),
        ("3", "Replay Conversation"),
        ("4", "Fetch New Report"),
    ]
    step_colors = {
        0: "#6e7681",
        1: "#2ea4ff",
        2: "#2ea4ff",
        3: "#2ea4ff",
        4: "#3dd68c",
    }
    completed = st.session_state.step
    for num, label in steps:
        n = int(num)
        color = "#3dd68c" if completed >= n else ("#f0883e" if st.session_state.running and completed == n-1 else "#6e7681")
        icon = "✓" if completed >= n else ("⟳" if st.session_state.running and completed == n-1 else "○")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #1c2333;">
            <span style="color:{color};font-size:0.9rem;font-weight:700">{icon}</span>
            <span style="font-size:0.8rem;color:{'#e6edf3' if completed>=n else '#6e7681'}">{label}</span>
        </div>""", unsafe_allow_html=True)

    if st.session_state.new_assessment_id:
        st.markdown(f"""
        <div style="margin-top:16px;padding:10px;background:#0d1f33;border:1px solid #1d3a5f;border-radius:8px">
            <div style="font-size:0.7rem;color:#2ea4ff;font-weight:600;margin-bottom:4px">NEW ASSESSMENT ID</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;color:#e6edf3;font-weight:700">{st.session_state.new_assessment_id}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Reset", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <div class="logo">🩺</div>
    <div>
        <h1>O-Health API Automator</h1>
        <p>Automate clinical assessment replay &amp; report comparison</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RUN TRIGGER
# ─────────────────────────────────────────────────────────────────────────────

if run_btn:
    # Reset previous run
    st.session_state.step = 0
    st.session_state.logs = []
    st.session_state.old_report = None
    st.session_state.old_fields = None
    st.session_state.new_report = None
    st.session_state.new_fields = None
    st.session_state.conv_history = []
    st.session_state.new_assessment_id = None
    st.session_state.replay_turns = []
    st.session_state.session_end_response = None
    st.session_state.running = True
    st.session_state.error = None

    log_ph = st.empty()
    status_ph = st.empty()
    run_automation(int(assessment_id_input), log_ph, status_ph)
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ERROR BANNER
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.error:
    st.markdown(f"""
    <div style="background:#1a0a0a;border:1px solid #f85149;border-radius:8px;padding:14px 18px;margin-bottom:16px;color:#f85149">
        ❌ <strong>Error:</strong> {st.session_state.error}
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LIVE LOG (while running)
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.logs and st.session_state.step < 4:
    with st.expander("📋 Execution Log", expanded=True):
        lines = "".join(
            f'<div class="log-line {e["level"]}">[{e["ts"]}] {e["msg"]}</div>'
            for e in st.session_state.logs
        )
        st.markdown(
            f'<div style="max-height:260px;overflow-y:auto;'
            f'background:#0a0e13;border-radius:6px;padding:12px">{lines}</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS (only when we have data)
# ─────────────────────────────────────────────────────────────────────────────

if not st.session_state.old_report:
    # Splash
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#6e7681">
        <div style="font-size:3rem;margin-bottom:16px">🩺</div>
        <div style="font-size:1.1rem;font-weight:600;color:#8b949e;margin-bottom:8px">Enter an Assessment ID and run the automation</div>
        <div style="font-size:0.85rem">The tool will fetch the original report, replay the conversation, and compare results.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# TWO-COLUMN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([1, 2], gap="large")


# ─────────────────────────────────────────────────────────────────────────────
# LEFT COLUMN — Old Fields
# ─────────────────────────────────────────────────────────────────────────────

with left_col:
    st.markdown("""
    <div style="background:#0d1f33;border:1px solid #1d3a5f;border-radius:10px;
                padding:6px 14px;display:inline-block;margin-bottom:16px">
        <span style="font-size:0.75rem;font-weight:600;color:#2ea4ff">OLD FIELDS</span>
        <span style="font-size:0.7rem;color:#6e7681;margin-left:6px">from original report</span>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for old fields
    tab_spec, tab_syms, tab_dur, tab_hist, tab_slm = st.tabs([
        "🏥 Specialist", "💊 Symptoms", "⏱ Duration", "📋 History", "🔬 SLM"
    ])

    old = st.session_state.old_fields or {}

    with tab_spec:
        field_card("specialist", old.get("specialist"))

    with tab_syms:
        field_card("symptoms", old.get("symptoms"))
        field_card("initial_symptom", old.get("initial_symptom"))

    with tab_dur:
        field_card("symptom_duration", old.get("symptom_duration"))

    with tab_hist:
        field_card("past_history", old.get("past_history"))

    with tab_slm:
        field_card("symptoms_SLM", old.get("symptoms_SLM"))
        field_card("past_history_SLM", old.get("past_history_SLM"))


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT COLUMN — All Tabs
# ─────────────────────────────────────────────────────────────────────────────

with right_col:
    main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs([
        "💬 Conversation", "🔄 Replay Log", "📊 Comparison",
        "📄 Old JSON", "📄 New JSON"
    ])

    # ── Tab 1: Original Conversation ──────────────────────────────────────
    with main_tab1:
        st.markdown('<div class="section-label">Original Conversation History</div>',
                    unsafe_allow_html=True)
        render_conversation(st.session_state.conv_history)

    # ── Tab 2: Replay Log ────────────────────────────────────────────────
    with main_tab2:
        st.markdown('<div class="section-label">Replayed Conversation Turns</div>',
                    unsafe_allow_html=True)

        if st.session_state.replay_turns:
            for turn in st.session_state.replay_turns:
                ended = turn.get("session_end", False)
                st.markdown(f"""
                <div style="background:var(--surface);border:1px solid {'#1a3a1a' if ended else '#30363d'};
                            border-radius:10px;padding:12px 16px;margin-bottom:10px">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                        <span style="font-size:0.7rem;font-weight:700;color:#6e7681">TURN {turn['turn']}</span>
                        <span style="font-size:0.7rem;color:#2ea4ff">{turn['question_category']}</span>
                        {'<span style="font-size:0.7rem;color:#3dd68c;margin-left:auto">SESSION END</span>' if ended else ''}
                    </div>
                    <div style="font-size:0.82rem;color:#8b949e;margin-bottom:6px">❓ {turn['question_en']}</div>
                    <div style="font-size:0.82rem;color:#e6edf3">💬 {turn['answer_sent']}</div>
                </div>""", unsafe_allow_html=True)

            if st.session_state.session_end_response:
                ser = st.session_state.session_end_response
                st.markdown(f"""
                <div style="background:#0d1f0d;border:1px solid #2ea44f;border-radius:10px;padding:16px;margin-top:8px">
                    <div style="font-size:0.75rem;font-weight:600;color:#3dd68c;margin-bottom:10px">🏁 SESSION SUMMARY</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                        <div>
                            <div style="font-size:0.7rem;color:#6e7681">Doctor</div>
                            <div style="font-size:0.85rem;color:#e6edf3">{ser.get('doctor_name','—')}</div>
                        </div>
                        <div>
                            <div style="font-size:0.7rem;color:#6e7681">Department</div>
                            <div style="font-size:0.85rem;color:#e6edf3">{ser.get('doctor_department','—')}</div>
                        </div>
                        <div>
                            <div style="font-size:0.7rem;color:#6e7681">Recommended Specialist</div>
                            <div style="font-size:0.85rem;color:#3dd68c">{ser.get('specialist_recommended','—')}</div>
                        </div>
                        <div>
                            <div style="font-size:0.7rem;color:#6e7681">Token #</div>
                            <div style="font-size:0.85rem;color:#e6edf3">{ser.get('token_number','—')}</div>
                        </div>
                    </div>
                    {f'<div style="margin-top:10px;padding:10px;background:#0a1a0a;border-radius:6px;font-size:0.82rem;color:#8b949e">{ser.get("audio_message_hi","")}</div>' if ser.get("audio_message_hi") else ''}
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Replay not yet completed.")

    # ── Tab 3: Field Comparison ───────────────────────────────────────────
    with main_tab3:
        st.markdown('<div class="section-label">Field-by-Field Comparison</div>',
                    unsafe_allow_html=True)

        if st.session_state.new_fields:
            old_f = st.session_state.old_fields or {}
            new_f = st.session_state.new_fields or {}
            rows = compare_fields(old_f, new_f)

            # Summary metrics
            changed_count = sum(1 for r in rows if r["Changed"] == "🔄 Changed")
            same_count = len(rows) - changed_count

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""
                <div style="background:#0d1f33;border:1px solid #1d3a5f;border-radius:8px;padding:14px;text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#2ea4ff">{len(rows)}</div>
                    <div style="font-size:0.7rem;color:#6e7681">Total Fields</div>
                </div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div style="background:#0d1a0d;border:1px solid #1a3a1a;border-radius:8px;padding:14px;text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#3dd68c">{same_count}</div>
                    <div style="font-size:0.7rem;color:#6e7681">Unchanged</div>
                </div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div style="background:#1a1200;border:1px solid #3a2a00;border-radius:8px;padding:14px;text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#f0883e">{changed_count}</div>
                    <div style="font-size:0.7rem;color:#6e7681">Changed</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            # Comparison rows
            for row in rows:
                changed = row["Changed"] == "🔄 Changed"
                border = "#3a2a00" if changed else "#1a3a1a"
                badge_color = "#f0883e" if changed else "#3dd68c"
                badge_bg = "#1a1200" if changed else "#0d1a0d"

                st.markdown(f"""
                <div style="background:#161b22;border:1px solid {border};border-radius:10px;
                            padding:14px 16px;margin-bottom:10px">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
                        <span style="font-size:0.75rem;font-weight:700;color:#2ea4ff;text-transform:uppercase;letter-spacing:0.06em">{row['Field']}</span>
                        <span style="font-size:0.7rem;font-weight:600;color:{badge_color};background:{badge_bg};padding:2px 10px;border-radius:20px">{row['Changed']}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                        <div>
                            <div style="font-size:0.65rem;color:#6e7681;margin-bottom:4px">OLD VALUE</div>
                            <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#8b949e;
                                        background:#0a0e13;padding:8px;border-radius:6px;word-break:break-all">
                                {row['Old Value'] if row['Old Value'] != 'None' else '—'}
                            </div>
                        </div>
                        <div>
                            <div style="font-size:0.65rem;color:#6e7681;margin-bottom:4px">NEW VALUE</div>
                            <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                        color:{'#f0883e' if changed else '#3dd68c'};
                                        background:#0a0e13;padding:8px;border-radius:6px;word-break:break-all">
                                {row['New Value'] if row['New Value'] != 'None' else '—'}
                            </div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Run the automation to completion to see field comparison.")

    # ── Tab 4: Old JSON ───────────────────────────────────────────────────
    with main_tab4:
        st.markdown('<div class="section-label">Original Report — Full JSON</div>',
                    unsafe_allow_html=True)
        if st.session_state.old_report:
            render_json_block(st.session_state.old_report)
            st.download_button(
                "⬇ Download Old Report JSON",
                data=json.dumps(st.session_state.old_report, indent=2),
                file_name=f"old_report_{assessment_id_input}.json",
                mime="application/json"
            )
        else:
            st.info("Not yet fetched.")

    # ── Tab 5: New JSON ───────────────────────────────────────────────────
    with main_tab5:
        st.markdown('<div class="section-label">New Report — Full JSON</div>',
                    unsafe_allow_html=True)
        if st.session_state.new_report:
            render_json_block(st.session_state.new_report)
            st.download_button(
                "⬇ Download New Report JSON",
                data=json.dumps(st.session_state.new_report, indent=2),
                file_name=f"new_report_{st.session_state.new_assessment_id}.json",
                mime="application/json"
            )
        else:
            st.info("New report not yet fetched. Complete the automation first.")


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION LOG (collapsible at bottom)
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.logs and st.session_state.step >= 4:
    with st.expander("📋 Full Execution Log", expanded=False):
        lines = "".join(
            f'<div class="log-line {e["level"]}">[{e["ts"]}] {e["msg"]}</div>'
            for e in st.session_state.logs
        )
        st.markdown(
            f'<div style="max-height:300px;overflow-y:auto;'
            f'background:#0a0e13;border-radius:6px;padding:12px">{lines}</div>',
            unsafe_allow_html=True
        )
