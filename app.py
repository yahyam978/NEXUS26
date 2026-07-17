import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="Event Dashboard", layout="wide")
st.title("📊 لوحة بيانات الإيفينت")

# دالة لجلب البيانات وتحديثها تلقائياً كل 5 دقائق
@st.cache_data(ttl=300)
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/export?format=csv&gid=1941132713"
    # قراءة كل الأعمدة كنصوص (String) لمنع تداخل الأرقام الطويلة زي البطاقة أو التليفون
    df = pd.read_csv(sheet_url, dtype=str)
    return df

try:
    df = load_data()

    # دالة مساعدة لتنظيف الخلايا التي تحتوي على أكثر من اختيار وفصلها
    def get_unique_elements(column_name):
        if column_name in df.columns:
            items = df[column_name].dropna().str.split('\n').explode().str.strip()
            return sorted(list(items[items != ""].unique()))
        return []

    # ==========================================
    # 1. إعدادات الفلاتر الجانبية (Sidebar Filters)
    # ==========================================
    st.sidebar.header("🔍 الفلاتر")
    
    all_univs = sorted(list(df["University"].dropna().unique()))
    all_depts = sorted(list(df["department"].dropna().unique()))
    all_years = sorted(list(df["Graduation year"].dropna().unique()))
    all_activities = get_unique_elements("Activity")
    all_topics = get_unique_elements("Mentorship sessions")

    sel_act = st.sidebar.multiselect("النشاط", all_activities)
    sel_topic = st.sidebar.multiselect("موضوع/نافذة الـ Mentorship", all_topics)
    sel_univ = st.sidebar.multiselect("الجامعة", all_univs)
    sel_dept = st.sidebar.multiselect("القسم", all_depts)
    sel_year = st.sidebar.multiselect("الدفعة", all_years)

    # ==========================================
    # 2. تطبيق الفلاتر على البيانات
    # ==========================================
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

    # ==========================================
    # 3. عرض الأرقام والإحصائيات
    # ==========================================
    
    # إجمالي الحضور
    st.metric(label="👥 إجمالي الحضور الكلي", value=len(filtered_df))
    st.markdown("---")

    # تقسيم الشاشة إلى 3 أعمدة لعرض الجداول بجوار بعضها
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎯 عدد الحضور في كل نشاط")
        act_counts = filtered_df['Activity'].dropna().str.split('\n').explode().str.strip()
        act_counts = act_counts[act_counts != ""].value_counts().reset_index()
        act_counts.columns = ["النشاط", "العدد"]
        st.dataframe(act_counts, hide_index=True, use_container_width=True)

        st.subheader("💡 الحضور في كل نافذة/موضوع")
        mentor_counts = filtered_df['Mentorship sessions'].dropna().str.split('\n').explode().str.strip()
        mentor_counts = mentor_counts[mentor_counts != ""].value_counts().reset_index()
        mentor_counts.columns = ["الموضوع", "العدد"]
        st.dataframe(mentor_counts, hide_index=True, use_container_width=True)

    with col2:
        st.subheader("🎓 عدد الحضور من كل جامعة")
        univ_counts = filtered_df['University'].dropna().value_counts().reset_index()
        univ_counts.columns = ["الجامعة", "العدد"]
        st.dataframe(univ_counts, hide_index=True, use_container_width=True)

        st.subheader("📅 عدد الحضور من كل دفعة")
        year_counts = filtered_df['Graduation year'].dropna().value_counts().reset_index()
        year_counts.columns = ["الدفعة", "العدد"]
        st.dataframe(year_counts, hide_index=True, use_container_width=True)

    with col3:
        st.subheader("🏛️ عدد الحضور من كل قسم")
        dept_counts = filtered_df['department'].dropna().value_counts().reset_index()
        dept_counts.columns = ["القسم", "العدد"]
        st.dataframe(dept_counts, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل البيانات. يرجى التأكد من الرابط. التفاصيل: {e}")
