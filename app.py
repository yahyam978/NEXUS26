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
    # سحب الـ JSON من الـ Secrets وتحويله
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
        # محاولة فتح صفحة الواتساب لو موجودة
        ws_sheet = main_sheet.worksheet("WhatsApp_Status")
    except gspread.exceptions.WorksheetNotFound:
        # لو مش موجودة، الكود هيكريتها أوتوماتيك!
        ws_sheet = main_sheet.add_worksheet(title="WhatsApp_Status", rows="1000", cols="2")
        ws_sheet.update(values=[["UID", "WhatsApp_Status"]], range_name="A1")
        
    records = ws_sheet.get_all_records()
    status_dict = {}
    for r in records:
        uid = str(r.get("UID", ""))
        status = str(r.get("WhatsApp_Status", "")).strip().lower()
        if uid:
            status_dict[uid] = (status == 'true')
            
    return status_dict, ws_sheet

def load_operations_tracker():
    client = init_connection()
    main_sheet = client.open_by_url(SHEET_URL)

    try:
        # محاولة فتح صفحة الـ Operations Tracker لو موجودة
        ops_sheet = main_sheet.worksheet("Operations_Tracker")
    except gspread.exceptions.WorksheetNotFound:
        # لو مش موجودة، الكود هيكريتها أوتوماتيك!
        ops_sheet = main_sheet.add_worksheet(title="Operations_Tracker", rows="1000", cols="6")
        ops_sheet.update(
            values=[["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]],
            range_name="A1"
        )

    records = ops_sheet.get_all_records()
    ops_dict = {}
    for r in records:
        uid = str(r.get("UID", ""))
        if uid:
            ops_dict[uid] = {
                "Attendance": str(r.get("Attendance", "")).strip().lower() == 'true',
                "Catering": str(r.get("Catering", "")).strip().lower() == 'true',
                "CV_Attended": str(r.get("CV_Attended", "")).strip().lower() == 'true',
                "Mock_Attended": str(r.get("Mock_Attended", "")).strip().lower() == 'true',
                "Mentorship_Attended": str(r.get("Mentorship_Attended", "")),
            }

    return ops_dict, ops_sheet

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

    # ==========================================
    # القائمة الجانبية (Navigation)
    # ==========================================
    st.sidebar.title("📌 القائمة الرئيسية")
    page = st.sidebar.radio(
        "اختر الصفحة:",
        ["📊 لوحة البيانات (Dashboard)", "📞 قوائم التواصل (Contact Lists)", "🔍 البحث برقم الـ UID"]
    )
    st.sidebar.markdown("---")

    # ==========================================
    # الصفحة الأولى: لوحة البيانات الأساسية
    # ==========================================
    if page == "📊 لوحة البيانات (Dashboard)":
        st.title("📊 لوحة بيانات الإيفينت")
        st.sidebar.header("🔍 فلاتر الداشبورد")
        
        all_univs = sorted(list(df["University"].dropna().unique()))
        all_depts = sorted(list(df["department"].dropna().unique()))
        all_years = sorted(list(df["Graduation year"].dropna().unique()))
        all_activities = get_unique_elements("Activity")
        all_topics = get_unique_elements("Mentorship sessions")
        all_cv_windows = get_unique_elements("CV screening time")
        all_mock_windows = get_unique_elements("Mock interview")

        sel_act = st.sidebar.multiselect("النشاط الأساسي", all_activities)
        sel_topic = st.sidebar.multiselect("نافذة/موضوع Mentorship", all_topics)
        sel_cv = st.sidebar.multiselect("نافذة CV Screening", all_cv_windows)
        sel_mock = st.sidebar.multiselect("نافذة Mock Interview", all_mock_windows)
        sel_univ = st.sidebar.multiselect("الجامعة", all_univs)
        sel_dept = st.sidebar.multiselect("القسم", all_depts)
        sel_year = st.sidebar.multiselect("الدفعة", all_years)

        filtered_df = df.copy()

        if sel_univ:
            filtered_df = filtered_df[filtered_df["University"].isin(sel_univ)]
        if sel_dept:
            filtered_df = filtered_df[filtered_df["department"].isin(sel_dept)]
        if sel_year:
            filtered_df = filtered_df[filtered_df["Graduation year"].isin(sel_year)]
        if sel_act:
            filtered_df = filtered_df[filtered_df['Activity'].fillna('').apply(lambda x: any(item in x for item in sel_act))]
        if sel_topic:
            filtered_df = filtered_df[filtered_df['Mentorship sessions'].fillna('').apply(lambda x: any(item in x for item in sel_topic))]
        if sel_cv:
            filtered_df = filtered_df[filtered_df['CV screening time'].fillna('').apply(lambda x: any(item in x for item in sel_cv))]
        if sel_mock:
            filtered_df = filtered_df[filtered_df['Mock interview'].fillna('').apply(lambda x: any(item in x for item in sel_mock))]

        st.metric(label="👥 إجمالي الحضور الكلي (بناءً على الفلاتر المختارة)", value=len(filtered_df))
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("🎯 الحضور في الأنشطة الأساسية")
            act_counts = filtered_df['Activity'].dropna().str.split('\n').explode().str.strip()
            act_counts = act_counts[act_counts != ""].value_counts().reset_index()
            act_counts.columns = ["النشاط", "العدد"]
            st.dataframe(act_counts, hide_index=True, use_container_width=True)

            st.subheader("🏛️ الحضور من كل قسم")
            dept_counts = filtered_df['department'].dropna().value_counts().reset_index()
            dept_counts.columns = ["القسم", "العدد"]
            st.dataframe(dept_counts, hide_index=True, use_container_width=True)

        with col2:
            st.subheader("🎓 الحضور من كل جامعة")
            univ_counts = filtered_df['University'].dropna().value_counts().reset_index()
            univ_counts.columns = ["الجامعة", "العدد"]
            st.dataframe(univ_counts, hide_index=True, use_container_width=True)

        with col3:
            st.subheader("📅 الحضور من كل دفعة")
            year_counts = filtered_df['Graduation year'].dropna().value_counts().reset_index()
            year_counts.columns = ["الدفعة", "العدد"]
            st.dataframe(year_counts, hide_index=True, use_container_width=True)

        st.markdown("---")
        st.header("⏳ تفاصيل نوافذ الأنشطة (Sessions & Windows)")

        col4, col5, col6 = st.columns(3)
        with col4:
            st.subheader("💡 نوافذ Mentorship")
            mentor_counts = filtered_df['Mentorship sessions'].dropna().str.split('\n').explode().str.strip()
            mentor_counts = mentor_counts[mentor_counts != ""].value_counts().reset_index()
            mentor_counts.columns = ["الموضوع", "العدد"]
            st.dataframe(mentor_counts, hide_index=True, use_container_width=True)

        with col5:
            st.subheader("📝 نوافذ CV Screening")
            cv_counts = filtered_df['CV screening time'].dropna().str.split('\n').explode().str.strip()
            cv_counts = cv_counts[cv_counts != ""].value_counts().reset_index()
            cv_counts.columns = ["النافذة", "العدد"]
            st.dataframe(cv_counts, hide_index=True, use_container_width=True)

        with col6:
            st.subheader("🤝 نوافذ Mock Interview")
            mock_counts = filtered_df['Mock interview'].dropna().str.split('\n').explode().str.strip()
            mock_counts = mock_counts[mock_counts != ""].value_counts().reset_index()
            mock_counts.columns = ["النافذة", "العدد"]
            st.dataframe(mock_counts, hide_index=True, use_container_width=True)

    # ==========================================
    # الصفحة الثانية: قوائم التواصل التفاعلية المربوطة بجوجل
    # ==========================================
    elif page == "📞 قوائم التواصل (Contact Lists)":
        st.title("📞 استخراج قوائم التواصل")
        st.markdown("اختر النشاط والنافذة. التعديلات هنا تُحفظ تلقائياً في الشيت!")

        col1, col2 = st.columns(2)
        with col1:
            activity_type = st.selectbox("اختر النشاط:", ["CV screening", "Mock interview", "Mentorship sessions"])
            
        with col2:
            if activity_type == "CV screening": target_column = "CV screening time"
            elif activity_type == "Mock interview": target_column = "Mock interview"
            else: target_column = "Mentorship sessions"
                
            options = get_unique_elements(target_column)
            selected_window = st.selectbox("اختر النافذة الزمنية / الموضوع:", options)

        if selected_window:
            contact_df = df[df[target_column].fillna('').str.contains(selected_window, regex=False)].copy()
            st.success(f"تم العثور على {len(contact_df)} شخص.")
            
            # جلب حالة الواتساب من جوجل شيتس
            with st.spinner('جاري مزامنة البيانات مع جوجل شيتس...'):
                status_dict, ws_sheet = load_whatsapp_status()
            
            contact_df['WhatsApp ✅'] = contact_df['UID'].map(lambda uid: status_dict.get(str(uid), False))
            display_cols = ["UID", "Full Name", "Phone Number", "University", "WhatsApp ✅"]
            display_cols = [col for col in display_cols if col in contact_df.columns]
            
            # جدول تفاعلي للتعديل
            edited_df = st.data_editor(
                contact_df[display_cols],
                hide_index=True,
                use_container_width=True,
                disabled=["UID", "Full Name", "Phone Number", "University"], 
                key=f"editor_{selected_window}"
            )
            
            has_changed = False
            for index, row in edited_df.iterrows():
                uid = str(row['UID'])
                is_in_whatsapp = row['WhatsApp ✅']
                if status_dict.get(uid, False) != is_in_whatsapp:
                    status_dict[uid] = is_in_whatsapp
                    has_changed = True
                    
            # لو حصل تغيير، نرفع الداتا الجديدة لجوجل شيتس
            if has_changed:
                with st.spinner("جاري حفظ التغييرات في الشيت..."):
                    # تجهيز البيانات للرفع
                    data_to_upload = [["UID", "WhatsApp_Status"]] + [[k, str(v)] for k, v in status_dict.items()]
                    ws_sheet.clear()
                    ws_sheet.update(values=data_to_upload, range_name="A1")
                st.success("✅ تم حفظ التغيير بنجاح في Google Sheets!")

    # ==========================================
    # الصفحة الثالثة: البحث بالـ UID
    # ==========================================
    elif page == "🔍 البحث برقم الـ UID":
        st.title("🔍 البحث في قاعدة البيانات")
        search_uid = st.text_input("📝 أدخل رقم الـ UID الخاص بالطالب (مثال: CLN260012):").strip()
        
        if search_uid:
            user_data = df[df['UID'].fillna('').str.lower() == search_uid.lower()]
            
            if not user_data.empty:
                st.success("✅ تم العثور على الطالب!")
                user_dict = user_data.iloc[0].to_dict()
                
                # جلب حالة الواتساب من جوجل شيتس
                status_dict, _ = load_whatsapp_status()
                in_whatsapp = "✅ تمت الإضافة" if status_dict.get(search_uid, False) else "❌ لم يتم الإضافة بعد"

                st.subheader(f"👤 بيانات: {user_dict.get('Full Name', 'غير متوفر')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📌 المعلومات الأساسية")
                    st.write(f"**رقم الهاتف:** {user_dict.get('Phone Number', 'N/A')}")
                    st.write(f"**الإيميل:** {user_dict.get('Email', 'N/A')}")
                    st.write(f"**الجامعة:** {user_dict.get('University', 'N/A')}")
                    st.write(f"**القسم:** {user_dict.get('department', 'N/A')}")
                    
                    st.markdown("---")
                    st.write(f"**حالة جروب الواتساب:** {in_whatsapp}")
                
                with col2:
                    st.markdown("### 🎯 الأنشطة المسجلة")
                    st.write(f"**CV Screening:**\n{user_dict.get('CV screening time', 'لم يسجل')}")
                    st.markdown("---")
                    st.write(f"**Mock Interview:**\n{user_dict.get('Mock interview', 'لم يسجل')}")
                    st.markdown("---")
                    st.write(f"**Mentorship Sessions:**\n{user_dict.get('Mentorship sessions', 'لم يسجل')}")

                # ==========================================
                # نظام تسجيل العمليات (Operations Tracker)
                # ==========================================
                st.markdown("---")
                st.header("📋 تسجيل العمليات (Operations Tracker)")

                actual_uid = str(user_dict.get('UID', search_uid))

                with st.spinner('جاري مزامنة بيانات العمليات مع جوجل شيتس...'):
                    ops_dict, ops_sheet = load_operations_tracker()

                current_ops = ops_dict.get(actual_uid, {
                    "Attendance": False,
                    "Catering": False,
                    "CV_Attended": False,
                    "Mock_Attended": False,
                    "Mentorship_Attended": ""
                })

                # استخراج مواضيع الـ Mentorship الخاصة بالطالب من عموده
                mentorship_raw = user_dict.get('Mentorship sessions', '')
                student_topics = [t.strip() for t in str(mentorship_raw).split('\n') if t.strip()]

                attended_raw = current_ops.get("Mentorship_Attended", "")
                attended_topics = [t.strip() for t in attended_raw.split(',') if t.strip()] if attended_raw else []

                with st.form(key=f"ops_form_{actual_uid}"):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        attendance_val = st.toggle("✅ الحضور (Attendance)", value=current_ops.get("Attendance", False))
                    with col_b:
                        catering_val = st.toggle("🍽️ استلام الوجبة (Catering)", value=current_ops.get("Catering", False))
                    with col_c:
                        cv_val = st.toggle("📝 حضور CV Screening", value=current_ops.get("CV_Attended", False))
                    with col_d:
                        mock_val = st.toggle("🤝 حضور Mock Interview", value=current_ops.get("Mock_Attended", False))

                    st.markdown("#### 💡 مواضيع الـ Mentorship")
                    selected_mentorship_topics = []
                    if student_topics:
                        m_cols = st.columns(min(len(student_topics), 3))
                        for i, topic in enumerate(student_topics):
                            with m_cols[i % len(m_cols)]:
                                checked = st.checkbox(
                                    topic,
                                    value=(topic in attended_topics),
                                    key=f"mentor_{actual_uid}_{i}"
                                )
                                if checked:
                                    selected_mentorship_topics.append(topic)
                    else:
                        st.info("لا توجد مواضيع Mentorship مسجلة لهذا الطالب.")

                    submitted = st.form_submit_button("💾 حفظ الحضور والأنشطة")

                if submitted:
                    ops_dict[actual_uid] = {
                        "Attendance": attendance_val,
                        "Catering": catering_val,
                        "CV_Attended": cv_val,
                        "Mock_Attended": mock_val,
                        "Mentorship_Attended": ", ".join(selected_mentorship_topics)
                    }

                    with st.spinner("جاري حفظ البيانات في Google Sheets..."):
                        header = ["UID", "Attendance", "Catering", "CV_Attended", "Mock_Attended", "Mentorship_Attended"]
                        data_to_upload = [header]
                        for uid, vals in ops_dict.items():
                            data_to_upload.append([
                                uid,
                                str(vals["Attendance"]),
                                str(vals["Catering"]),
                                str(vals["CV_Attended"]),
                                str(vals["Mock_Attended"]),
                                vals["Mentorship_Attended"],
                            ])
                        ops_sheet.clear()
                        ops_sheet.update(values=data_to_upload, range_name="A1")

                    st.success("✅ تم حفظ بيانات الحضور والأنشطة بنجاح في Google Sheets!")
            else:
                st.error("❌ لم يتم العثور على أي طالب بهذا الرقم. تأكد من الرقم وحاول مرة أخرى.")

except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل البيانات. تأكد من إعدادات الربط أو الرابط. التفاصيل: {e}")
