import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# إعدادات الصفحة
st.set_page_config(page_title="Event Management App", layout="wide", page_icon="⚙️")

# ==========================================
# 1. إعدادات الربط مع Google Sheets API
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/edit"

@st.cache_resource
def init_connection():
    secret_string = st.secrets["gcp_service_account"]
    creds_dict = json.loads(secret_string)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_whatsapp_status():
    client = init_connection()
    main_sheet = client.open_by_url(SHEET_URL)
    try:
        ws_sheet = main_sheet.worksheet("WhatsApp_Status")
    except gspread.exceptions.WorksheetNotFound:
        ws_sheet = main_sheet.add_worksheet(title="WhatsApp_Status", rows="1000", cols="2")
        ws_sheet.update(values=[["UID", "WhatsApp_Status"]], range_name="A1")
    records = ws_sheet.get_all_records()
    status_dict = {str(r.get("UID", "")): (str(r.get("WhatsApp_Status", "")).strip().lower() == 'true') for r in records if r.get("UID", "")}
    return status_dict, ws_sheet

# دالة جديدة لجلب/إنشاء شيت العمليات
def load_ops_tracker():
    client = init_connection()
    main_sheet = client.open_by_url(SHEET_URL)
    headers = ["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]
    try:
        ws_ops = main_sheet.worksheet("Operations_Tracker")
    except gspread.exceptions.WorksheetNotFound:
        ws_ops = main_sheet.add_worksheet(title="Operations_Tracker", rows="1000", cols=str(len(headers)))
        ws_ops.update(values=[headers], range_name="A1")
    records = ws_ops.get_all_records()
    ops_dict = {str(r.get("UID", "")): r for r in records if r.get("UID", "")}
    return ops_dict, ws_ops

# ==========================================
# 2. دالة جلب البيانات الأساسية من الماستر شيت
# ==========================================
@st.cache_data(ttl=300)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/export?format=csv&gid=1941132713"
    df = pd.read_csv(csv_url, dtype=str)
    if 'Name - First Name' in df.columns and 'Name - Last Name' in df.columns:
        df['Full Name'] = df['Name - First Name'].fillna('') + ' ' + df['Name - Last Name'].fillna('')
    return df

try:
    df = load_data()
    def get_unique_elements(column_name):
        if column_name in df.columns:
            items = df[column_name].dropna().str.split('\n').explode().str.strip()
            return sorted(list(items[items != ""].unique()))
        return []

    st.sidebar.title("📌 القائمة الرئيسية")
    page = st.sidebar.radio("اختر الصفحة:", ["📊 لوحة البيانات (Dashboard)", "📞 قوائم التواصل (Contact Lists)", "🔍 البحث برقم الـ UID"])
    st.sidebar.markdown("---")

    # [باقي كود الداشبورد والكونتاكتس كما هو تماماً دون تغيير]
    # (تم اختصار الجزء هنا للتركيز على طلبك في الصفحة الثالثة)
    if page == "📊 لوحة البيانات (Dashboard)":
        st.title("📊 لوحة بيانات الإيفينت")
        # ... الكود الخاص بك كما هو ...

    elif page == "📞 قوائم التواصل (Contact Lists)":
        st.title("📞 قوائم التواصل")
        # ... الكود الخاص بك كما هو ...

    # ==========================================
    # الصفحة الثالثة المعدلة: البحث + العمليات
    # ==========================================
    elif page == "🔍 البحث برقم الـ UID":
        st.title("🔍 البحث في قاعدة البيانات")
        search_uid = st.text_input("📝 أدخل رقم الـ UID الخاص بالطالب:").strip()
        
        if search_uid:
            user_data = df[df['UID'].fillna('').str.lower() == search_uid.lower()]
            if not user_data.empty:
                st.success("✅ تم العثور على الطالب!")
                user_dict = user_data.iloc[0].to_dict()
                
                status_dict, _ = load_whatsapp_status()
                ops_dict, ws_ops = load_ops_tracker()
                user_ops = ops_dict.get(search_uid, {"Attendance": "False", "Catering": "False", "CV_Attended": "False", "Mock_Attended": "False", "Mentorship_Attended": ""})

                st.subheader(f"👤 بيانات: {user_dict.get('Full Name', 'غير متوفر')}")
                
                # إضافة الفورم الجديد
                with st.form(key="ops_form"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        new_att = st.checkbox("✅ الحضور (Attendance)", value=(str(user_ops.get("Attendance")) == 'True'))
                        new_cat = st.checkbox("🍔 استلام الوجبة (Catering)", value=(str(user_ops.get("Catering")) == 'True'))
                    
                    with col_b:
                        st.markdown("**Mentorship Sessions:**")
                        mentorship_str = str(user_dict.get('Mentorship sessions', ''))
                        topics = [t.strip() for t in mentorship_str.split('\n') if t.strip()]
                        attended_topics = str(user_ops.get("Mentorship_Attended", "")).split(" | ")
                        selected_topics = [t for t in topics if st.checkbox(t, value=(t in attended_topics))]

                    if st.form_submit_button("💾 حفظ العمليات"):
                        ops_dict[search_uid] = {
                            "UID": search_uid,
                            "Attendance": str(new_att), "Catering": str(new_cat), 
                            "CV_Attended": "False", "Mock_Attended": "False", 
                            "Mentorship_Attended": " | ".join(selected_topics)
                        }
                        data_to_upload = [["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]] + \
                                         [[v["UID"], v["Attendance"], v["Catering"], v["CV_Attended"], v["Mock_Attended"], v["Mentorship_Attended"]] for v in ops_dict.values()]
                        ws_ops.clear()
                        ws_ops.update(values=data_to_upload, range_name="A1")
                        st.success("✅ تم حفظ حالة الحضور!")
            else:
                st.error("❌ لم يتم العثور على أي طالب بهذا الرقم.")

except Exception as e:
    st.error(f"حدث خطأ. التفاصيل: {e}")
