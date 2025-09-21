import streamlit as st
import sqlite3
import re
import pandas as pd
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution, now, now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    return c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()

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
# Page Config + CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0; font-family: 'Times New Roman', serif;}
.stApp {background-color: #0d0f12; color: #e0e0e0; font-family: 'Times New Roman', serif;}
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
.card {background:#1e1e1e; border-radius:10px; padding:20px; text-align:center; margin:10px;}
.card-title {font-size:26px; font-weight:bold; color:#4CAF50;}
.card-subtitle {font-size:16px; color:#bbbbbb;}
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
                if st.button("Enroll", key=f"enroll_{course[0]}_{idx}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}_{idx}", use_container_width=True):
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
# Pages
# ---------------------------
def page_home():
    st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px; font-family:'Times New Roman', serif;">
<img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
<h1 style="margin:0; color:#ffffff;">EinTrust Academy</h1>
</div>
    """, unsafe_allow_html=True)

    main_tabs = st.tabs(["Courses", "Student", "Admin"])

    # Courses Tab
    with main_tabs[0]:
        st.subheader("Courses")
        student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)

    # Student Tab
    with main_tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        with student_tabs[0]:
            page_signup()
        with student_tabs[1]:
            page_login()

    # Admin Tab
    with main_tabs[2]:
        page_admin()

    # Footer
    st.markdown("""
<div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px; font-family:'Times New Roman', serif;">
&copy; 2025 EinTrust. All rights reserved.
</div>
    """, unsafe_allow_html=True)

def page_signup():
    st.subheader("Student Signup")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Signup")
        if submitted:
            if not is_valid_email(email):
                st.error("Invalid Email")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 upper, 1 number, 1 special char")
            else:
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Signup successful! Redirecting to login...")
                    st.session_state["page"] = "home"
                    st.experimental_rerun()
                else:
                    st.error("Email already exists!")

def page_login():
    st.subheader("Student Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = authenticate_student(email, password)
            if user:
                st.session_state["student"] = user
                st.success(f"Welcome {user[1]}!")
                st.session_state["page"] = "home"
                st.experimental_rerun()
            else:
                st.error("Invalid credentials!")

def page_admin():
    st.subheader("Admin Login")
    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username=="admin" and password=="admin":
                st.session_state["admin"] = True
                st.session_state["page"] = "admin_dashboard"
                st.experimental_rerun()
            else:
                st.error("Invalid credentials!")

def page_admin_dashboard():
    if "admin" not in st.session_state:
        st.warning("Login as Admin first!")
        return

    st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px; font-family:'Times New Roman', serif;">
<img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="50" style="margin-right: 10px;">
<h2 style="margin:0; color:#ffffff;">Admin Dashboard</h2>
</div>
    """, unsafe_allow_html=True)

    admin_tabs = st.tabs(["Courses Management", "Modules Management", "Students Management"])

    # ---------------- Courses Management ----------------
    with admin_tabs[0]:
        st.subheader("Courses Management")
        courses = get_courses()
        display_courses(courses, editable=True)

        st.markdown("---")
        st.markdown("**Add New Course**")
        with st.form("add_course_form"):
            title = st.text_input("Title")
            subtitle = st.text_input("Subtitle")
            description = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, value=0.0)
            submitted = st.form_submit_button("Add Course")
            if submitted:
                add_course(title, subtitle, description, price)
                st.success("Course added successfully!")
                st.experimental_rerun()

    # ---------------- Modules Management ----------------
    with admin_tabs[1]:
        st.subheader("Modules Management")
        courses = get_courses()
        course_select = st.selectbox("Select Course", ["--Select--"] + [c[1] for c in courses])
        if course_select != "--Select--":
            selected_course = [c for c in courses if c[1]==course_select][0]
            modules = get_modules(selected_course[0])
            for m in modules:
                st.write(f"- {m[2]} ({m[4]})")
            st.markdown("---")
            st.markdown("**Add Module**")
            with st.form("add_module_form"):
                title = st.text_input("Module Title")
                description = st.text_area("Description")
                module_type = st.selectbox("Type", ["Video","PDF","Link"])
                file = st.file_uploader("Upload file") if module_type in ["Video","PDF"] else None
                link = st.text_input("Link") if module_type=="Link" else ""
                submitted = st.form_submit_button("Add Module")
                if submitted:
                    add_module(selected_course[0], title, description, module_type, convert_file_to_bytes(file), link)
                    st.success("Module added successfully!")
                    st.experimental_rerun()

    # ---------------- Students Management ----------------
    with admin_tabs[2]:
        st.subheader("Students Management")
        students = c.execute("SELECT * FROM students").fetchall()
        df = pd.DataFrame(students, columns=["ID","Full Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
        st.dataframe(df)

    # Footer
    st.markdown("""
<div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px; font-family:'Times New Roman', serif;">
&copy; 2025 EinTrust. All rights reserved.
</div>
    """, unsafe_allow_html=True)

# ---------------------------
# App Logic
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
