import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dr. Geetanjali’s PhysioWorks", page_icon="🩺", layout="wide"
)

st.title("🩺 Dr. Geetanjali’s PhysioWorks")
st.subheader("Clinic Management & Clinical Assessment System")

# Sidebar Navigation
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "New Patient Registration",
        "Clinical Assessment & Protocols",
        "Daily Treatment Log",
        "Patient Progress Dashboard",
    ],
)

# Initialize session state for mock database persistence during local test runs
if "patients" not in st.session_state:
  st.session_state.patients = pd.DataFrame(
      columns=["Patient_ID", "Name", "Email", "Gender", "Phone", "Medical_History"]
  )

if "assessments" not in st.session_state:
  st.session_state.assessments = pd.DataFrame(
      columns=[
          "Assessment_ID",
          "Patient_ID",
          "Body_Parts",
          "VAS_Score",
          "Suggested_Treatment",
          "Therapist",
          "Date",
      ]
  )

if "daily_logs" not in st.session_state:
  st.session_state.daily_logs = pd.DataFrame(
      columns=[
          "Patient_ID",
          "Session_Date",
          "Treatment_Given",
          "Current_VAS",
          "Notes",
      ]
  )

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
      # Auto-ID matching your sequence format (PW + YYMM + Counter)
      counter = len(st.session_state.patients) + 1
      patient_id = f"PW{datetime.datetime.now().strftime('%m%y')}{counter:03d}"

      new_patient = pd.DataFrame([{
          "Patient_ID": patient_id,
          "Name": name,
          "Email": email,
          "Gender": gender,
          "Phone": phone,
          "Medical_History": med_history,
      }])

      st.session_state.patients = pd.concat(
          [st.session_state.patients, new_patient], ignore_index=True
      )
      st.success(
          f"Patient registered successfully! Generated Patient ID: **{patient_id}**"
      )

  if not st.session_state.patients.empty:
    st.subheader("Registered Patients Directory")
    st.dataframe(
        st.session_state.patients, use_container_width=True, hide_index=True
    )

# --- 2. CLINICAL ASSESSMENT & SUGGESTIVE TREATMENT ---
elif menu == "Clinical Assessment & Protocols":
  st.header("Step-by-Step Clinical Assessment")

  if st.session_state.patients.empty:
    st.warning("Please register at least one patient first.")
  else:
    patient_list = st.session_state.patients["Patient_ID"].tolist()
    selected_patient = st.selectbox("Select Patient ID & Name", patient_list)

    with st.form("assessment_form"):
      st.subheader("1. Select Affected Body Part(s)")
      body_parts = st.multiselect(
          "Anatomical Regions:",
          [
              "Cervical Spine (Neck)",
              "Thoracic Spine",
              "Lumbar Spine (Lower Back)",
              "Right Shoulder",
              "Left Shoulder",
              "Right Knee",
              "Left Knee",
              "Wrist / Hand",
              "Ankle / Foot",
          ],
      )

      st.subheader("2. Objective & Subjective Assessment")
      vas_score = st.slider("VAS Pain Scale (0 = No Pain, 10 = Max Pain)", 0, 10, 6)
      rom_notes = st.text_area(
          "Range of Motion (ROM) & Special Test Findings (MMT / Goniometry)"
      )

      st.subheader("3. Suggestive Treatment & Duration")
      suggested_treatments = []
      if any("Cervical" in bp for bp in body_parts):
        suggested_treatments.append(
            "Cervical Traction (15 mins) + TENS + Ergonomic Correction"
        )
      if any("Lumbar" in bp for bp in body_parts):
        suggested_treatments.append(
            "IFT + Short Wave Diathermy + Core Stabilization Exercises"
        )
      if any("Knee" in bp for bp in body_parts):
        suggested_treatments.append(
            "Ultrasound Therapy + Quadriceps Strengthening + Patellar Mobilization"
        )

      if not suggested_treatments:
        suggested_treatments.append(
            "General Modality Evaluation & Soft Tissue Release"
        )

      st.info(
          f"**🤖 Suggestive Treatments:** {', '.join(suggested_treatments)}"
      )
      suggested_time = st.number_input(
          "Suggested Total Sessions", min_value=1, value=10
      )

      therapist = st.selectbox(
          "Assign to Therapist",
          ["Dr. Geetanjali", "Dr. Rohan", "Dr. Senior Resident"],
      )

      save_btn = st.form_submit_button("Save Assessment & Assign Protocol")
      if save_btn:
        assessment_id = f"ASM-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        new_assessment = pd.DataFrame([{
            "Assessment_ID": assessment_id,
            "Patient_ID": selected_patient,
            "Body_Parts": ", ".join(body_parts),
            "VAS_Score": vas_score,
            "Suggested_Treatment": " | ".join(suggested_treatments),
            "Therapist": therapist,
            "Date": str(datetime.date.today()),
        }])
        st.session_state.assessments = pd.concat(
            [st.session_state.assessments, new_assessment], ignore_index=True
        )
        st.success("Assessment saved successfully and assigned to therapist!")

# --- 3. DAILY TREATMENT LOG ---
elif menu == "Daily Treatment Log":
  st.header("Daily Treatment Provided & Status Update")

  if st.session_state.patients.empty:
    st.warning("No patients found in database.")
  else:
    patient_list = st.session_state.patients["Patient_ID"].tolist()
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
        new_log = pd.DataFrame([{
            "Patient_ID": log_patient,
            "Session_Date": str(log_date),
            "Treatment_Given": treatment_given,
            "Current_VAS": current_vas,
            "Notes": notes,
        }])
        st.session_state.daily_logs = pd.concat(
            [st.session_state.daily_logs, new_log], ignore_index=True
        )
        st.success("Daily treatment log saved successfully!")

# --- 4. PATIENT PROGRESS DASHBOARD ---
elif menu == "Patient Progress Dashboard":
  st.header("Patient Improvement & Progress Analytics")

  if st.session_state.patients.empty:
    st.warning("No patient records available for charts.")
  else:
    patient_list = st.session_state.patients["Patient_ID"].tolist()
    dash_patient = st.selectbox(
        "Select Patient ID for Graph", patient_list, key="dash_p"
    )

    patient_logs = st.session_state.daily_logs[
        st.session_state.daily_logs["Patient_ID"] == dash_patient
    ]

    if patient_logs.empty:
      st.info(
          "No daily logs recorded yet for this patient. Complete a daily log"
          " session to generate improvement curves."
      )
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