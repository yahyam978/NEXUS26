import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# إعدادات الصفحة
st.set_page_config(page_title="Event Management App", layout="wide", page_icon="⚙️")

# ==========================================
# دالة الربط (نفس الكود السابق)
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/edit"

@st.cache_resource
def init_connection():
    secret_string = st.secrets["gcp_service_account"]
    creds_dict = json.loads(secret_string)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_or_create_worksheet(main_sheet, sheet_name, headers):
    try:
        ws = main_sheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = main_sheet.add_worksheet(title=sheet_name, rows="1000", cols=str(len(headers)))
        ws.update(values=[headers], range_name="A1")
    return ws

def load_tracking_data():
    client = init_connection()
    main_sheet = client.open_by_url(SHEET_URL)
    
    # WhatsApp Status
    ws_whatsapp = get_or_create_worksheet(main_sheet, "WhatsApp_Status", ["UID", "WhatsApp_Status"])
    whatsapp_records = ws_whatsapp.get_all_records()
    whatsapp_dict = {str(r.get("UID", "")): (str(r.get("WhatsApp_Status", "")).strip().lower() == 'true') for r in whatsapp_records}
    
    # Operations Tracker
    ops_headers = ["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]
    ws_ops = get_or_create_worksheet(main_sheet, "Operations_Tracker", ops_headers)
    ops_records = ws_ops.get_all_records()
    
    ops_dict = {}
    for r in ops_records:
        uid = str(r.get("UID", ""))
        if uid:
            ops_dict[uid] = {
                "Attendance": str(r.get("Attendance", "")).strip().lower() == 'true',
                "Catering": str(r.get("Catering", "")).strip().lower() == 'true',
                "CV_Attended": str(r.get("CV_Attended", "")).strip().lower() == 'true',
                "Mock_Attended": str(r.get("Mock_Attended", "")).strip().lower() == 'true',
                "Mentorship_Attended": str(r.get("Mentorship_Attended", ""))
            }
    return whatsapp_dict, ws_whatsapp, ops_dict, ws_ops

@st.cache_data(ttl=60)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/export?format=csv&gid=1941132713"
    df = pd.read_csv(csv_url, dtype=str)
    if 'Name - First Name' in df.columns and 'Name - Last Name' in df.columns:
        df['Full Name'] = df['Name - First Name'].fillna('') + ' ' + df['Name - Last Name'].fillna('')
    return df

df = load_data()

# ==========================================
# الصفحة الثالثة: Check-in (بدون QR)
# ==========================================
st.title("📋 استقبال وتسجيل الحضور")
search_uid = st.text_input("📝 أدخل رقم الـ UID للطالب للبدء:").strip()

if search_uid:
    user_data = df[df['UID'].fillna('').str.lower() == search_uid.lower()]
    if not user_data.empty:
        st.success("✅ تم العثور على الطالب!")
        user_dict = user_data.iloc[0].to_dict()
        
        _, _, ops_dict, ws_ops = load_tracking_data()
        user_ops = ops_dict.get(search_uid, {"Attendance": False, "Catering": False, "CV_Attended": False, "Mock_Attended": False, "Mentorship_Attended": ""})
        
        with st.form(key="ops_form"):
            st.subheader(f"👤 {user_dict.get('Full Name')}")
            new_att = st.toggle("✅ الحضور (Attendance)", value=user_ops["Attendance"])
            new_cat = st.toggle("🍔 الوجبة (Catering)", value=user_ops["Catering"])
            
            # Mentorship Topics
            mentorship_str = str(user_dict.get('Mentorship sessions', ''))
            topics = [t.strip() for t in mentorship_str.split('\n') if t.strip()]
            attended = user_ops["Mentorship_Attended"].split(" | ")
            
            selected_topics = []
            for topic in topics:
                if st.checkbox(topic, value=topic in attended):
                    selected_topics.append(topic)
            
            if st.form_submit_button("💾 حفظ"):
                ops_dict[search_uid] = {
                    "Attendance": new_att, "Catering": new_cat, "CV_Attended": False, 
                    "Mock_Attended": False, "Mentorship_Attended": " | ".join(selected_topics)
                }
                # تحديث الشيت
                ops_headers = ["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]
                data_to_upload = [ops_headers] + [[k, str(v["Attendance"]), str(v["Catering"]), str(v["CV_Attended"]), str(v["Mock_Attended"]), v["Mentorship_Attended"]] for k, v in ops_dict.items()]
                ws_ops.clear()
                ws_ops.update(values=data_to_upload, range_name="A1")
                st.success("✅ تم الحفظ بنجاح!")
    else:
        st.error("❌ لم يتم العثور على طالب بهذا الـ UID.")
