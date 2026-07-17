import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة
st.set_page_config(page_title="Event Dashboard", layout="wide")
st.title("📊 Event Registration Dashboard")

# دالة لجلب البيانات وتحديثها تلقائياً كل 5 دقائق
@st.cache_data(ttl=300)
def load_data():
    # تم وضع الـ gid الخاص بصفحة الـ Master Data
    sheet_url = "https://docs.google.com/spreadsheets/d/1TOCfWjjMPwNRk-2U1dPMB0XG_tuXnDh_MVKvU-FUqrU/export?format=csv&gid=1941132713"
    df = pd.read_csv(sheet_url)
    return df

try:
    df = load_data()
    
    # إضافة فلتر جانبي للجامعات
    st.sidebar.header("🔍 Filters")
    univ_filter = st.sidebar.multiselect(
        "Select University:",
        options=df["University"].dropna().unique(),
        default=df["University"].dropna().unique()
    )
    
    # تطبيق الفلتر على البيانات
    filtered_df = df[df["University"].isin(univ_filter)]
    
    # -- 1. إجمالي الحضور --
    st.metric(label="Total Attending", value=len(filtered_df))
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    # -- 2. إحصائيات الأنشطة (Activity) --
    with col1:
        st.subheader("🎯 People in each Activity")
        activities = filtered_df['Activity'].dropna().astype(str).str.split('\n').explode().str.strip()
        act_counts = activities.value_counts().reset_index()
        act_counts.columns = ['Activity', 'Count']
        
        fig_act = px.pie(act_counts, names='Activity', values='Count', hole=0.4)
        st.plotly_chart(fig_act, use_container_width=True)
        
    # -- 3. إحصائيات الجامعات --
    with col2:
        st.subheader("🎓 Universities")
        univ_counts = filtered_df['University'].dropna().value_counts().reset_index()
        univ_counts.columns = ['University', 'Count']
        
        fig_univ = px.bar(univ_counts, x='University', y='Count', text='Count', color='University')
        st.plotly_chart(fig_univ, use_container_width=True)
        
    st.markdown("---")
    
    # -- 4. تفاصيل الـ Mentorship Sessions --
    st.subheader("💡 Mentorship Topics (Confirmed vs Waiting List)")
    mentorships = filtered_df['Mentorship sessions'].dropna().astype(str).str.split('\n').explode().str.strip()
    mentorships = mentorships[mentorships != ""]
    mentor_counts = mentorships.value_counts().reset_index()
    mentor_counts.columns = ['Topic', 'Count']
    
    fig_mentor = px.bar(mentor_counts, x='Count', y='Topic', orientation='h', text='Count')
    fig_mentor.update_layout(yaxis={'categoryorder':'total ascending'}, height=700)
    st.plotly_chart(fig_mentor, use_container_width=True)
    
    st.markdown("---")
    
    # -- 5. معلومات الدفعات والأقسام --
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏛️ Departments")
        dept_counts = filtered_df['department'].dropna().value_counts().reset_index()
        dept_counts.columns = ['Department', 'Count']
        fig_dept = px.bar(dept_counts, x='Department', y='Count', text='Count')
        st.plotly_chart(fig_dept, use_container_width=True)
        
    with col4:
        st.subheader("📅 Graduation Years")
        year_counts = filtered_df['Graduation year'].dropna().astype(str).value_counts().reset_index()
        year_counts.columns = ['Year', 'Count']
        fig_year = px.pie(year_counts, names='Year', values='Count')
        st.plotly_chart(fig_year, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data. Please check the sheet link or column names. Details: {e}")
