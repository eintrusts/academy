import streamlit as st
import sqlite3
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------
# DB Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Courses table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL,
    views INTEGER DEFAULT 0
)''')

# Modules table
c.execute('''CREATE TABLE IF NOT EXISTS modules (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    module_type TEXT,
    file BLOB,
    link TEXT,
    views INTEGER DEFAULT 0,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)''')

# Students table
c.execute('''CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT,
    first_enrollment TEXT,
    last_login TEXT
)''')

# Student-Courses relation
c.execute('''CREATE TABLE IF NOT EXISTS student_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)''')

conn.commit()

# ---------------------------
# Utility Functions
# ---------------------------
def is_valid_email(email):
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email)

def is_valid_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

def convert_file_to_bytes(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.read()
    return None

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def get_modules(course_id):
    return c.execute("SELECT * FROM modules WHERE course_id=? ORDER BY module_id ASC", (course_id,)).fetchall()

def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment) VALUES (?,?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    student = c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
    if student:
        c.execute("UPDATE students SET last_login=? WHERE student_id=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), student[0]))
        conn.commit()
    return student

def enroll_student_in_course(student_id, course_id):
    existing = c.execute("SELECT * FROM student_courses WHERE student_id=? AND course_id=?", (student_id, course_id)).fetchone()
    if not existing:
        c.execute("INSERT INTO student_courses (student_id, course_id) VALUES (?,?)", (student_id, course_id))
        conn.commit()

def get_student_courses(student_id):
    return c.execute(
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price 
           FROM courses JOIN student_courses 
           ON courses.course_id = student_courses.course_id 
           WHERE student_courses.student_id=?''', (student_id,)).fetchall()

def add_course(title, subtitle, description, price):
    c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?,?,?,?)", (title, subtitle, description, price))
    conn.commit()
    return c.lastrowid

def update_course(course_id, title, subtitle, description, price):
    c.execute("UPDATE courses SET title=?, subtitle=?, description=?, price=? WHERE course_id=?",
              (title, subtitle, description, price, course_id))
    conn.commit()

def delete_course(course_id):
    c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
    c.execute("DELETE FROM modules WHERE course_id=?", (course_id,))
    conn.commit()

def add_module(course_id, title, description, module_type, file, link):
    c.execute("INSERT INTO modules (course_id, title, description, module_type, file, link) VALUES (?,?,?,?,?,?)",
              (course_id, title, description, module_type, file, link))
    conn.commit()

def update_module(module_id, title, description, module_type, file, link):
    c.execute("UPDATE modules SET title=?, description=?, module_type=?, file=?, link=? WHERE module_id=?",
              (title, description, module_type, file, link, module_id))
    conn.commit()

def delete_module(module_id):
    c.execute("DELETE FROM modules WHERE module_id=?", (module_id,))
    conn.commit()

