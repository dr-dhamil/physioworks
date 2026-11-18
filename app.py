import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Dr. Geetanjali’s PhysioWorks", page_icon="🩺", layout="wide"
)

# --- CUSTOM BRANDING & CSS STYLING ---
st.markdown(
    """
    <style>
    :root {
        --primary-color: #F47920;
        --secondary-color: #1B365D;
        --background-color: #F8F9FA;
    }
    .stApp {
        background-color: #F8F9FA;
    }
    [data-testid="stSidebar"] {
        background-color: #1B365D;
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stSelectbox div {
        color: white !important;
    }
    h1, h2, h3 {
        color: #1B365D;
    }
    .stButton>button {
        background-color: #F47920;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #d66515;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR LOGO & BRANDING ---
try:
  st.sidebar.image("image_500b64.jpg", width=200)
except Exception:
  st.sidebar.info("Logo image loading...")
st.sidebar.markdown("---")

# --- SUPABASE CONNECTION SETUP ---
SUPABASE_URL = "https://bicpyvfotfqoftpppatd.supabase.co"
SUPABASE_KEY = "sb_publishable_FK0NBVBpOG-Ek9BOIqQUjQ_1Jb-fOgW"

supabase = None
try:
  if SUPABASE_URL != "https://your-project-id.supabase.co":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    st.sidebar.success("✅ Connected to Supabase Database!")
  else:
    st.sidebar.warning(
        "ℹ️ Running in local memory mode. Update Supabase URL & Key in `app.py`."
    )
except Exception as e:
  st.sidebar.error(f"Supabase connection error: {e}")

menu = st.sidebar.selectbox(
    "Clinic Navigation",
    [
        "New Patient Registration",
        "Comprehensive Clinical Assessment",
        "Daily Treatment Log",
        "Patient Progress Dashboard",
    ],
)


# Helper Functions for Supabase Database Read/Write
def get_data(table_name):
  if supabase:
    try:
      response = supabase.table(table_name).select("*").execute()
      if response.data:
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
  if table_name not in st.session_state:
    st.session_state[table_name] = pd.DataFrame()
  new_df = pd.DataFrame([row_dict])
  st.session_state[table_name] = pd.concat(
      [st.session_state[table_name], new_df], ignore_index=True
  )


st.title("🩺 Dr. Geetanjali’s PhysioWorks")
st.markdown(
    "**Physiotherapy | Osteopathy | Chiropractic** — *Get the care you"
    " deserve*"
)
st.markdown("---")

# --- 1. PATIENT REGISTRATION & AUTO-ID ---
if menu == "New Patient Registration":
  st.header("Patient Registration & Universal Assessment Framework")

  with st.form("reg_form"):
    col1, col2 = st.columns(2)
    with col1:
      name = st.text_input("Patient Full Name")
      email = st.text_input("Email Address")
      gender = st.selectbox("Gender", ["Female", "Male", "Other"])
      occupation = st.text_input("Occupation & Activity/Sport Demands")
    with col2:
      phone = st.text_input("Phone Number")
      dominant_side = st.selectbox("Dominant Side", ["Right", "Left", "Mixed"])
      referral = st.text_input("Referral Source")
      med_history = st.text_area(
          "Medical History & Red Flag Screening (Comorbidities, Surgeries,"
          " Anticoagulants, Pregnancy)"
      )

    submitted = st.form_submit_button("Register Patient")

    if submitted and name and phone:
      patients_df = get_data("patients")
      counter = len(patients_df) + 1 if not patients_df.empty else 1
      patient_id = f"PW{datetime.datetime.now().strftime('%m%y')}{counter:03d}"

      patient_dict = {
          "patient_id": patient_id,
          "name": name,
          "email": email,
          "gender": gender,
          "phone": phone,
          "medical_history": med_history,
          "registration_date": str(datetime.date.today()),
      }

      save_data("patients", patient_dict)
      st.success(
          f"Patient registered successfully & saved! Generated ID:"
          f" **{patient_id}**"
      )

  patients_display = get_data("patients")
  if not patients_display.empty:
    st.subheader("Registered Patients Directory")
    st.dataframe(patients_display, use_container_width=True, hide_index=True)

# --- 2. COMPREHENSIVE CLINICAL ASSESSMENT & PROTOCOLS ---
elif menu == "Comprehensive Clinical Assessment":
  st.header("Comprehensive Anatomical Assessment Protocols")

  patients_df = get_data("patients")
  id_col = "patient_id" if "patient_id" in patients_df.columns else "Patient_ID"

  if patients_df.empty or id_col not in patients_df.columns:
    st.warning("Please register at least one patient first.")
  else:
    patient_list = patients_df[id_col].tolist()
    selected_patient = st.selectbox("Select Patient ID & Name", patient_list)

    with st.form("assessment_form"):
      st.subheader("1. Affected Body Region Selection")
      body_parts = st.multiselect(
          "Select Body Part(s):",
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

      st.subheader("2. Pain & Irritability Recording (NPRS Scale)")
      col_p1, col_p2, col_p3 = st.columns(3)
      with col_p1:
        nprs_rest = st.slider("NPRS at Rest (0-10)", 0, 10, 0)
      with col_p2:
        nprs_activity = st.slider("NPRS with Relevant Activity (0-10)", 0, 10, 5)
      with col_p3:
        nprs_night = st.slider("NPRS at Night (0-10)", 0, 10, 2)

      assessment_details_dict = {}
      suggested_treatments = []
      bp_str = "".join(body_parts)

      # --- CERVICAL SPINE ---
      if "Cervical" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Cervical Spine / Neck Assessment")
        c_rom = st.text_input(
            "Cervical ROM (Flexion 45°, Extension 45°, Lateral Flexion 45°,"
            " Rotation 80°)"
        )
        c_neuro = st.text_input("Neurological Screen (C5-T1 Myotomes/Dermatomes)")
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

      # --- THORACIC SPINE ---
      if "Thoracic" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Thoracic Spine / Upper Back Assessment")
        t_rom = st.text_input(
            "Thoracic Flexion, Extension, Rotation, and Side-Flexion Findings"
        )
        t_palp = st.text_input(
            "Palpation / Costovertebral Joint Mobility Findings"
        )
        assessment_details_dict["Thoracic"] = {
            "ROM": t_rom,
            "Palpation": t_palp,
        }
        suggested_treatments.append(
            "Thoracic Mobility Exercises + Scapular Stabilization + Breathing"
            " Re-education"
        )

      # --- LUMBAR SPINE ---
      if "Lumbar" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Lumbar Spine / Low Back Assessment")
        l_rom = st.text_input(
            "Lumbar ROM (Flexion, Extension, Side-Glide, Rotation)"
        )
        l_neuro = st.text_input(
            "Neurological Screen (L2-S1 Myotomes, Reflexes, Slump/SLR)"
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
            "Core Stabilization Exercises + Lumbar Traction + Centralization"
            " Mechanics"
        )

      # --- SHOULDER COMPLEX ---
      if "Shoulder" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Shoulder Complex Assessment")
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
            "Rotator Cuff Strengthening + Scapular Retraction Drills +"
            " Ultrasound"
        )

      # --- ELBOW ---
      if "Elbow" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Elbow Assessment")
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

      # --- WRIST & HAND ---
      if "Wrist" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Wrist & Hand Assessment")
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

      # --- HIP & GROIN ---
      if "Hip" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Hip & Groin Assessment")
        h_rom = st.text_input(
            "Hip ROM (Flexion, Extension, Abduction/Adduction, Internal/External"
            " Rotation)"
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

      # --- KNEE JOINT ---
      if "Knee" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Knee Joint Assessment")
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

      # --- ANKLE & FOOT ---
      if "Ankle" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Ankle & Foot Assessment")
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

      # --- TMJ / JAW ---
      if "TMJ" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 TMJ / Jaw Assessment")
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
      st.markdown("### 🔹 General Manual Muscle Testing (MMT)")
      mmt_grade = st.selectbox(
          "Overall MMT Grading Scale",
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

      st.subheader("3. Suggestive Treatment & Duration")
      st.info(f"**🤖 Suggested Modalities:** {', '.join(suggested_treatments)}")
      suggested_time = st.number_input(
          "Suggested Total Treatment Sessions", min_value=1, value=10
      )
      therapist = st.selectbox(
          "Assign to Therapist",
          ["Dr. Geetanjali", "Dr. Rohan", "Dr. Senior Consultant"],
      )

      save_assessment = st.form_submit_button(
          "Save Assessment & Protocols to Database"
      )
      if save_assessment:
        assessment_id = f"ASM-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        assessment_dict = {
            "assessment_id": assessment_id,
            "patient_id": selected_patient,
            "body_parts": ", ".join(body_parts),
            "vas_score": nprs_activity,
            "assessment_details": (
                f"NPRS[Rest:{nprs_rest}, Act:{nprs_activity},"
                f" Night:{nprs_night}] | MMT: {mmt_grade} | Details:"
                f" {str(assessment_details_dict)}"
            ),
            "suggested_treatment": " | ".join(suggested_treatments),
            "suggested_duration": f"{suggested_time} Sessions",
            "therapist": therapist,
            "date": str(datetime.date.today()),
        }

        save_data("assessments", assessment_dict)
        st.success(
            "Comprehensive assessment protocol saved and synced to Supabase"
            f" for **{selected_patient}**!"
        )

# --- 3. DAILY TREATMENT LOG ---
elif menu == "Daily Treatment Log":
  st.header("Daily Treatment Provided & Status Update")

  patients_df = get_data("patients")
  id_col = "patient_id" if "patient_id" in patients_df.columns else "Patient_ID"

  if patients_df.empty or id_col not in patients_df.columns:
    st.warning("No patients found in database.")
  else:
    patient_list = patients_df[id_col].tolist()
    log_patient = st.selectbox("Select Patient ID", patient_list, key="log_p")

    with st.form("daily_log_form"):
      log_date = st.date_input("Session Date", datetime.date.today())
      treatment_given = st.text_area(
          "Treatment Provided Today (e.g., IFT 15 mins, Exercise therapy)"
      )
      current_vas = st.slider(
          "Current Session NPRS Pain Score", 0, 10, 3, key="cur_v"
      )
      notes = st.text_area("Therapist Progress Notes")

      submit_log = st.form_submit_button("Save Daily Log")
      if submit_log:
        log_dict = {
            "patient_id": log_patient,
            "session_date": str(log_date),
            "treatment_given": treatment_given,
            "current_vas": current_vas,
            "notes": notes,
        }
        save_data("daily_logs", log_dict)
        st.success(
            "Daily treatment log saved and synced to Supabase database!"
        )

# --- 4. PATIENT PROGRESS DASHBOARD ---
elif menu == "Patient Progress Dashboard":
  st.header("Patient Improvement & Progress Analytics")

  patients_df = get_data("patients")
  id_col = "patient_id" if "patient_id" in patients_df.columns else "Patient_ID"

  if patients_df.empty or id_col not in patients_df.columns:
    st.warning("No patient records available for charts.")
  else:
    patient_list = patients_df[id_col].tolist()
    dash_patient = st.selectbox(
        "Select Patient ID for Graph", patient_list, key="dash_p"
    )

    logs_df = get_data("daily_logs")
    date_col = (
        "session_date" if "session_date" in logs_df.columns else "Session_Date"
    )
    pat_col = "patient_id" if "patient_id" in logs_df.columns else "Patient_ID"
    vas_col = "current_vas" if "current_vas" in logs_df.columns else "Current_VAS"

    if logs_df.empty or pat_col not in logs_df.columns:
      st.info("No daily logs recorded yet for this patient.")
    else:
      patient_logs = logs_df[logs_df[pat_col] == dash_patient]

      if patient_logs.empty:
        st.info("No daily logs recorded yet for this patient.")
      else:
        st.subheader("Pain Reduction Over Time (NPRS Trend)")
        fig = px.line(
            patient_logs,
            x=date_col,
            y=vas_col,
            markers=True,
            title=f"Improvement Graph for Patient: {dash_patient}",
            labels={
                date_col: "Date of Session",
                vas_col: "NPRS Pain Score (0-10)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
