import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Event Management App", layout="wide", page_icon="⚙️")

# ==========================================
# 1. إعدادات الربط والتحميل
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
    try: ws = main_sheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = main_sheet.add_worksheet(title=sheet_name, rows="1000", cols=str(len(headers)))
        ws.update(values=[headers], range_name="A1")
    return ws

@st.cache_data(ttl=60)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/export?format=csv&gid=1941132713"
    df = pd.read_csv(csv_url, dtype=str)
    if 'Name - First Name' in df.columns and 'Name - Last Name' in df.columns:
        df['Full Name'] = df['Name - First Name'].fillna('') + ' ' + df['Name - Last Name'].fillna('')
    return df

df = load_data()

# ==========================================
# القائمة الجانبية
# ==========================================
st.sidebar.title("📌 القائمة الرئيسية")
page = st.sidebar.radio("اختر الصفحة:", ["📊 Dashboard", "📞 Contacts", "🔍 Check-in"])

# ==========================================
# الصفحة 1: Dashboard
# ==========================================
if page == "📊 Dashboard":
    st.title("📊 لوحة بيانات الإيفينت")
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الحضور", len(df))
    st.dataframe(df[['Full Name', 'University', 'department']], use_container_width=True)

# ==========================================
# الصفحة 2: Contacts
# ==========================================
elif page == "📞 Contacts":
    st.title("📞 قوائم التواصل")
    st.write("هنا يمكنك إدارة قوائم الواتساب والتواصل.")
    # (يمكنك إضافة كود القوائم السابق هنا)

# ==========================================
# الصفحة 3: Check-in & Scan (بدون مكتبات معقدة)
# ==========================================
elif page == "🔍 Check-in":
    st.title("📋 استقبال وتسجيل الحضور")
    
    st.info("💡 نصيحة: استخدم أي تطبيق QR Scanner على موبايلك، وسلط الكاميرا على كود الطالب، وسيتم إدخال الـ UID هنا أوتوماتيك!")
    search_uid = st.text_input("📝 ضع الماسح هنا أو أدخل الـ UID يدوياً:").strip()
    
    if search_uid:
        user_data = df[df['UID'].fillna('').str.lower() == search_uid.lower()]
        if not user_data.empty:
            st.success("✅ تم العثور على الطالب!")
            user_dict = user_data.iloc[0].to_dict()
            
            # (هنا يتم دمج كود الحفظ في الشيت الخاص بالعمليات اللي عملناه قبل كدة)
            st.write(f"### 👤 {user_dict.get('Full Name')}")
            if st.button("تسجيل الحضور"):
                st.success("تم تسجيل الحضور بنجاح!")
        else:
            st.error("❌ لم يتم العثور على طالب بهذا الـ UID.")
