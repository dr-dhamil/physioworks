import datetime
import json
from fpdf import FPDF
from google import genai
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

st.set_page_config(
    page_title="Dr. Geetanjali’s PhysioWorks",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- BRANDING & MODERN CLINIC UI THEME (#1B365D Navy & #F47920 Orange) ---
st.markdown(
    """
    <style>
    :root {
        --navy: #1B365D;
        --navy-dark: #122542;
        --orange: #F47920;
        --orange-hover: #D96412;
        --bg-soft: #F4F6F9;
        --card-bg: #FFFFFF;
        --border-subtle: #E2E8F0;
        --text-main: #1E293B;
    }

    .stApp {
        background-color: var(--bg-soft);
        color: var(--text-main);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--navy) 0%, var(--navy-dark) 100%);
        border-right: 3px solid var(--orange);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.12);
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.25);
    }
    [data-testid="stSidebar"] input {
        background-color: rgba(255, 255, 255, 0.14) !important;
        color: #FFFFFF !important;
    }

    .clinic-banner {
        background: linear-gradient(135deg, var(--navy) 0%, #24477A 100%);
        color: #FFFFFF;
        padding: 20px 26px;
        border-radius: 12px;
        border-bottom: 4px solid var(--orange);
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(27, 54, 93, 0.12);
    }
    .clinic-banner h1 {
        color: #FFFFFF !important;
        margin: 0 0 4px 0;
        font-size: 1.75rem;
        font-weight: 700;
    }
    .clinic-tagline {
        color: #FDBA74;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0;
    }
    .clinic-badge {
        display: inline-block;
        background-color: var(--orange);
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 999px;
        letter-spacing: 0.4px;
        margin-top: 8px;
    }

    .ui-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    .patient-strip {
        background-color: var(--card-bg);
        border-left: 5px solid var(--orange);
        border-top: 1px solid var(--border-subtle);
        border-right: 1px solid var(--border-subtle);
        border-bottom: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    .section-heading {
        color: var(--navy) !important;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #F1F5F9;
    }
    .ai-box {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #1B365D;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 12px;
        margin-bottom: 14px;
    }

    h2, h3 {
        color: var(--navy) !important;
    }

    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button {
        background-color: var(--orange) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.1rem !important;
        transition: background-color 0.2s ease;
    }
    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover {
        background-color: var(--orange-hover) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-subtle);
        border-top: 3px solid var(--navy);
        border-radius: 8px;
        padding: 12px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BODY_REGIONS = [
    "Cervical Spine (Neck)",
    "Thoracic Spine (Upper Back)",
    "Lumbar Spine (Lower Back)",
    "Shoulder Complex",
    "Elbow",
    "Wrist & Hand",
    "Hip & Groin",
    "Knee Joint",
    "Ankle & Foot",
    "TMJ / Jaw",
]

# --- SUPABASE CONNECTION SETUP ---
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
  SUPABASE_URL = "https://bicpyvfotfqoftpppatd.supabase.co"
  SUPABASE_KEY = "sb_publishable_FK0NBVBpOG-Ek9BOIqQUjQ_1Jb-fOgW"


supabase = None
db_connected = False
try:
  if (
      SUPABASE_URL != "https://your-project-id.supabase.co"
      and SUPABASE_KEY != "your-anon-public-key-here"
  ):
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    db_connected = True
except Exception as e:
  st.sidebar.error(f"Supabase connection error: {e}")

# --- GEMINI AI KEY INITIALIZATION ---
secret_gemini_key = ""
try:
  secret_gemini_key = st.secrets.get("GEMINI_API_KEY") or ""
except Exception:
  secret_gemini_key = ""

if "gemini_api_key_input" not in st.session_state:
  st.session_state["gemini_api_key_input"] = secret_gemini_key


def get_data(table_name):
  if supabase:
    try:
      response = supabase.table(table_name).select("*").execute()
      if response.data is not None:
        return pd.DataFrame(response.data)
    except Exception:
      pass
  if table_name not in st.session_state:
    st.session_state[table_name] = pd.DataFrame()
  return st.session_state[table_name]


def save_data(table_name, row_dict):
  if supabase:
    try:
      supabase.table(table_name).insert(row_dict).execute()
    except Exception as e:
      st.error(f"Error saving to Supabase: {e}")
      return
  if table_name not in st.session_state:
    st.session_state[table_name] = pd.DataFrame()
  new_df = pd.DataFrame([row_dict])
  st.session_state[table_name] = pd.concat(
      [st.session_state[table_name], new_df], ignore_index=True
  )


def col_val(df, col_options, default=""):
  for c in col_options:
    if c in df.columns:
      return c
  return default


def format_patient_selector(patients_df, pid_col, name_col):
  patient_ids = patients_df[pid_col].tolist()

  def _fmt(pid):
    if name_col:
      match = patients_df[patients_df[pid_col] == pid]
      if not match.empty:
        return f"{pid} • {match.iloc[0][name_col]}"
    return pid

  return patient_ids, _fmt


def render_patient_banner(patients_df, selected_pid):
  pid_col = col_val(patients_df, ["patient_id", "Patient_ID"])
  name_col = col_val(patients_df, ["name", "Name"])
  phone_col = col_val(patients_df, ["phone", "Phone"])
  gender_col = col_val(patients_df, ["gender", "Gender"])
  hist_col = col_val(patients_df, ["medical_history", "Medical_History"])

  row = patients_df[patients_df[pid_col] == selected_pid]
  if row.empty:
    return ""

  r = row.iloc[0]
  p_name = r.get(name_col, "N/A") if name_col else "N/A"
  p_phone = r.get(phone_col, "N/A") if phone_col else "N/A"
  p_gender = r.get(gender_col, "N/A") if gender_col else "N/A"
  p_hist = str(r.get(hist_col, "") or "").strip()

  st.markdown(
      f"""
      <div class="patient-strip">
          <strong>Active Patient:</strong> {p_name} &nbsp;•&nbsp;
          <strong>ID:</strong> <code>{selected_pid}</code> &nbsp;•&nbsp;
          <strong>Gender:</strong> {p_gender} &nbsp;•&nbsp;
          <strong>Phone:</strong> {p_phone}
      </div>
      """,
      unsafe_allow_html=True,
  )

  if p_hist:
    alert_keywords = [
        "diabet",
        "hypertens",
        "bp",
        "anticoagulant",
        "blood thinner",
        "pregnan",
        "osteopor",
        "cancer",
        "surger",
        "fracture",
        "pacemaker",
    ]
    if any(k in p_hist.lower() for k in alert_keywords):
      st.warning(f"⚠️ **Medical Precaution Flags:** {p_hist}")
    else:
      st.info(f"📋 **Medical Notes:** {p_hist}")
  return p_hist


def render_interactive_body_chart(selected_regions):
  """Option B: Crisp Anterior/Posterior clinical SVG body map with direct pain-spot pins & region highlights."""
  active_json = json.dumps(selected_regions)
  html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{
          margin: 0; padding: 10px; background: #FFFFFF;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: #1E293B;
        }}
        .toolbar {{
          display: flex; justify-content: space-between; align-items: center;
          gap: 8px; margin-bottom: 8px; flex-wrap: wrap;
        }}
        .btn-group {{ display: flex; gap: 6px; }}
        .tbtn {{
          border: 1px solid #CBD5E1; background: #F8FAFC; color: #1B365D;
          padding: 5px 11px; border-radius: 7px; font-size: 12px; font-weight: 600;
          cursor: pointer; transition: all 0.15s ease;
        }}
        .tbtn.active {{
          background: #1B365D; color: #FFFFFF; border-color: #1B365D;
        }}
        .tbtn.clear {{
          background: #FEF2F2; color: #B91C1C; border-color: #FECACA;
        }}
        .status-chip {{
          background: #FFF7ED; border: 1px solid #FDBA74; color: #9A3412;
          padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700;
        }}
        .canvas-box {{
          position: relative; width: 100%; height: 390px;
          border: 1px solid #E2E8F0; border-radius: 10px; background: #F8FAFC;
          display: flex; justify-content: center; align-items: center; overflow: hidden;
        }}
        svg {{ height: 374px; width: auto; user-select: none; }}
        .body-part {{
          fill: #E2E8F0; stroke: #64748B; stroke-width: 1.6;
          cursor: pointer; transition: fill 0.15s ease;
        }}
        .body-part:hover {{ fill: #FED7AA; }}
        .body-part.selected {{ fill: #F47920; stroke: #9A3412; stroke-width: 2; }}
        .pin-dot {{ fill: #DC2626; stroke: #FFFFFF; stroke-width: 1.5; }}
        .pin-ring {{ fill: none; stroke: #F47920; stroke-width: 1.5; opacity: 0.85; }}
        .pin-num {{ font-size: 9px; font-weight: 700; fill: #FFFFFF; text-anchor: middle; dominant-baseline: central; pointer-events: none; }}
        .footer-bar {{
          margin-top: 8px; font-size: 11px; color: #475569;
          display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap;
        }}
        .pin-summary {{ color: #1B365D; font-weight: 600; }}
      </style>
    </head>
    <body>
      <div class="toolbar">
        <div class="btn-group">
          <button id="btn-front" class="tbtn active" onclick="setSide('front')">Anterior (Front)</button>
          <button id="btn-back" class="tbtn" onclick="setSide('back')">Posterior (Back)</button>
          <button class="tbtn clear" onclick="clearAllPins()">Clear Pins</button>
        </div>
        <span id="hover-readout" class="status-chip">Click body to mark pain point</span>
      </div>

      <div class="canvas-box">
        <!-- ANTERIOR (FRONT) SVG -->
        <svg id="svg-front" viewBox="0 0 260 430">
          <!-- Head & TMJ -->
          <ellipse class="body-part" data-region="TMJ / Jaw" cx="130" cy="42" rx="28" ry="34" />
          <circle class="body-part" data-region="TMJ / Jaw" cx="101" cy="48" r="6" />
          <circle class="body-part" data-region="TMJ / Jaw" cx="159" cy="48" r="6" />

          <!-- Cervical (Neck) -->
          <rect class="body-part" data-region="Cervical Spine (Neck)" x="114" y="74" width="32" height="22" rx="6" />

          <!-- Shoulders -->
          <ellipse class="body-part" data-region="Shoulder Complex" cx="84" cy="112" rx="22" ry="16" />
          <ellipse class="body-part" data-region="Shoulder Complex" cx="176" cy="112" rx="22" ry="16" />

          <!-- Chest / Thoracic Front -->
          <path class="body-part" data-region="Thoracic Spine (Upper Back)" d="M98,98 L162,98 L156,154 L104,154 Z" />

          <!-- Abdomen / Lumbar Front -->
          <path class="body-part" data-region="Lumbar Spine (Lower Back)" d="M104,154 L156,154 L160,196 L100,196 Z" />

          <!-- Pelvis & Hip/Groin -->
          <path class="body-part" data-region="Hip & Groin" d="M100,196 L160,196 L166,224 L94,224 Z" />
          <ellipse class="body-part" data-region="Hip & Groin" cx="102" cy="216" rx="16" ry="12" />
          <ellipse class="body-part" data-region="Hip & Groin" cx="158" cy="216" rx="16" ry="12" />

          <!-- Upper Arms -->
          <rect class="body-part" data-region="Shoulder Complex" x="62" y="126" width="22" height="54" rx="10" transform="rotate(6 73 153)" />
          <rect class="body-part" data-region="Shoulder Complex" x="176" y="126" width="22" height="54" rx="10" transform="rotate(-6 187 153)" />

          <!-- Elbows -->
          <circle class="body-part" data-region="Elbow" cx="70" cy="184" r="11" />
          <circle class="body-part" data-region="Elbow" cx="190" cy="184" r="11" />

          <!-- Forearms -->
          <rect class="body-part" data-region="Elbow" x="55" y="194" width="20" height="52" rx="9" transform="rotate(8 65 220)" />
          <rect class="body-part" data-region="Elbow" x="185" y="194" width="20" height="52" rx="9" transform="rotate(-8 195 220)" />

          <!-- Wrist & Hand -->
          <ellipse class="body-part" data-region="Wrist & Hand" cx="56" cy="256" rx="12" ry="18" transform="rotate(10 56 256)" />
          <ellipse class="body-part" data-region="Wrist & Hand" cx="204" cy="256" rx="12" ry="18" transform="rotate(-10 204 256)" />

          <!-- Thighs -->
          <path class="body-part" data-region="Hip & Groin" d="M96,224 L126,224 L122,302 L92,302 Z" />
          <path class="body-part" data-region="Hip & Groin" d="M134,224 L164,224 L168,302 L138,302 Z" />

          <!-- Knees -->
          <ellipse class="body-part" data-region="Knee Joint" cx="107" cy="310" rx="15" ry="14" />
          <ellipse class="body-part" data-region="Knee Joint" cx="153" cy="310" rx="15" ry="14" />

          <!-- Lower Legs / Shins -->
          <path class="body-part" data-region="Knee Joint" x="93" d="M93,324 L121,324 L117,384 L97,384 Z" />
          <path class="body-part" data-region="Knee Joint" x="139" d="M139,324 L167,324 L163,384 L143,384 Z" />

          <!-- Ankle & Foot -->
          <ellipse class="body-part" data-region="Ankle & Foot" cx="106" cy="392" rx="13" ry="9" />
          <ellipse class="body-part" data-region="Ankle & Foot" cx="154" cy="392" rx="13" ry="9" />
          <path class="body-part" data-region="Ankle & Foot" d="M92,398 L118,398 L116,422 L86,422 Z" />
          <path class="body-part" data-region="Ankle & Foot" d="M142,398 L168,398 L174,422 L144,422 Z" />

          <g id="pins-front"></g>
        </svg>

        <!-- POSTERIOR (BACK) SVG -->
        <svg id="svg-back" viewBox="0 0 260 430" style="display:none;">
          <!-- Head Back & Neck -->
          <ellipse class="body-part" data-region="Cervical Spine (Neck)" cx="130" cy="42" rx="28" ry="34" />
          <rect class="body-part" data-region="Cervical Spine (Neck)" x="114" y="74" width="32" height="22" rx="6" />

          <!-- Upper Back / Thoracic & Scapulae -->
          <path class="body-part" data-region="Thoracic Spine (Upper Back)" d="M96,98 L164,98 L158,156 L102,156 Z" />
          <ellipse class="body-part" data-region="Thoracic Spine (Upper Back)" cx="108" cy="124" rx="15" ry="20" />
          <ellipse class="body-part" data-region="Thoracic Spine (Upper Back)" cx="152" cy="124" rx="15" ry="20" />

          <!-- Shoulders Posterior -->
          <ellipse class="body-part" data-region="Shoulder Complex" cx="84" cy="112" rx="22" ry="16" />
          <ellipse class="body-part" data-region="Shoulder Complex" cx="176" cy="112" rx="22" ry="16" />

          <!-- Lumbar Spine (Lower Back) -->
          <path class="body-part" data-region="Lumbar Spine (Lower Back)" d="M102,156 L158,156 L162,196 L98,196 Z" />

          <!-- Glutes / Hip Posterior -->
          <ellipse class="body-part" data-region="Hip & Groin" cx="111" cy="212" rx="18" ry="16" />
          <ellipse class="body-part" data-region="Hip & Groin" cx="149" cy="212" rx="18" ry="16" />

          <!-- Arms & Elbows & Wrists -->
          <rect class="body-part" data-region="Shoulder Complex" x="62" y="126" width="22" height="54" rx="10" transform="rotate(6 73 153)" />
          <rect class="body-part" data-region="Shoulder Complex" x="176" y="126" width="22" height="54" rx="10" transform="rotate(-6 187 153)" />
          <circle class="body-part" data-region="Elbow" cx="70" cy="184" r="11" />
          <circle class="body-part" data-region="Elbow" cx="190" cy="184" r="11" />
          <rect class="body-part" data-region="Elbow" x="55" y="194" width="20" height="52" rx="9" transform="rotate(8 65 220)" />
          <rect class="body-part" data-region="Elbow" x="185" y="194" width="20" height="52" rx="9" transform="rotate(-8 195 220)" />
          <ellipse class="body-part" data-region="Wrist & Hand" cx="56" cy="256" rx="12" ry="18" transform="rotate(10 56 256)" />
          <ellipse class="body-part" data-region="Wrist & Hand" cx="204" cy="256" rx="12" ry="18" transform="rotate(-10 204 256)" />

          <!-- Hamstrings -->
          <path class="body-part" data-region="Hip & Groin" d="M95,226 L126,226 L122,302 L92,302 Z" />
          <path class="body-part" data-region="Hip & Groin" d="M134,226 L165,226 L168,302 L138,302 Z" />

          <!-- Back of Knee -->
          <ellipse class="body-part" data-region="Knee Joint" cx="107" cy="310" rx="14" ry="13" />
          <ellipse class="body-part" data-region="Knee Joint" cx="153" cy="310" rx="14" ry="13" />

          <!-- Calves -->
          <path class="body-part" data-region="Knee Joint" d="M93,324 L121,324 L117,384 L97,384 Z" />
          <path class="body-part" data-region="Knee Joint" d="M139,324 L167,324 L163,384 L143,384 Z" />

          <!-- Heel & Ankle -->
          <ellipse class="body-part" data-region="Ankle & Foot" cx="106" cy="392" rx="13" ry="9" />
          <ellipse class="body-part" data-region="Ankle & Foot" cx="154" cy="392" rx="13" ry="9" />
          <rect class="body-part" data-region="Ankle & Foot" x="92" y="400" width="26" height="20" rx="5" />
          <rect class="body-part" data-region="Ankle & Foot" x="142" y="400" width="26" height="20" rx="5" />

          <g id="pins-back"></g>
        </svg>
      </div>

      <div class="footer-bar">
        <span>Orange = selected assessment region • Red numbered pins = marked pain spots</span>
        <span id="pin-summary" class="pin-summary">No pain pins marked yet</span>
      </div>

      <script>
        const selectedSet = new Set({active_json});
        let currentSide = 'front';
        const pins = {{ front: [], back: [] }};

        function refreshHighlights() {{
          document.querySelectorAll('.body-part').forEach(el => {{
            const reg = el.getAttribute('data-region');
            if (selectedSet.has(reg)) el.classList.add('selected');
            else el.classList.remove('selected');
          }});
        }}

        function setSide(side) {{
          currentSide = side;
          document.getElementById('svg-front').style.display = side === 'front' ? 'block' : 'none';
          document.getElementById('svg-back').style.display = side === 'back' ? 'block' : 'none';
          document.getElementById('btn-front').classList.toggle('active', side === 'front');
          document.getElementById('btn-back').classList.toggle('active', side === 'back');
        }}

        function renderPins() {{
          ['front', 'back'].forEach(side => {{
            const g = document.getElementById('pins-' + side);
            g.innerHTML = '';
            pins[side].forEach((p, idx) => {{
              const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
              ring.setAttribute('cx', p.x); ring.setAttribute('cy', p.y); ring.setAttribute('r', '10');
              ring.setAttribute('class', 'pin-ring');

              const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
              dot.setAttribute('cx', p.x); dot.setAttribute('cy', p.y); dot.setAttribute('r', '7');
              dot.setAttribute('class', 'pin-dot');

              const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
              txt.setAttribute('x', p.x); txt.setAttribute('y', p.y + 0.5);
              txt.setAttribute('class', 'pin-num');
              txt.textContent = String(idx + 1);

              g.appendChild(ring); g.appendChild(dot); g.appendChild(txt);
            }});
          }});

          const allLabels = [
            ...pins.front.map((p, i) => `#${{i+1}} Front: ${{p.label}}`),
            ...pins.back.map((p, i) => `#${{i+1}} Back: ${{p.label}}`)
          ];
          document.getElementById('pin-summary').textContent =
            allLabels.length ? allLabels.join(' | ') : 'No pain pins marked yet';
        }}

        function clearAllPins() {{
          pins.front = [];
          pins.back = [];
          renderPins();
          document.getElementById('hover-readout').textContent = 'Pins cleared';
        }}

        document.querySelectorAll('.body-part').forEach(el => {{
          el.addEventListener('mouseenter', () => {{
            const reg = el.getAttribute('data-region');
            document.getElementById('hover-readout').textContent = reg;
          }});
          el.addEventListener('click', evt => {{
            const svg = el.ownerSVGElement;
            const pt = svg.createSVGPoint();
            pt.x = evt.clientX; pt.y = evt.clientY;
            const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
            const reg = el.getAttribute('data-region');
            const sideText = currentSide === 'front' ? 'Anterior' : 'Posterior';
            const latText = svgP.x < 122 ? 'Left ' : (svgP.x > 138 ? 'Right ' : '');
            const desc = `${{latText}}${{sideText}} ${{reg}}`;

            pins[currentSide].push({{ x: svgP.x.toFixed(1), y: svgP.y.toFixed(1), label: desc }});
            renderPins();
            document.getElementById('hover-readout').textContent = `Pinned: ${{desc}}`;
          }});
        }});

        refreshHighlights();
      </script>
    </body>
    </html>
    """
  components.html(html_code, height=462)


def generate_gemini_protocol(api_key, context_payload):
  """Calls Gemini via google-genai SDK first, with direct REST API fallback."""
  if not api_key:
    return (
        "⚠️ **Gemini API Key missing.** Paste your Gemini API key in the"
        " left sidebar under **Gemini AI Settings**."
    )

  prompt = f"""
You are a clinical physiotherapy decision-support assistant for Dr. Geetanjali's PhysioWorks.
Analyze the following patient assessment data and provide a clear, structured clinical protocol suggestion.
Frame findings as clinical hypotheses to support professional physiotherapy judgment (not a standalone medical diagnosis).

Assessment Data:
{json.dumps(context_payload, indent=2)}

Format your response cleanly with these 4 sections:
1. **Safety & Precaution Check** (flag any medical history precautions, red flags, or high irritability considerations)
2. **Clinical Impression & Key Impairments** (priority body regions, pain/irritability behavior, ROM/neuro/MMT findings)
3. **Suggested Treatment Protocol** (electrotherapy/modalities, manual therapy focus, targeted exercises with sets/reps/dosage & progression rules)
4. **Reassessment & Milestones** (key NPRS, ROM, and functional markers to track at follow-up)
"""

  models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]
  errors = []

  # Attempt 1: Official google-genai SDK
  try:
    client = genai.Client(api_key=api_key)
    for model_name in models_to_try:
      try:
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = getattr(resp, "text", None)
        if text and text.strip():
          return text.strip()
      except Exception as e:
        errors.append(f"SDK[{model_name}]: {e}")
  except Exception as e:
    errors.append(f"SDK init: {e}")

  # Attempt 2: Direct Gemini REST endpoint fallback
  for model_name in models_to_try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
      r = requests.post(
          url,
          params={"key": api_key},
          json=payload,
          timeout=30,
      )
      if r.status_code == 200:
        data = r.json()
        candidates = data.get("candidates") or []
        if candidates:
          parts = (candidates[0].get("content") or {}).get("parts") or []
          joined = "".join(p.get("text", "") for p in parts if p.get("text"))
          if joined.strip():
            return joined.strip()
      else:
        errors.append(f"REST[{model_name}] HTTP {r.status_code}: {r.text[:220]}")
    except Exception as e:
      errors.append(f"REST[{model_name}]: {e}")

  raise RuntimeError(" | ".join(errors[-3:]) if errors else "Unknown Gemini error")


def _latin1_safe(text):
  return str(text or "").encode("latin-1", errors="replace").decode("latin-1")


def create_assessment_pdf(
    patient_row, asm_row=None, logo_path="image_500b64.jpg"
):
  pdf = FPDF()
  pdf.set_auto_page_break(auto=True, margin=15)
  pdf.add_page()

  try:
    pdf.image(logo_path, x=12, y=10, w=32)
  except Exception:
    pass

  pdf.set_xy(48, 12)
  pdf.set_font("Helvetica", "B", 16)
  pdf.set_text_color(27, 54, 93)
  pdf.cell(0, 8, _latin1_safe("Dr. Geetanjali's PhysioWorks"), ln=True)

  pdf.set_x(48)
  pdf.set_font("Helvetica", "", 10)
  pdf.set_text_color(244, 121, 32)
  pdf.cell(
      0,
      6,
      _latin1_safe(
          "Physiotherapy | Osteopathy | Chiropractic - Clinical Assessment"
          " Record"
      ),
      ln=True,
  )

  pdf.ln(10)
  pdf.set_draw_color(244, 121, 32)
  pdf.set_line_width(0.8)
  pdf.line(12, pdf.get_y(), 198, pdf.get_y())
  pdf.ln(6)

  pdf.set_font("Helvetica", "B", 12)
  pdf.set_text_color(27, 54, 93)
  pdf.cell(0, 8, _latin1_safe("1. Patient Profile & Screening"), ln=True)

  pdf.set_font("Helvetica", "", 10)
  pdf.set_text_color(30, 41, 59)
  pid = patient_row.get("patient_id") or patient_row.get("Patient_ID", "N/A")
  name = patient_row.get("name") or patient_row.get("Name", "N/A")
  gender = patient_row.get("gender") or patient_row.get("Gender", "N/A")
  phone = patient_row.get("phone") or patient_row.get("Phone", "N/A")
  reg_date = patient_row.get("registration_date") or patient_row.get(
      "Registration_Date", str(datetime.date.today())
  )
  med_hist = patient_row.get("medical_history") or patient_row.get(
      "Medical_History", "None reported"
  )

  pdf.cell(95, 7, _latin1_safe(f"Patient ID: {pid}"), border=1)
  pdf.cell(91, 7, _latin1_safe(f"Date: {reg_date}"), border=1, ln=True)
  pdf.cell(95, 7, _latin1_safe(f"Name: {name}"), border=1)
  pdf.cell(
      91, 7, _latin1_safe(f"Gender / Phone: {gender} | {phone}"), border=1, ln=True
  )
  pdf.multi_cell(
      186,
      7,
      _latin1_safe(f"Medical History & Safety Flags: {med_hist}"),
      border=1,
  )
  pdf.ln(5)

  pdf.set_font("Helvetica", "B", 12)
  pdf.set_text_color(27, 54, 93)
  pdf.cell(
      0, 8, _latin1_safe("2. Clinical Assessment & Examination Findings"), ln=True
  )

  pdf.set_font("Helvetica", "", 10)
  pdf.set_text_color(30, 41, 59)

  if asm_row is not None:
    asm_id = asm_row.get("assessment_id") or asm_row.get(
        "Assessment_ID", "N/A"
    )
    asm_date = asm_row.get("date") or asm_row.get("Date", "N/A")
    regions = asm_row.get("body_parts") or asm_row.get("Body_Parts", "N/A")
    vas = asm_row.get("vas_score") or asm_row.get("VAS_Score", "N/A")
    details = asm_row.get("assessment_details") or asm_row.get(
        "Assessment_Details", "N/A"
    )
    plan = asm_row.get("suggested_treatment") or asm_row.get(
        "Suggested_Treatment", "N/A"
    )
    duration = asm_row.get("suggested_duration") or asm_row.get(
        "Suggested_Duration", "N/A"
    )
    therapist = asm_row.get("therapist") or asm_row.get("Therapist", "N/A")

    pdf.cell(95, 7, _latin1_safe(f"Assessment ID: {asm_id}"), border=1)
    pdf.cell(
        91, 7, _latin1_safe(f"Assessment Date: {asm_date}"), border=1, ln=True
    )
    pdf.cell(140, 7, _latin1_safe(f"Affected Region(s): {regions}"), border=1)
    pdf.cell(46, 7, _latin1_safe(f"Activity NPRS: {vas}/10"), border=1, ln=True)
    pdf.multi_cell(
        186,
        7,
        _latin1_safe(f"Examination, ROM, Special Tests & MMT:\n{details}"),
        border=1,
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(27, 54, 93)
    pdf.cell(
        0, 8, _latin1_safe("3. Rehabilitation Plan & Therapist Assignment"), ln=True
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(
        186, 7, _latin1_safe(f"Suggested Modalities & Plan:\n{plan}"), border=1
    )
    pdf.cell(
        95, 7, _latin1_safe(f"Recommended Duration: {duration}"), border=1
    )
    pdf.cell(
        91, 7, _latin1_safe(f"Assigned Therapist: {therapist}"), border=1, ln=True
    )
  else:
    blank_sections = [
        "Chief Complaint, Onset & 24-Hr Behavior:",
        "NPRS Pain Score - Rest: ___/10   Activity: ___/10   Night: ___/10",
        "Observation & Posture:",
        "Active / Passive ROM & End-Feel:",
        "Neurological Screen (Myotomes / Dermatomes / Reflexes):",
        "Manual Muscle Testing (MMT 0-5) & Strength:",
        "Region-Specific Special Tests & Side Comparison:",
        "Clinical Impression & Differential Diagnosis:",
        "Treatment Plan, Modalities & Home Exercise Program:",
    ]
    for sec in blank_sections:
      pdf.multi_cell(186, 12, _latin1_safe(sec), border=1)

  pdf.ln(12)
  pdf.set_font("Helvetica", "I", 9)
  pdf.set_text_color(100, 116, 139)
  pdf.cell(
      0,
      6,
      _latin1_safe(
          "Clinician Signature: ___________________________      Date:"
          " _______________"
      ),
      ln=True,
  )

  return bytes(pdf.output())


if "asm_body_parts" not in st.session_state:
  st.session_state["asm_body_parts"] = []

# --- SIDEBAR ---
with st.sidebar:
  try:
    st.sidebar.image("image_500b64.jpg", width=210)
  except Exception:
    st.sidebar.markdown("### 🩺 PhysioWorks")

  st.markdown("---")
  menu = st.selectbox(
      "Clinic Workspace",
      [
          "Clinical Assessment",
          "Patient Registration",
          "Daily Treatment Log",
          "Progress & Summary",
      ],
  )
  st.markdown("---")
  st.markdown("**🤖 Gemini AI Settings**")
  st.text_input(
      "Gemini API Key",
      type="password",
      key="gemini_api_key_input",
      placeholder="Paste Gemini API key here",
  )
  GEMINI_API_KEY = st.session_state["gemini_api_key_input"].strip() or None

  if GEMINI_API_KEY:
    st.success("● Gemini AI: Ready")
  else:
    st.warning("● Gemini AI: Enter API Key Above")

  if db_connected:
    st.success("● Supabase Cloud Sync: Active")
  else:
    st.info("● Storage Mode: Session Memory")

# --- TOP BANNER & CLINIC SNAPSHOT ---
patients_all = get_data("patients")
assessments_all = get_data("assessments")
logs_all = get_data("daily_logs")

st.markdown(
    """
    <div class="clinic-banner">
        <h1>🩺 Dr. Geetanjali’s PhysioWorks</h1>
        <p class="clinic-tagline">Physiotherapy • Osteopathy • Chiropractic — Clinical Documentation & Rehabilitation Suite</p>
        <span class="clinic-badge">GET THE CARE YOU DESERVE</span>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3 = st.columns(3)
k1.metric("Registered Patients", len(patients_all))
k2.metric("Assessments Completed", len(assessments_all))
k3.metric("Treatment Sessions Logged", len(logs_all))

# =====================================================================
# 1. REDESIGNED CLINICAL ASSESSMENT (OPTION B BODY CHART + GEMINI AI)
# =====================================================================
if menu == "Clinical Assessment":
  pid_col = col_val(patients_all, ["patient_id", "Patient_ID"])
  name_col = col_val(patients_all, ["name", "Name"])

  if patients_all.empty or not pid_col:
    st.warning("Register a patient first under **Patient Registration**.")
  else:
    patient_ids, fmt_fn = format_patient_selector(
        patients_all, pid_col, name_col
    )
    selected_patient = st.selectbox(
        "Select Patient", patient_ids, format_func=fmt_fn
    )
    patient_med_history = render_patient_banner(patients_all, selected_patient)

    if not assessments_all.empty:
      asm_pid_col = col_val(assessments_all, ["patient_id", "Patient_ID"])
      if asm_pid_col:
        p_asm = assessments_all[assessments_all[asm_pid_col] == selected_patient]
        if not p_asm.empty:
          with st.expander(
              f"📂 Past Assessments for {selected_patient} ({len(p_asm)})"
          ):
            st.dataframe(p_asm, width="stretch", hide_index=True)

    # --- STEP 1: INTERACTIVE BODY CHART & PAIN MARKING ---
    st.markdown(
        '<div class="ui-card"><div class="section-heading">1. Anterior &'
        " Posterior Pain Chart & Region Selection</div>",
        unsafe_allow_html=True,
    )
    col_map, col_reg = st.columns([1.08, 1.22])

    with col_map:
      render_interactive_body_chart(st.session_state["asm_body_parts"])

    with col_reg:
      body_parts = st.multiselect(
          "Affected Body Region(s):",
          BODY_REGIONS,
          key="asm_body_parts",
      )
      pain_spot_notes = st.text_input(
          "Pinned Pain Locations / Side & Tissue Note",
          placeholder=(
              "e.g., #1 Right Anterior Knee, #2 Left Lumbar Paraspinal"
          ),
          key="asm_pain_spots",
      )

      st.markdown("**Pain Intensity & Irritability (NPRS 0–10)**")
      p1, p2, p3 = st.columns(3)
      with p1:
        nprs_rest = st.slider("Rest", 0, 10, 0, key="nprs_rest_s")
      with p2:
        nprs_activity = st.slider("Activity", 0, 10, 5, key="nprs_act_s")
      with p3:
        nprs_night = st.slider("Night", 0, 10, 2, key="nprs_night_s")

      irritability = st.selectbox(
          "Symptom Irritability",
          [
              "Low (Settles quickly, tolerates moderate load)",
              "Moderate (Provoked by clear activity, settles within hours)",
              "High (Easily provoked, slow to settle, night/rest symptoms)",
          ],
          key="asm_irritability",
      )
      functional_goal = st.text_input(
          "Functional Goal / Outcome Note (e.g., NDI, ODI, KOOS, stairs)",
          key="asm_goal",
      )

    st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 2: REGION-SPECIFIC EXAMINATION & MMT ---
    st.markdown(
        '<div class="ui-card"><div class="section-heading">2. Detailed'
        " Examination, Special Tests & MMT</div>",
        unsafe_allow_html=True,
    )

    assessment_details_dict = {}
    suggested_treatments = []
    bp_str = "".join(body_parts)

    if not body_parts:
      st.info(
          "Select one or more body regions above to open region-specific ROM,"
          " neurological, and special test fields."
      )

    if "Cervical" in bp_str:
      st.markdown("#### 🔹 Cervical Spine / Neck")
      c1, c2 = st.columns(2)
      with c1:
        c_rom = st.text_input(
            "Cervical ROM (Flexion 45°, Extension 45°, Lat Flexion 45°,"
            " Rotation 80°)",
            key="c_rom",
        )
      with c2:
        c_neuro = st.text_input(
            "Neurological Screen (C5–T1 Myotomes/Dermatomes/Reflexes)",
            key="c_neuro",
        )
      c_tests = st.multiselect(
          "Cervical Special Tests",
          [
              "Spurling’s Test",
              "Cervical Distraction Test",
              "Upper Limb Neurodynamic Tests (ULNT)",
              "Bakody Sign",
          ],
          key="c_tests",
      )
      assessment_details_dict["Cervical"] = {
          "ROM": c_rom,
          "Neurological": c_neuro,
          "Tests": c_tests,
      }
      suggested_treatments.append(
          "Cervical Traction + Deep Neck Flexor Endurance + Posture Correction"
      )

    if "Thoracic" in bp_str:
      st.markdown("#### 🔹 Thoracic Spine / Upper Back")
      t1, t2 = st.columns(2)
      with t1:
        t_rom = st.text_input(
            "Thoracic ROM (Flexion, Extension, Rotation, Side-Flexion)",
            key="t_rom",
        )
      with t2:
        t_palp = st.text_input(
            "Palpation / Costovertebral Mobility & Breathing", key="t_palp"
        )
      assessment_details_dict["Thoracic"] = {"ROM": t_rom, "Palpation": t_palp}
      suggested_treatments.append(
          "Thoracic Mobility + Scapular Stabilization + Breathing Re-education"
      )

    if "Lumbar" in bp_str:
      st.markdown("#### 🔹 Lumbar Spine / Low Back")
      l1, l2 = st.columns(2)
      with l1:
        l_rom = st.text_input(
            "Lumbar ROM (Flexion, Extension, Side-Glide, Rotation)", key="l_rom"
        )
      with l2:
        l_neuro = st.text_input(
            "Neurological Screen (L2–S1 Myotomes, Reflexes, Neural Tension)",
            key="l_neuro",
        )
      l_tests = st.multiselect(
          "Lumbar Special Tests",
          [
              "Straight Leg Raise (SLR)",
              "Crossed SLR",
              "Slump Test",
              "Femoral Nerve Stretch",
          ],
          key="l_tests",
      )
      assessment_details_dict["Lumbar"] = {
          "ROM": l_rom,
          "Neurological": l_neuro,
          "Tests": l_tests,
      }
      suggested_treatments.append(
          "Core Stabilization + Lumbar Traction + Centralization Mechanics"
      )

    if "Shoulder" in bp_str:
      st.markdown("#### 🔹 Shoulder Complex")
      sh_rom = st.text_input(
          "Shoulder ROM (Flexion 180°, Abduction 180°, ER/IR, Painful Arc)",
          key="sh_rom",
      )
      sh_tests = st.multiselect(
          "Shoulder Special Tests",
          [
              "Neer Test",
              "Hawkins-Kennedy Test",
              "Empty Can (Jobe)",
              "Speed's / Yergason's",
              "Apprehension / Relocation",
          ],
          key="sh_tests",
      )
      assessment_details_dict["Shoulder"] = {"ROM": sh_rom, "Tests": sh_tests}
      suggested_treatments.append(
          "Rotator Cuff Strengthening + Scapular Retraction + Ultrasound"
      )

    if "Elbow" in bp_str:
      st.markdown("#### 🔹 Elbow")
      el_rom = st.text_input(
          "Elbow Flexion/Extension & Pronation/Supination", key="el_rom"
      )
      el_tests = st.multiselect(
          "Elbow Special Tests",
          [
              "Cozen's / Maudsley's Test",
              "Resisted Wrist Flexion",
              "Valgus/Varus Stress Test",
          ],
          key="el_tests",
      )
      assessment_details_dict["Elbow"] = {"ROM": el_rom, "Tests": el_tests}
      suggested_treatments.append(
          "Eccentric Wrist Extension/Flexion + Soft Tissue Mobilization"
      )

    if "Wrist" in bp_str:
      st.markdown("#### 🔹 Wrist & Hand")
      w_rom = st.text_input(
          "Wrist Flexion/Extension, Radial/Ulnar Deviation, Pronation/Supination",
          key="w_rom",
      )
      w_tests = st.multiselect(
          "Wrist Special Tests",
          [
              "Phalen’s Test",
              "Tinel’s Sign",
              "Durkan's Test",
              "Finkelstein’s Test",
              "Scaphoid Shift Test",
          ],
          key="w_tests",
      )
      assessment_details_dict["Wrist"] = {"ROM": w_rom, "Tests": w_tests}
      suggested_treatments.append(
          "Carpal Tunnel Glides + Splinting Advice + Ergonomic Correction"
      )

    if "Hip" in bp_str:
      st.markdown("#### 🔹 Hip & Groin")
      h_rom = st.text_input(
          "Hip ROM (Flexion, Extension, Abduction/Adduction, ER/IR)", key="h_rom"
      )
      h_tests = st.multiselect(
          "Hip Special Tests",
          [
              "FADIR Test",
              "FABER (Patrick's) Test",
              "Scour Test",
              "Trendelenburg Test",
          ],
          key="h_tests",
      )
      assessment_details_dict["Hip"] = {"ROM": h_rom, "Tests": h_tests}
      suggested_treatments.append(
          "Hip Abductor Strengthening + Capsule Mobilization + Single-Leg Control"
      )

    if "Knee" in bp_str:
      st.markdown("#### 🔹 Knee Joint")
      k_rom = st.text_input(
          "Knee ROM (Flexion 140°, Extension 0°, Effusion/Sweep Test)",
          key="k_rom",
      )
      k_tests = st.multiselect(
          "Knee Special Tests",
          [
              "Lachman Test",
              "Anterior/Posterior Drawer",
              "McMurray Test",
              "Valgus/Varus Stress Test",
              "Patellar Apprehension",
          ],
          key="k_tests",
      )
      assessment_details_dict["Knee"] = {"ROM": k_rom, "Tests": k_tests}
      suggested_treatments.append(
          "Quadriceps VMO Strengthening + Patellar Mobilization + Squat"
          " Mechanics"
      )

    if "Ankle" in bp_str:
      st.markdown("#### 🔹 Ankle & Foot")
      a_rom = st.text_input(
          "Ankle Dorsiflexion/Plantarflexion, Weight-Bearing Lunge Test",
          key="a_rom",
      )
      a_tests = st.multiselect(
          "Ankle Special Tests",
          [
              "Anterior Drawer (ATFL)",
              "Squeeze Test (Syndesmosis)",
              "Thompson Test (Achilles)",
          ],
          key="a_tests",
      )
      assessment_details_dict["Ankle"] = {"ROM": a_rom, "Tests": a_tests}
      suggested_treatments.append(
          "Proprioceptive Balance Training + Calf Raises + Taping/Bracing"
      )

    if "TMJ" in bp_str:
      st.markdown("#### 🔹 TMJ / Jaw")
      j_rom = st.text_input(
          "Jaw Opening (mm), Lateral Excursion, Deviation/Deflection Path",
          key="j_rom",
      )
      j_tests = st.multiselect(
          "TMJ Screening",
          ["Joint Sounds / Clicking History", "Masticatory Muscle Palpation"],
          key="j_tests",
      )
      assessment_details_dict["TMJ"] = {"ROM": j_rom, "Tests": j_tests}
      suggested_treatments.append(
          "Cervicogenic Posture Correction + Jaw Relaxation Drills"
      )

    st.markdown("---")
    mmt_grade = st.selectbox(
        "Overall Manual Muscle Testing (MMT)",
        [
            "Grade 5 (Normal - Full ROM against max resistance)",
            "Grade 4 (Good - Full ROM against moderate resistance)",
            "Grade 3 (Fair - Full ROM against gravity only)",
            "Grade 2 (Poor - ROM with gravity eliminated)",
            "Grade 1 (Trace - Flicker of contraction)",
            "Grade 0 (Zero - No movement)",
        ],
        key="asm_mmt",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 3: GEMINI AI PROTOCOL ANALYSIS & SAVING ---
    st.markdown(
        '<div class="ui-card"><div class="section-heading">3. Gemini AI'
        " Protocol Analysis & Saving</div>",
        unsafe_allow_html=True,
    )

    if not suggested_treatments:
      suggested_treatments.append(
          "General Electrotherapy & Soft Tissue Mobilization"
      )

    ai_key = f"ai_protocol_{selected_patient}"
    if st.button("✨ Analyze Assessment & Suggest Protocol with Gemini AI"):
      payload = {
          "patient_id": selected_patient,
          "medical_history_and_flags": patient_med_history or "None recorded",
          "affected_regions": body_parts or ["General"],
          "marked_pain_locations": pain_spot_notes or "Not specified",
          "nprs": {
              "rest": nprs_rest,
              "activity": nprs_activity,
              "night": nprs_night,
          },
          "irritability": irritability,
          "functional_goal": functional_goal,
          "mmt_grade": mmt_grade,
          "region_details": assessment_details_dict,
          "baseline_modalities": suggested_treatments,
      }
      with st.spinner("Analyzing assessment with Gemini AI..."):
        try:
          st.session_state[ai_key] = generate_gemini_protocol(
              GEMINI_API_KEY, payload
          )
        except Exception as e:
          st.error(f"Gemini AI error: {e}")

    if st.session_state.get(ai_key):
      st.markdown(
          '<div class="ai-box"><strong>🤖 Gemini AI Suggested Treatment'
          " Protocol</strong></div>",
          unsafe_allow_html=True,
      )
      st.markdown(st.session_state[ai_key])

    with st.form("assessment_save_form"):
      default_plan = " | ".join(suggested_treatments)
      treatment_plan_input = st.text_area(
          "Final Treatment Plan & Suggested Modalities (Editable)",
          value=default_plan,
          height=85,
      )
      include_ai = st.checkbox(
          "Attach Gemini AI Protocol summary to saved assessment record",
          value=bool(st.session_state.get(ai_key)),
      )

      s1, s2 = st.columns(2)
      with s1:
        suggested_time = st.number_input(
            "Suggested Total Sessions", min_value=1, value=10
        )
      with s2:
        therapist = st.selectbox(
            "Assigned Therapist",
            ["Dr. Geetanjali", "Dr. Rohan", "Dr. Senior Consultant"],
        )

      save_assessment = st.form_submit_button("Save Assessment & Protocol")
      if save_assessment:
        assessment_id = f"ASM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        ai_note = ""
        if include_ai and st.session_state.get(ai_key):
          ai_note = f" | AI Protocol: {st.session_state[ai_key]}"

        spot_note = (
            f" | Pain Locations: {pain_spot_notes.strip()}"
            if pain_spot_notes.strip()
            else ""
        )

        assessment_dict = {
            "assessment_id": assessment_id,
            "patient_id": selected_patient,
            "body_parts": ", ".join(body_parts) if body_parts else "General",
            "vas_score": int(nprs_activity),
            "assessment_details": (
                f"NPRS[Rest:{nprs_rest}, Act:{nprs_activity},"
                f" Night:{nprs_night}] | Irritability: {irritability} | Goal:"
                f" {functional_goal}{spot_note} | MMT: {mmt_grade} | Details:"
                f" {str(assessment_details_dict)}{ai_note}"
            ),
            "suggested_treatment": treatment_plan_input.strip() or default_plan,
            "suggested_duration": f"{suggested_time} Sessions",
            "therapist": therapist,
            "date": str(datetime.date.today()),
        }
        save_data("assessments", assessment_dict)
        st.success(f"Assessment saved under ID `{assessment_id}`.")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# 2. PATIENT REGISTRATION & DIRECTORY
# =====================================================================
elif menu == "Patient Registration":
  st.markdown(
      '<div class="ui-card"><div class="section-heading">New Patient'
      " Intake Form</div>",
      unsafe_allow_html=True,
  )

  with st.form("reg_form"):
    c1, c2 = st.columns(2)
    with c1:
      name = st.text_input("Patient Full Name*")
      email = st.text_input("Email Address")
      gender = st.selectbox("Gender", ["Female", "Male", "Other"])
      age_occ = st.text_input("Age / Occupation & Activity Demands")
    with c2:
      phone = st.text_input("Phone Number*")
      dominant_side = st.selectbox(
          "Dominant Side", ["Right", "Left", "Bilateral / Mixed"]
      )
      referral = st.text_input("Referral Source")
      med_history = st.text_area(
          "Medical History & Safety Flags (Diabetes, BP, Surgeries, Medications,"
          " Red Flags)"
      )

    submitted = st.form_submit_button("Register & Generate Patient ID")

    if submitted and name and phone:
      counter = len(patients_all) + 1 if not patients_all.empty else 1
      patient_id = f"PW{datetime.datetime.now().strftime('%m%y')}{counter:03d}"

      meta_notes = []
      if age_occ.strip():
        meta_notes.append(f"Profile: {age_occ.strip()}")
      if dominant_side:
        meta_notes.append(f"Dominant: {dominant_side}")
      if referral.strip():
        meta_notes.append(f"Ref: {referral.strip()}")

      combined_history = med_history.strip()
      if meta_notes:
        combined_history = (
            f"{combined_history} | {' ; '.join(meta_notes)}".strip(" |")
        )

      patient_dict = {
          "patient_id": patient_id,
          "name": name.strip(),
          "email": email.strip(),
          "gender": gender,
          "phone": phone.strip(),
          "medical_history": combined_history,
          "registration_date": str(datetime.date.today()),
      }

      save_data("patients", patient_dict)
      st.success(f"Patient registered! Generated ID: **{patient_id}**")
      st.rerun()
    elif submitted:
      st.error("Please enter both Patient Full Name and Phone Number.")

  st.markdown("</div>", unsafe_allow_html=True)

  patients_display = get_data("patients")
  if not patients_display.empty:
    st.markdown(
        '<div class="ui-card"><div class="section-heading">Patient'
        " Directory</div>",
        unsafe_allow_html=True,
    )
    search_q = st.text_input(
        "🔍 Filter directory by Name, Patient ID, or Phone",
        placeholder="Type to search...",
    )
    filtered_df = patients_display.copy()
    if search_q.strip():
      q = search_q.strip().lower()
      filtered_df = filtered_df[
          filtered_df.apply(
              lambda r: any(q in str(val).lower() for val in r.values), axis=1
          )
      ]
    st.caption(f"Showing {len(filtered_df)} of {len(patients_display)} records")
    st.dataframe(filtered_df, width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# 3. DAILY TREATMENT LOG & REASSESSMENT
# =====================================================================
elif menu == "Daily Treatment Log":
  pid_col = col_val(patients_all, ["patient_id", "Patient_ID"])
  name_col = col_val(patients_all, ["name", "Name"])

  if patients_all.empty or not pid_col:
    st.warning("Register a patient first under **Patient Registration**.")
  else:
    patient_ids, fmt_fn = format_patient_selector(
        patients_all, pid_col, name_col
    )
    log_patient = st.selectbox(
        "Select Patient", patient_ids, format_func=fmt_fn, key="log_p"
    )
    render_patient_banner(patients_all, log_patient)

    completed_sessions = 0
    if not logs_all.empty:
      lp_col = col_val(logs_all, ["patient_id", "Patient_ID"])
      if lp_col:
        completed_sessions = len(logs_all[logs_all[lp_col] == log_patient])

    suggested_target = "Not set"
    if not assessments_all.empty:
      ap_col = col_val(assessments_all, ["patient_id", "Patient_ID"])
      dur_col = col_val(
          assessments_all, ["suggested_duration", "Suggested_Duration"]
      )
      if ap_col and dur_col:
        p_a = assessments_all[assessments_all[ap_col] == log_patient]
        if not p_a.empty:
          suggested_target = p_a.iloc[-1][dur_col]

    m1, m2 = st.columns(2)
    m1.metric("Sessions Logged", completed_sessions)
    m2.metric("Suggested Plan", suggested_target)

    with st.form("daily_log_form"):
      st.markdown("### Log Session & Quick Reassessment")
      c1, c2 = st.columns(2)
      with c1:
        log_date = st.date_input("Session Date", datetime.date.today())
      with c2:
        current_vas = st.slider(
            "Current Session NPRS (0–10)", 0, 10, 3, key="cur_v"
        )

      treatment_given = st.text_area(
          "Treatment Provided (Electrotherapy, Manual Therapy, Exercise"
          " Sets/Reps)"
      )
      reassessment_note = st.text_input(
          "Reassessment / Key ROM or Strength Note (Optional)"
      )
      notes = st.text_area("Therapist Progress & Next-Session Notes")

      submit_log = st.form_submit_button("Save Daily Log")
      if submit_log:
        full_notes = notes.strip()
        if reassessment_note.strip():
          full_notes = (
              f"[Reassessment: {reassessment_note.strip()}] {full_notes}".strip()
          )

        log_dict = {
            "patient_id": log_patient,
            "session_date": str(log_date),
            "treatment_given": treatment_given,
            "current_vas": int(current_vas),
            "notes": full_notes,
        }
        save_data("daily_logs", log_dict)
        st.success("Daily treatment log saved.")
        st.rerun()

    if not logs_all.empty:
      lp_col = col_val(logs_all, ["patient_id", "Patient_ID"])
      if lp_col:
        p_logs = logs_all[logs_all[lp_col] == log_patient]
        if not p_logs.empty:
          st.markdown(
              '<div class="ui-card"><div class="section-heading">Session'
              " History</div>",
              unsafe_allow_html=True,
          )
          st.dataframe(p_logs, width="stretch", hide_index=True)
          st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# 4. PROGRESS DASHBOARD & CLINICAL SUMMARY
# =====================================================================
elif menu == "Progress & Summary":
  pid_col = col_val(patients_all, ["patient_id", "Patient_ID"])
  name_col = col_val(patients_all, ["name", "Name"])

  if patients_all.empty or not pid_col:
    st.warning("No patient records available.")
  else:
    patient_ids, fmt_fn = format_patient_selector(
        patients_all, pid_col, name_col
    )
    dash_patient = st.selectbox(
        "Select Patient", patient_ids, format_func=fmt_fn, key="dash_p"
    )
    render_patient_banner(patients_all, dash_patient)

    p_logs = pd.DataFrame()
    if not logs_all.empty:
      lp_col = col_val(logs_all, ["patient_id", "Patient_ID"])
      if lp_col:
        p_logs = logs_all[logs_all[lp_col] == dash_patient].copy()

    p_asm = pd.DataFrame()
    if not assessments_all.empty:
      ap_col = col_val(assessments_all, ["patient_id", "Patient_ID"])
      if ap_col:
        p_asm = assessments_all[assessments_all[ap_col] == dash_patient].copy()

    k1, k2, k3 = st.columns(3)
    k1.metric("Assessments", len(p_asm))
    k2.metric("Sessions Logged", len(p_logs))

    vas_col = col_val(p_logs, ["current_vas", "Current_VAS"])
    if not p_logs.empty and vas_col:
      p_logs[vas_col] = pd.to_numeric(p_logs[vas_col], errors="coerce")
      valid_vas = p_logs[vas_col].dropna()
      latest_vas = valid_vas.iloc[-1] if not valid_vas.empty else "N/A"
      first_vas = valid_vas.iloc[0] if not valid_vas.empty else "N/A"
      delta_txt = (
          f"{int(latest_vas - first_vas):+d} vs baseline"
          if isinstance(latest_vas, (int, float))
          and isinstance(first_vas, (int, float))
          else None
      )
      k3.metric("Latest NPRS", latest_vas, delta=delta_txt)
    else:
      k3.metric("Latest NPRS", "N/A")

    tab_chart, tab_records, tab_export = st.tabs(
        ["📈 Pain Trend", "🗂️ Records", "📄 Clinical Summary"]
    )

    with tab_chart:
      date_col = col_val(p_logs, ["session_date", "Session_Date"])
      if p_logs.empty or not date_col or not vas_col:
        st.info(
            "No session logs recorded yet for this patient to plot NPRS progress."
        )
      else:
        fig = px.line(
            p_logs,
            x=date_col,
            y=vas_col,
            markers=True,
            title=f"NPRS Pain Score Trend — {dash_patient}",
            labels={date_col: "Session Date", vas_col: "NPRS Score (0–10)"},
        )
        fig.update_traces(
            line_color="#1B365D", marker=dict(color="#F47920", size=9)
        )
        st.plotly_chart(fig, width="stretch")

    with tab_records:
      st.markdown("**Assessments**")
      if not p_asm.empty:
        st.dataframe(p_asm, width="stretch", hide_index=True)
      else:
        st.caption("No assessments recorded.")

      st.markdown("**Daily Treatment Logs**")
      if not p_logs.empty:
        st.dataframe(p_logs, width="stretch", hide_index=True)
      else:
        st.caption("No daily logs recorded.")

    with tab_export:
      p_row = (
          patients_all[patients_all[pid_col] == dash_patient].iloc[0].to_dict()
      )
      summary_lines = [
          "DR. GEETANJALI'S PHYSIO WORKS — CLINICAL SUMMARY",
          f"Generated On: {datetime.date.today()}",
          "-" * 50,
          f"Patient ID: {dash_patient}",
          f"Patient Profile: {p_row}",
          f"Sessions Completed: {len(p_logs)}",
          "",
          "ASSESSMENTS:",
      ]
      if not p_asm.empty:
        for _, r in p_asm.iterrows():
          summary_lines.append(str(dict(r)))
      else:
        summary_lines.append("No assessments recorded.")

      summary_lines.append("")
      summary_lines.append("DAILY TREATMENT LOGS:")
      if not p_logs.empty:
        for _, r in p_logs.iterrows():
          summary_lines.append(str(dict(r)))
      else:
        summary_lines.append("No daily logs recorded.")

      summary_text = "\n".join(str(x) for x in summary_lines)
      st.download_button(
          label="⬇️ Download Clinical Summary (.txt)",
          data=summary_text,
          file_name=(
              f"{dash_patient}_clinical_summary_{datetime.date.today()}.txt"
          ),
          mime="text/plain",
      )

      st.markdown("---")
      st.markdown("**Printable PDF Clinical Assessment Record**")
      latest_asm = p_asm.iloc[-1].to_dict() if not p_asm.empty else None

      col_pdf1, col_pdf2 = st.columns(2)
      with col_pdf1:
        filled_pdf_bytes = create_assessment_pdf(p_row, asm_row=latest_asm)
        st.download_button(
            label="📄 Download Patient Assessment PDF",
            data=filled_pdf_bytes,
            file_name=(
                f"{dash_patient}_assessment_record_{datetime.date.today()}.pdf"
            ),
            mime="application/pdf",
        )
      with col_pdf2:
        blank_pdf_bytes = create_assessment_pdf(p_row, asm_row=None)
        st.download_button(
            label="🖨️ Download Blank Printable Form (With Patient Header)",
            data=blank_pdf_bytes,
            file_name=f"{dash_patient}_blank_clinical_form.pdf",
            mime="application/pdf",
        )
