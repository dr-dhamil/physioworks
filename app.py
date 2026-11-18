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
# Replace with your actual Supabase URL & Anon Key from Project Settings > API
SUPABASE_URL = "bicpyvfotfqoftpppatd"
SUPABASE_KEY = "sb_publishable_FK0NBVBpOG-Ek9BOIqQUjQ_1Jb-fOgW"

supabase = None
try:
  if SUPABASE_URL != "YOUR_SUPABASE_URL":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    st.sidebar.success("✅ Connected to Supabase Database!")
  else:
    st.sidebar.warning(
        "ℹ️ Running in local memory mode. Add your Supabase URL & Key in"
        " `app.py` for live sync."
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
  st.header("Patient Registration & Auto-ID Generation")

  with st.form("reg_form"):
    col1, col2 = st.columns(2)
    with col1:
      name = st.text_input("Patient Full Name")
      email = st.text_input("Email Address")
      gender = st.selectbox("Gender", ["Female", "Male", "Other"])
    with col2:
      phone = st.text_input("Phone Number")
      med_history = st.text_area(
          "Medical History & Flags (Diabetes, Hypertension, Surgeries)"
      )

    submitted = st.form_submit_button("Register Patient")

    if submitted and name and phone:
      patients_df = get_data("Patients")
      counter = len(patients_df) + 1 if not patients_df.empty else 1
      patient_id = f"PW{datetime.datetime.now().strftime('%m%y')}{counter:03d}"

      patient_dict = {
          "Patient_ID": patient_id,
          "Name": name,
          "Email": email,
          "Gender": gender,
          "Phone": phone,
          "Medical_History": med_history,
          "Registration_Date": str(datetime.date.today()),
      }

      save_data("Patients", patient_dict)
      st.success(
          f"Patient registered successfully & saved to Supabase! Generated ID:"
          f" **{patient_id}**"
      )

  patients_display = get_data("Patients")
  if not patients_display.empty:
    st.subheader("Registered Patients Directory")
    st.dataframe(patients_display, use_container_width=True, hide_index=True)

# --- 2. COMPREHENSIVE CLINICAL ASSESSMENT & PROTOCOLS ---
elif menu == "Comprehensive Clinical Assessment":
  st.header("Step-by-Step Anatomical Assessment Protocols")

  patients_df = get_data("Patients")
  if patients_df.empty or "Patient_ID" not in patients_df.columns:
    st.warning("Please register at least one patient first.")
  else:
    patient_list = patients_df["Patient_ID"].tolist()
    selected_patient = st.selectbox("Select Patient ID & Name", patient_list)

    with st.form("assessment_form"):
      st.subheader("1. Affected Body Region Selection (Can select multiple)")
      body_parts = st.multiselect(
          "Select Body Part(s):",
          [
              "Cervical Spine (Neck)",
              "Lumbar Spine (Lower Back)",
              "Shoulder Complex",
              "Knee Joint",
              "Wrist & Hand",
              "Ankle & Foot",
          ],
      )

      st.subheader("2. Subjective & General Scoring")
      vas_score = st.slider("VAS Pain Scale (0 = No Pain, 10 = Max Pain)", 0, 10, 5)

      assessment_details_dict = {}
      suggested_treatments = []
      bp_str = "".join(body_parts)

      if "Cervical" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Cervical Spine Assessment Criteria")
        flex = st.text_input(
            "Cervical Flexion / Extension (Norm: 0-45° / 0-45°)"
        )
        lat = st.text_input(
            "Cervical Lateral Flexion & Rotation (Norm: 0-45° / 0-80°)"
        )
        c_tests = st.multiselect(
            "Cervical Special Tests",
            [
                "Spurling’s Test",
                "Cervical Distraction Test",
                "Bakody Sign (Shoulder Abduction Test)",
            ],
        )
        assessment_details_dict["Cervical"] = {
            "ROM": f"Flex/Ext: {flex}, Lat/Rot: {lat}",
            "Tests": c_tests,
        }
        suggested_treatments.append(
            "Cervical Traction (15 mins) + TENS + Ergonomic Posture Correction"
        )

      if "Lumbar" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Lumbar Spine Assessment Criteria")
        lum_rom = st.text_input(
            "Lumbar ROM (Forward Flexion, Extension, Side Flexion)"
        )
        l_tests = st.multiselect(
            "Lumbar Special Tests",
            ["Straight Leg Raise (SLR)", "Slump Test", "FABER (Patrick's) Test"],
        )
        assessment_details_dict["Lumbar"] = {
            "ROM": lum_rom,
            "Tests": l_tests,
        }
        suggested_treatments.append(
            "IFT + Short Wave Diathermy (SWD) + Core Stabilization Exercises"
        )

      if "Shoulder" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Shoulder Complex Assessment Criteria")
        sh_rom = st.text_input(
            "Shoulder ROM (Flexion 0-180°, Abduction 0-180°, Rotations)"
        )
        sh_tests = st.multiselect(
            "Shoulder Special Tests",
            [
                "Neer Test",
                "Hawkins-Kennedy Test",
                "Empty Can (Jobe) Test",
                "Apprehension & Relocation Test",
            ],
        )
        assessment_details_dict["Shoulder"] = {
            "ROM": sh_rom,
            "Tests": sh_tests,
        }
        suggested_treatments.append(
            "Ultrasound Therapy + Pendular Exercises + Rotator Cuff Strengthening"
        )

      if "Knee" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Knee Joint Assessment Criteria")
        kn_rom = st.text_input(
            "Knee ROM (Flexion Norm: 0-140°, Extension Norm: 0°)"
        )
        kn_tests = st.multiselect(
            "Knee Special Tests",
            [
                "Lachman Test",
                "Anterior Drawer Test",
                "Posterior Drawer Test",
                "McMurray Test",
                "Valgus / Varus Stress Test",
            ],
        )
        assessment_details_dict["Knee"] = {"ROM": kn_rom, "Tests": kn_tests}
        suggested_treatments.append(
            "Short Wave Diathermy / IFT + Quadriceps Strengthening + Patellar"
            " Mobilization"
        )

      if "Wrist" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Wrist & Hand Assessment Criteria")
        wr_rom = st.text_input(
            "Wrist ROM (Flexion 0-80°, Extension 0-70°, Deviations)"
        )
        wr_tests = st.multiselect(
            "Wrist Special Tests",
            ["Phalen’s Test", "Tinel’s Sign", "Finkelstein’s Test"],
        )
        assessment_details_dict["Wrist"] = {"ROM": wr_rom, "Tests": wr_tests}
        suggested_treatments.append(
            "Wax Bath Therapy / Ultrasound + Gentle Joint Mobilization & Ergonomics"
        )

      if "Ankle" in bp_str:
        st.markdown("---")
        st.markdown("### 🔹 Ankle & Foot Assessment Criteria")
        an_rom = st.text_input(
            "Ankle ROM (Dorsiflexion 0-20°, Plantarflexion 0-50°)"
        )
        an_tests = st.multiselect(
            "Ankle Special Tests",
            [
                "Anterior Drawer Test (ATFL)",
                "Squeeze Test (Syndesmosis)",
                "Thompson Test (Achilles Tendon)",
            ],
        )
        assessment_details_dict["Ankle"] = {"ROM": an_rom, "Tests": an_tests}
        suggested_treatments.append(
            "Contrast Bath / TENS + Proprioceptive & Balance Training"
        )

      st.markdown("---")
      st.markdown("### 🔹 General Manual Muscle Testing (MMT)")
      mmt_grade = st.selectbox(
          "Overall MMT Grading",
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
            "Assessment_ID": assessment_id,
            "Patient_ID": selected_patient,
            "Body_Parts": ", ".join(body_parts),
            "VAS_Score": vas_score,
            "Assessment_Details": (
                f"MMT: {mmt_grade} | Details: {str(assessment_details_dict)}"
            ),
            "Suggested_Treatment": " | ".join(suggested_treatments),
            "Suggested_Duration": f"{suggested_time} Sessions",
            "Therapist": therapist,
            "Date": str(datetime.date.today()),
        }

        save_data("Assessments", assessment_dict)
        st.success(
            "Assessment protocols saved and synced to Supabase for"
            f" **{selected_patient}**!"
        )

# --- 3. DAILY TREATMENT LOG ---
elif menu == "Daily Treatment Log":
  st.header("Daily Treatment Provided & Status Update")

  patients_df = get_data("Patients")
  if patients_df.empty or "Patient_ID" not in patients_df.columns:
    st.warning("No patients found in database.")
  else:
    patient_list = patients_df["Patient_ID"].tolist()
    log_patient = st.selectbox("Select Patient ID", patient_list, key="log_p")

    with st.form("daily_log_form"):
      log_date = st.date_input("Session Date", datetime.date.today())
      treatment_given = st.text_area(
          "Treatment Provided Today (e.g., IFT 15 mins, Exercise therapy)"
      )
      current_vas = st.slider(
          "Current Session VAS Pain Score", 0, 10, 3, key="cur_v"
      )
      notes = st.text_area("Therapist Progress Notes")

      submit_log = st.form_submit_button("Save Daily Log")
      if submit_log:
        log_dict = {
            "Patient_ID": log_patient,
            "Session_Date": str(log_date),
            "Treatment_Given": treatment_given,
            "Current_VAS": current_vas,
            "Notes": notes,
        }
        save_data("Daily_Logs", log_dict)
        st.success(
            "Daily treatment log saved and synced to Supabase database!"
        )

# --- 4. PATIENT PROGRESS DASHBOARD ---
elif menu == "Patient Progress Dashboard":
  st.header("Patient Improvement & Progress Analytics")

  patients_df = get_data("Patients")
  if patients_df.empty or "Patient_ID" not in patients_df.columns:
    st.warning("No patient records available for charts.")
  else:
    patient_list = patients_df["Patient_ID"].tolist()
    dash_patient = st.selectbox(
        "Select Patient ID for Graph", patient_list, key="dash_p"
    )

    logs_df = get_data("Daily_Logs")
    if logs_df.empty or "Patient_ID" not in logs_df.columns:
      st.info("No daily logs recorded yet for this patient.")
    else:
      patient_logs = logs_df[logs_df["Patient_ID"] == dash_patient]

      if patient_logs.empty:
        st.info("No daily logs recorded yet for this patient.")
      else:
        st.subheader("Pain Reduction Over Time (VAS Score Trend)")
        fig = px.line(
            patient_logs,
            x="Session_Date",
            y="Current_VAS",
            markers=True,
            title=f"Improvement Graph for Patient: {dash_patient}",
            labels={
                "Session_Date": "Date of Session",
                "Current_VAS": "VAS Pain Score (0-10)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
