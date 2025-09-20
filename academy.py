import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import datetime

# -----------------------------------
# Database Setup
# -----------------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    first_enrollment TIMESTAMP,
    last_login TIMESTAMP
)""")

c.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP,
    views INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content TEXT,
    type TEXT,
    created_at TIMESTAMP,
    views INTEGER DEFAULT 0,
    FOREIGN KEY(course_id) REFERENCES courses(id)
)""")
conn.commit()

# -----------------------------------
# Utility Functions
# -----------------------------------
def add_student(name, email, password):
    now = datetime.datetime.now()
    c.execute("INSERT INTO students (name, email, password, first_enrollment, last_login) VALUES (?, ?, ?, ?, ?)",
              (name, email, password, now, now))
    conn.commit()

def authenticate_student(email, password):
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def update_last_login(student_id):
    now = datetime.datetime.now()
    c.execute("UPDATE students SET last_login=? WHERE id=?", (now, student_id))
    conn.commit()

def add_course(title, description):
    now = datetime.datetime.now()
    c.execute("INSERT INTO courses (title, description, created_at) VALUES (?, ?, ?)",
              (title, description, now))
    conn.commit()

def get_courses():
    return c.execute("SELECT * FROM courses").fetchall()

def add_module(course_id, title, content, mtype):
    now = datetime.datetime.now()
    c.execute("INSERT INTO modules (course_id, title, content, type, created_at) VALUES (?, ?, ?, ?, ?)",
              (course_id, title, content, mtype, now))
    conn.commit()

def get_modules(course_id):
    return c.execute("SELECT * FROM modules WHERE course_id=?", (course_id,)).fetchall()

def delete_student(student_id):
    c.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()

def delete_module(module_id):
    c.execute("DELETE FROM modules WHERE id=?", (module_id,))
    conn.commit()

def get_student_data():
    return pd.read_sql("SELECT id, name, email, first_enrollment, last_login FROM students", conn)

def increment_views(table, item_id):
    c.execute(f"UPDATE {table} SET views = views + 1 WHERE id=?", (item_id,))
    conn.commit()

# -----------------------------------
# CSS Styling (Dark Professional Theme)
# -----------------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.block-container {
    padding: 2rem;
}
.card {
    display: inline-block;
    padding: 20px;
    margin: 10px;
    background: #1e1e26;
    border-radius: 10px;
    text-align: center;
    width: 220px;
    color: white;
    font-family: 'Helvetica Neue', sans-serif;
}
.card h3 {
    margin: 0;
    font-size: 28px;
    color: #4CAF50;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# Pages
# -----------------------------------
def page_home():
    st.markdown("<h1 style='text-align:center;'>EinTrust Academy</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["Courses", "Student", "Admin"])

    # Courses
    with tabs[0]:
        st.header("Available Courses")
        courses = get_courses()
        for course in courses:
            with st.expander(course[1]):
                st.write(course[2])
                increment_views("courses", course[0])  # Track views

    # Student
    with tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        with student_tabs[0]:
            with st.form("signup_form"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Signup")
                if submitted:
                    add_student(name, email, password)
                    st.success("Signup successful! Please login.")
                    st.session_state["page"] = "student_dashboard"
                    st.experimental_rerun()

        with student_tabs[1]:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    student = authenticate_student(email, password)
                    if student:
                        st.session_state["student"] = student
                        update_last_login(student[0])
                        st.session_state["page"] = "student_dashboard"
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")

    # Admin
    with tabs[2]:
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == "admin":
                st.session_state["page"] = "admin_dashboard"
                st.experimental_rerun()
            else:
                st.error("Wrong password")

    st.markdown("<center>© EinTrust Academy</center>", unsafe_allow_html=True)

def page_student_dashboard():
    st.title("Student Dashboard")
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login.")
        st.session_state["page"] = "home"
        st.experimental_rerun()

    st.subheader(f"Welcome {student[1]}")
    courses = get_courses()
    for course in courses:
        with st.expander(course[1]):
            st.write(course[2])
            modules = get_modules(course[0])
            for m in modules:
                if st.button(f"Open {m[2]} ({m[4]})", key=f"mod_{m[0]}"):
                    increment_views("modules", m[0])
                    st.info(f"Opened {m[2]} ({m[4]}): {m[3]}")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

def page_admin_dashboard():
    st.title("Admin Dashboard")
    tabs = st.tabs(["Dashboard", "Students Data", "Courses Data", "Logout"])

    # Dashboard
    with tabs[0]:
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]

        st.markdown(f"<div class='card'>Students<br><h3>{total_students}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>Courses<br><h3>{total_courses}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>Modules<br><h3>{total_modules}</h3></div>", unsafe_allow_html=True)

        df_courses = pd.read_sql("SELECT title, views FROM courses", conn)
        if not df_courses.empty:
            fig = px.bar(df_courses, x="title", y="views", title="Most Viewed Courses", color="views")
            st.plotly_chart(fig, use_container_width=True)

        df_modules = pd.read_sql("SELECT title, views FROM modules", conn)
        if not df_modules.empty:
            fig2 = px.bar(df_modules, x="title", y="views", title="Most Viewed Modules", color="views")
            st.plotly_chart(fig2, use_container_width=True)

    # Students Data
    with tabs[1]:
        df = get_student_data()
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Students Data", csv, "students.csv", "text/csv")

        for idx, row in df.iterrows():
            if st.button(f"Delete {row['name']}", key=f"delstu_{row['id']}"):
                delete_student(row['id'])
                st.success("Student deleted!")
                st.experimental_rerun()

    # Courses Data
    with tabs[2]:
        subtabs = st.tabs(["Add Course", "Update Course"])

        with subtabs[0]:
            with st.form("add_course"):
                title = st.text_input("Course Title")
                desc = st.text_area("Description")
                submitted = st.form_submit_button("Add Course")
                if submitted:
                    add_course(title, desc)
                    st.success("Course added!")

            st.subheader("Add Module")
            courses = get_courses()
            if courses:
                course_list = {c[1]: c[0] for c in courses}
                course_selected = st.selectbox("Select Course", list(course_list.keys()))
                mtitle = st.text_input("Module Title")
                mtype = st.selectbox("Type", ["Video", "PPT", "PDF", "Task", "Quiz"])
                content = st.text_area("Content / Link")
                if st.button("Add Module"):
                    add_module(course_list[course_selected], mtitle, content, mtype)
                    st.success("Module added!")

        with subtabs[1]:
            courses = get_courses()
            for course in courses:
                with st.expander(course[1]):
                    st.write(course[2])
                    modules = get_modules(course[0])
                    for m in modules:
                        st.write(f"{m[2]} ({m[4]})")
                        if st.button(f"Delete {m[2]}", key=f"delmod_{m[0]}"):
                            delete_module(m[0])
                            st.success("Module deleted!")
                            st.experimental_rerun()

    # Logout
    with tabs[3]:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()

# -----------------------------------
# Main
# -----------------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
