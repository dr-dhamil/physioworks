import datetime
from fpdf import FPDF
import pandas as pd
import plotly.express as px
import streamlit as st
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
        --text-muted: #64748B;
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
    return

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
          "Patient Registration",
          "Clinical Assessment",
          "Daily Treatment Log",
          "Progress & Summary",
      ],
  )
  st.markdown("---")
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
# 1. PATIENT REGISTRATION & DIRECTORY
# =====================================================================
if menu == "Patient Registration":
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
# 2. COMPREHENSIVE CLINICAL ASSESSMENT
# =====================================================================
elif menu == "Clinical Assessment":
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
    render_patient_banner(patients_all, selected_patient)

    if not assessments_all.empty:
      asm_pid_col = col_val(assessments_all, ["patient_id", "Patient_ID"])
      if asm_pid_col:
        p_asm = assessments_all[assessments_all[asm_pid_col] == selected_patient]
        if not p_asm.empty:
          with st.expander(
              f"📂 Past Assessments for {selected_patient} ({len(p_asm)})"
          ):
            st.dataframe(p_asm, width="stretch", hide_index=True)

    with st.form("assessment_form"):
      st.markdown("### 1. Body Region & Pain Profile (NPRS)")
      body_parts = st.multiselect(
          "Affected Body Region(s):",
          [
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
          ],
      )

      p1, p2, p3 = st.columns(3)
      with p1:
        nprs_rest = st.slider("NPRS at Rest (0–10)", 0, 10, 0)
      with p2:
        nprs_activity = st.slider("NPRS with Activity (0–10)", 0, 10, 5)
      with p3:
        nprs_night = st.slider("NPRS at Night (0–10)", 0, 10, 2)

      c_ir, c_gl = st.columns(2)
      with c_ir:
        irritability = st.selectbox(
            "Symptom Irritability",
            [
                "Low (Settles quickly, tolerates moderate load)",
                "Moderate (Provoked by clear activity, settles within hours)",
                "High (Easily provoked, slow to settle, night/rest symptoms)",
            ],
        )
      with c_gl:
        functional_goal = st.text_input(
            "Functional Goal / Outcome Note (e.g., NDI, ODI, KOOS, stairs)"
        )

      assessment_details_dict = {}
      suggested_treatments = []
      bp_str = "".join(body_parts)

      if "Cervical" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Cervical Spine / Neck")
        c_rom = st.text_input(
            "Cervical ROM (Flexion 45°, Extension 45°, Lateral Flexion 45°,"
            " Rotation 80°)"
        )
        c_neuro = st.text_input("Neurological Screen (C5–T1 Myotomes/Dermatomes)")
        c_tests = st.multiselect(
            "Cervical Special Tests",
            [
                "Spurling’s Test",
                "Cervical Distraction Test",
                "Upper Limb Neurodynamic Tests (ULNT)",
                "Bakody Sign",
            ],
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
        st.markdown("---")
        st.markdown("### 🔹 Thoracic Spine / Upper Back")
        t_rom = st.text_input(
            "Thoracic ROM (Flexion, Extension, Rotation, Side-Flexion)"
        )
        t_palp = st.text_input("Palpation / Costovertebral Mobility")
        assessment_details_dict["Thoracic"] = {
            "ROM": t_rom,
            "Palpation": t_palp,
        }
        suggested_treatments.append(
            "Thoracic Mobility + Scapular Stabilization + Breathing Re-education"
        )

      if "Lumbar" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Lumbar Spine / Low Back")
        l_rom = st.text_input(
            "Lumbar ROM (Flexion, Extension, Side-Glide, Rotation)"
        )
        l_neuro = st.text_input(
            "Neurological Screen (L2–S1 Myotomes, Reflexes, Neural Tension)"
        )
        l_tests = st.multiselect(
            "Lumbar Special Tests",
            [
                "Straight Leg Raise (SLR)",
                "Crossed SLR",
                "Slump Test",
                "Femoral Nerve Stretch",
            ],
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
        st.markdown("---")
        st.markdown("### 🔹 Shoulder Complex")
        sh_rom = st.text_input(
            "Shoulder ROM (Flexion 180°, Abduction 180°, ER/IR, Painful Arc)"
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
        )
        assessment_details_dict["Shoulder"] = {
            "ROM": sh_rom,
            "Tests": sh_tests,
        }
        suggested_treatments.append(
            "Rotator Cuff Strengthening + Scapular Retraction + Ultrasound"
        )

      if "Elbow" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Elbow")
        el_rom = st.text_input("Elbow Flexion/Extension & Pronation/Supination")
        el_tests = st.multiselect(
            "Elbow Special Tests",
            [
                "Cozen's / Maudsley's Test",
                "Resisted Wrist Flexion",
                "Valgus/Varus Stress Test",
            ],
        )
        assessment_details_dict["Elbow"] = {"ROM": el_rom, "Tests": el_tests}
        suggested_treatments.append(
            "Eccentric Wrist Extension/Flexion + Soft Tissue Mobilization"
        )

      if "Wrist" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Wrist & Hand")
        w_rom = st.text_input(
            "Wrist Flexion/Extension, Radial/Ulnar Deviation, Pronation/Supination"
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
        )
        assessment_details_dict["Wrist"] = {"ROM": w_rom, "Tests": w_tests}
        suggested_treatments.append(
            "Carpal Tunnel Glides + Splinting Advice + Ergonomic Correction"
        )

      if "Hip" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Hip & Groin")
        h_rom = st.text_input(
            "Hip ROM (Flexion, Extension, Abduction/Adduction, ER/IR)"
        )
        h_tests = st.multiselect(
            "Hip Special Tests",
            [
                "FADIR Test",
                "FABER (Patrick's) Test",
                "Scour Test",
                "Trendelenburg Test",
            ],
        )
        assessment_details_dict["Hip"] = {"ROM": h_rom, "Tests": h_tests}
        suggested_treatments.append(
            "Hip Abductor Strengthening + Capsule Mobilization + Single-Leg"
            " Control"
        )

      if "Knee" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Knee Joint")
        k_rom = st.text_input(
            "Knee ROM (Flexion 140°, Extension 0°, Effusion/Sweep Test)"
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
        )
        assessment_details_dict["Knee"] = {"ROM": k_rom, "Tests": k_tests}
        suggested_treatments.append(
            "Quadriceps VMO Strengthening + Patellar Mobilization + Squat"
            " Mechanics"
        )

      if "Ankle" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Ankle & Foot")
        a_rom = st.text_input(
            "Ankle Dorsiflexion/Plantarflexion, Weight-Bearing Lunge Test"
        )
        a_tests = st.multiselect(
            "Ankle Special Tests",
            [
                "Anterior Drawer (ATFL)",
                "Squeeze Test (Syndesmosis)",
                "Thompson Test (Achilles)",
            ],
        )
        assessment_details_dict["Ankle"] = {"ROM": a_rom, "Tests": a_tests}
        suggested_treatments.append(
            "Proprioceptive Balance Training + Calf Raises + Taping/Bracing"
        )

      if "TMJ" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 TMJ / Jaw")
        j_rom = st.text_input(
            "Jaw Opening (mm), Lateral Excursion, Deviation/Deflection Path"
        )
        j_tests = st.multiselect(
            "TMJ Screening",
            ["Joint Sounds / Clicking History", "Masticatory Muscle Palpation"],
        )
        assessment_details_dict["TMJ"] = {"ROM": j_rom, "Tests": j_tests}
        suggested_treatments.append(
            "Cervicogenic Posture Correction + Jaw Relaxation Drills"
        )

      st.markdown("---")
      st.markdown("### 3. MMT, Treatment Plan & Assignment")
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
      )

      if not suggested_treatments:
        suggested_treatments.append(
            "General Electrotherapy & Soft Tissue Mobilization"
        )

      st.info(f"**Suggested Plan:** {' • '.join(suggested_treatments)}")
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
        assessment_dict = {
            "assessment_id": assessment_id,
            "patient_id": selected_patient,
            "body_parts": ", ".join(body_parts) if body_parts else "General",
            "vas_score": int(nprs_activity),
            "assessment_details": (
                f"NPRS[Rest:{nprs_rest}, Act:{nprs_activity},"
                f" Night:{nprs_night}] | Irritability: {irritability} | Goal:"
                f" {functional_goal} | MMT: {mmt_grade} | Details:"
                f" {str(assessment_details_dict)}"
            ),
            "suggested_treatment": " | ".join(suggested_treatments),
            "suggested_duration": f"{suggested_time} Sessions",
            "therapist": therapist,
            "date": str(datetime.date.today()),
        }
        save_data("assessments", assessment_dict)
        st.success(f"Assessment saved under ID `{assessment_id}`.")

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