# ---------------------------
# CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0;}
.stApp {background-color: #0d0f12; color: #e0e0e0;}
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > textarea,
.stNumberInput > div > input {
    background-color: #1e1e1e; color: #f5f5f5; border: 1px solid #333333; border-radius: 6px;
}
.unique-btn button {
    background-color: #4CAF50 !important; 
    color: white !important; 
    border-radius: 8px !important; 
    border: none !important; 
    padding: 12px 25px !important; 
    font-weight: bold !important;
    width: 100%;
}
.unique-btn button:hover {background-color: #45a049 !important; color: #ffffff !important;}
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc;}
.section-header {border-bottom: 1px solid #333333; padding-bottom: 8px; margin-bottom: 10px; font-size: 20px;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Display Courses
# ---------------------------
def display_courses(courses, enroll=False, student_id=None, show_modules=False, editable=False):
    if not courses:
        st.info("No courses available.")
        return
    cols = st.columns(2)
    for idx, course in enumerate(courses):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="course-card">
                <div class="course-title">{course[1]}</div>
                <div class="course-subtitle">{course[2]}</div>
                <div class="course-desc">{course[3][:150]}...</div>
                <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
            </div>
            """, unsafe_allow_html=True)
            if enroll and student_id:
                if st.button("Enroll", key=f"enroll_{course[0]}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}", use_container_width=True):
                    st.session_state["edit_course"] = course
                    st.session_state["page"] = "edit_course"
                    st.experimental_rerun()
            if show_modules:
                modules = get_modules(course[0])
                if modules:
                    st.write("Modules:")
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")

# ---------------------------
# Home Page
# ---------------------------
def page_home():
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
        <h1 style="margin:0; color:#ffffff;">EinTrust Academy</h1>
    </div>
    """, unsafe_allow_html=True)

    main_tabs = st.tabs(["Courses", "Student", "Admin"])

    with main_tabs[0]:
        st.subheader("Available Courses")
        student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)

    with main_tabs[1]:
        default_student_tab = st.session_state.get("student_tab", "Signup")
        student_tabs = st.tabs(["Signup", "Login"])
        if default_student_tab == "Signup":
            with student_tabs[0]:
                page_signup()
        else:
            with student_tabs[1]:
                page_login()
        st.session_state["student_tab"] = "Signup"

    with main_tabs[2]:
        page_admin()

    st.markdown("""
    <div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px;">
        &copy; 2025 EinTrust Academy. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# Student Signup/Login/Dashboard
# ---------------------------
def page_signup():
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            else:
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Redirecting to login...")
                    st.session_state["page"] = "home"
                    st.session_state["student_tab"] = "Login"
                    st.experimental_rerun()
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

def page_student_dashboard():
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.subheader(f"Welcome, {student[1]}")
        st.write("---")
        st.subheader("Available Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])
        st.subheader("Your Enrolled Courses")
        enrolled_courses = get_student_courses(student[0])
        display_courses(enrolled_courses, show_modules=True)
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

# ---------------------------
# Admin
# ---------------------------
def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

# ---------------------------
# Admin Dashboard Full Code
# ---------------------------
def page_admin_dashboard():
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard","Students Data","Courses Data","Logout"])

    # ------------------ Dashboard Tab ------------------
    with tabs[0]:
        st.subheader("Statistics Overview")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        most_viewed_course = c.execute("SELECT title, views FROM courses ORDER BY views DESC LIMIT 1").fetchone()
        most_viewed_module = c.execute("SELECT title, views FROM modules ORDER BY views DESC LIMIT 1").fetchone()

        cols = st.columns(4)
        cols[0].metric("Total Students", total_students)
        cols[1].metric("Total Courses", total_courses)
        cols[2].metric("Most Viewed Course", f"{most_viewed_course[0]} ({most_viewed_course[1]} views)" if most_viewed_course else "N/A")
        cols[3].metric("Most Viewed Module", f"{most_viewed_module[0]} ({most_viewed_module[1]} views)" if most_viewed_module else "N/A")

        st.subheader("Most Viewed Courses Chart")
        course_views = pd.DataFrame(c.execute("SELECT title, views FROM courses ORDER BY views DESC").fetchall(), columns=["Course","Views"])
        if not course_views.empty:
            fig = px.bar(course_views, x="Course", y="Views", color="Views", title="Most Viewed Courses", text="Views")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Most Viewed Modules Chart")
        module_views = pd.DataFrame(c.execute("SELECT title, views FROM modules ORDER BY views DESC").fetchall(), columns=["Module","Views"])
        if not module_views.empty:
            fig2 = px.bar(module_views, x="Module", y="Views", color="Views", title="Most Viewed Modules", text="Views")
            st.plotly_chart(fig2, use_container_width=True)

    # ------------------ Students Data ------------------
    with tabs[1]:
        st.subheader("Students List")
        students = pd.DataFrame(c.execute("SELECT student_id, full_name, email, first_enrollment, last_login FROM students").fetchall(),
                                columns=["ID","Student Name","Email ID","First Enrollment","Last Login"])
        st.dataframe(students, use_container_width=True)

        csv = students.to_csv(index=False).encode('utf-8')
        st.download_button("Download Students Data", data=csv, file_name="students_data.csv", mime="text/csv")

    # ------------------ Courses Data ------------------
    with tabs[2]:
        sub_tabs = st.tabs(["Add Course","Update Course"])
        with sub_tabs[0]:
            st.subheader("Add New Course")
            with st.form("add_course_form"):
                title = st.text_input("Title")
                subtitle = st.text_input("Subtitle")
                description = st.text_area("Description")
                price = st.number_input("Price", 0, 1000000)
                submitted = st.form_submit_button("Add Course")
                if submitted:
                    course_id = add_course(title, subtitle, description, price)
                    st.success("Course Added Successfully!")
                    st.session_state["edit_course"] = c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
                    st.experimental_rerun()
            if "edit_course" in st.session_state:
                course = st.session_state["edit_course"]
                st.markdown(f"### Add Modules for {course[1]}")
                with st.form("add_module_form"):
                    m_title = st.text_input("Module Title")
                    m_desc = st.text_area("Module Description")
                    m_type = st.selectbox("Module Type", ["Video","PPT","PDF","Task","Quiz"])
                    m_file = st.file_uploader("Upload File", type=None)
                    m_link = st.text_input("Or External Link (Optional)")
                    m_submitted = st.form_submit_button("Add Module")
                    if m_submitted:
                        add_module(course[0], m_title, m_desc, m_type, convert_file_to_bytes(m_file), m_link)
                        st.success("Module Added Successfully!")

        with sub_tabs[1]:
            st.subheader("Update Courses")
            courses = get_courses()
            course_choice = st.selectbox("Select Course to Update", [f"{c[0]} - {c[1]}" for c in courses])
            selected_course_id = int(course_choice.split(" - ")[0])
            course = c.execute("SELECT * FROM courses WHERE course_id=?", (selected_course_id,)).fetchone()
            with st.form("update_course_form"):
                title = st.text_input("Title", value=course[1])
                subtitle = st.text_input("Subtitle", value=course[2])
                description = st.text_area("Description", value=course[3])
                price = st.number_input("Price", value=course[4])
                update_submitted = st.form_submit_button("Update Course")
                if update_submitted:
                    update_course(course[0], title, subtitle, description, price)
                    st.success("Course Updated Successfully!")
            st.write("Modules in this Course:")
            modules = get_modules(course[0])
            for m in modules:
                with st.expander(f"{m[2]} ({m[4]})"):
                    m_new_title = st.text_input("Title", value=m[2], key=f"title_{m[0]}")
                    m_new_desc = st.text_area("Description", value=m[3], key=f"desc_{m[0]}")
                    m_new_type = st.selectbox("Module Type", ["Video","PPT","PDF","Task","Quiz"], index=["Video","PPT","PDF","Task","Quiz"].index(m[4]), key=f"type_{m[0]}")
                    m_new_file = st.file_uploader("Upload File", type=None, key=f"file_{m[0]}")
                    m_new_link = st.text_input("Or External Link", value=m[6], key=f"link_{m[0]}")
                    if st.button("Update Module", key=f"update_module_{m[0]}"):
                        update_module(m[0], m_new_title, m_new_desc, m_new_type, convert_file_to_bytes(m_new_file), m_new_link)
                        st.success("Module Updated Successfully!")
                    if st.button("Delete Module", key=f"del_module_{m[0]}"):
                        delete_module(m[0])
                        st.success("Module Deleted Successfully!")
                        st.experimental_rerun()

    # ------------------ Logout Tab ------------------
    with tabs[3]:
        if st.button("Logout Admin"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()

# ---------------------------
# Main Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "signup": page_signup()
elif st.session_state["page"] == "login": page_login()
elif st.session_state["page"] == "student_dashboard": page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard": page_admin_dashboard()
elif st.session_state["page"] == "edit_course": st.write("Edit Course Page Placeholder")
