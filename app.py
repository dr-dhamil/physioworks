import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dr. Geetanjali’s PhysioWorks", page_icon="🩺", layout="wide"
)

# --- CUSTOM BRANDING & CSS STYLING ---
st.markdown(
    """
    <style>
    /* Primary Color Theme matching the clinic logo */
    :root {
        --primary-color: #F47920;
        --secondary-color: #1B365D;
        --background-color: #F8F9FA;
    }
    .stApp {
        background-color: #F8F9FA;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1B365D;
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stSelectbox div {
        color: white !important;
    }
    /* Headers */
    h1, h2, h3 {
        color: #1B365D;
    }
    /* Buttons */
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
st.sidebar.image(
    "image_500b64.jpg", use_column_width=True
)  # Displays your clinic logo
st.sidebar.markdown("---")


# --- GOOGLE SHEETS CONNECTION SETUP ---
@st.cache_resource
def connect_to_sheets():
  scope = [
      "https://www.spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("Dr_Geetanjalis_PhysioWorks_Live_DB")
    return sheet
  except Exception as e:
    return None


db_sheet = connect_to_sheets()

if db_sheet is None:
  st.sidebar.warning(
      "⚠️ Live Google Sheet not connected. Running in local state memory mode."
      " (Ensure `credentials.json` is uploaded)."
  )

# Navigation Menu
menu = st.sidebar.selectbox(
    "Clinic Navigation",
    [
        "New Patient Registration",
        "Comprehensive Clinical Assessment",
        "Daily Treatment Log",
        "Patient Progress Dashboard",
    ],
)


# Helper function to fetch data safely
def get_data(tab_name):
  if db_sheet:
    try:
      worksheet = db_sheet.worksheet(tab_name)
      data = worksheet.get_all_records()
      return pd.DataFrame(data)
    except Exception:
      return pd.DataFrame()
  else:
    if tab_name not in st.session_state:
      st.session_state[tab_name] = pd.DataFrame()
    return st.session_state[tab_name]


def save_data(tab_name, new_row_df):
  if db_sheet:
    try:
      worksheet = db_sheet.worksheet(tab_name)
      worksheet.append_row(new_row_df.values.tolist()[0])
    except Exception as e:
      st.error(f"Error saving to Google Sheets: {e}")
  else:
    if tab_name not in st.session_state:
      st.session_state[tab_name] = pd.DataFrame()
    st.session_state[tab_name] = pd.concat(
        [st.session_state[tab_name], new_row_df], ignore
