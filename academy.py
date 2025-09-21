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
   completed INTEGER DEFAULT 0,
   time_spent INTEGER DEFAULT 0,
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
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price, student_courses.completed, student_courses.time_spent
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

def update_student_profile(student_id, full_name, gender, profession, institution):
    c.execute("UPDATE students SET full_name=?, gender=?, profession=?, institution=? WHERE student_id=?",
              (full_name, gender, profession, institution, student_id))
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
                if st.button("Enroll", key=f"enroll_{course[0]}_{idx}"):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if show_modules:
                modules = get_modules(course[0])
                if modules:
                    st.write("Modules:")
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")

# ---------------------------
# Pages
# ---------------------------
def render_logo_name():
    st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
<img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
<h1 style="margin:0; font-family:'Times New Roman', serif; color:#ffffff;">EinTrust Academy</h1>
</div>
""", unsafe_allow_html=True)

def render_footer():
    st.markdown("""
<div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px;">
&copy; 2025 EinTrust. All rights reserved.
</div>
""", unsafe_allow_html=True)

# --- Home, Signup, Login ---
def page_home():
    render_logo_name()
    main_tabs = st.tabs(["Courses", "Student", "Admin"])

    with main_tabs[0]:
        st.subheader("Courses")
        student_id = st.session_state.get("student")[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)

    with main_tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        with student_tabs[0]:
            page_signup()
        with student_tabs[1]:
            page_login()

    with main_tabs[2]:
        page_admin()

    render_footer()

def page_signup():
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email ID", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        gender = st.selectbox("Gender", ["Male","Female","Other"], key="signup_gender")
        profession = st.text_input("Profession", key="signup_prof")
        institution = st.text_input("Institution", key="signup_inst")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            else:
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Please login below.")
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

# ---------------------------
# Student Dashboard
# ---------------------------
def page_student_dashboard():
    render_logo_name()
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login first.")
        return

    st.header(f"Welcome, {student[1]}")
    sub_tabs = st.tabs(["Courses", "My Learning", "My Achievements", "Profile", "Logout"])

    with sub_tabs[0]:
        st.subheader("All Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])

    with sub_tabs[1]:
        st.subheader("My Learning")
        enrolled_courses = get_student_courses(student[0])
        if enrolled_courses:
            for course in enrolled_courses:
                st.markdown(f"**{course[1]}** - Progress: {course[5]*100 if course[5] else 0}%")
                modules = get_modules(course[0])
                if modules:
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")
        else:
            st.info("No courses enrolled yet.")

    with sub_tabs[2]:
        st.subheader("My Achievements")
        completed_courses = [c for c in get_student_courses(student[0]) if c[5]==1]
        if completed_courses:
            for c in completed_courses:
                st.markdown(f"**{c[1]}** - Certificate: [Download](#)")
        else:
            st.info("No achievements yet.")

    with sub_tabs[3]:
        st.subheader("Profile")
        with st.form("profile_form"):
            full_name = st.text_input("Full Name", student[1], key="prof_name")
            gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(student[4]), key="prof_gender")
            profession = st.text_input("Profession", student[5], key="prof_prof")
            institution = st.text_input("Institution", student[6], key="prof_inst")
            if st.form_submit_button("Update Profile"):
                update_student_profile(student[0], full_name, gender, profession, institution)
                st.success("Profile updated successfully!")
                st.session_state["student"] = authenticate_student(student[2], student[3])  # refresh session

    with sub_tabs[4]:
        if st.button("Logout"):
            del st.session_state["student"]
            st.session_state["page"] = "home"
            st.experimental_rerun()

    render_footer()

# ---------------------------
# Admin Pages
# ---------------------------
def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password", key="admin_pass")
    if st.button("Login as Admin", key="admin_btn"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    render_logo_name()
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard", "Students Data", "Courses Data", "Logout"])

    with tabs[0]:
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        cols = st.columns(3)
        cols[0].markdown(f"<div class='card'><div class='card-title'>{total_courses}</div><div class='card-subtitle'>Courses</div></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='card'><div class='card-title'>{total_modules}</div><div class='card-subtitle'>Modules</div></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='card'><div class='card-title'>{total_students}</div><div class='card-subtitle'>Students</div></div>", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Students Data")
        students = c.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
        if students:
            df = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
            st.dataframe(df)
        else:
            st.info("No students found.")

    with tabs[2]:
        course_subtabs = st.tabs(["Add Course", "Add Module", "Update Course", "Update Module"])
        # --- Add Course
        with course_subtabs[0]:
            st.subheader("Add Course")
            with st.form("add_course_form"):
                title = st.text_input("Course Title", key="add_course_title")
                subtitle = st.text_input("Subtitle", key="add_course_subtitle")
                desc = st.text_area("Description", key="add_course_desc")
                price = st.number_input("Price", 0.0, 100000.0, key="add_course_price")
                if st.form_submit_button("Add Course"):
                    add_course(title, subtitle, desc, price)
                    st.success("Course added successfully!")

        # --- Add Module
        with course_subtabs[1]:
            st.subheader("Add Module")
            courses = get_courses()
            if courses:
                course_options = {c[1]: c[0] for c in courses}
                selected_course = st.selectbox("Select Course", options=list(course_options.keys()), key="add_module_course")
                title = st.text_input("Module Title", key="add_module_title")
                desc = st.text_area("Description", key="add_module_desc")
                mtype = st.selectbox("Module Type", ["Video","PDF","Link","Other"], key="add_module_type")
                file = st.file_uploader("Upload File", key="add_module_file")
                link = st.text_input("Link (optional)", key="add_module_link")
                if st.button("Add Module", key="add_module_btn"):
                    add_module(course_options[selected_course], title, desc, mtype, convert_file_to_bytes(file), link)
                    st.success("Module added successfully!")

        # --- Update/Delete Course
        with course_subtabs[2]:
            st.subheader("Update / Delete Course")
            courses = get_courses()
            if courses:
                course_options = {c[1]: c[0] for c in courses}
                selected_course = st.selectbox("Select Course", list(course_options.keys()), key="upd_course_select")
                course_data = c.execute("SELECT * FROM courses WHERE course_id=?", (course_options[selected_course],)).fetchone()
                title = st.text_input("Course Title", course_data[1], key="upd_course_title")
                subtitle = st.text_input("Subtitle", course_data[2], key="upd_course_subtitle")
                desc = st.text_area("Description", course_data[3], key="upd_course_desc")
                price = st.number_input("Price", course_data[4], key="upd_course_price")
                if st.button("Update Course", key="upd_course_btn"):
                    update_course(course_options[selected_course], title, subtitle, desc, price)
                    st.success("Course updated!")
                if st.button("Delete Course", key="del_course_btn"):
                    delete_course(course_options[selected_course])
                    st.success("Course deleted!")

        # --- Update/Delete Module
        with course_subtabs[3]:
            st.subheader("Update / Delete Module")
            modules = c.execute("SELECT module_id, title FROM modules ORDER BY module_id DESC").fetchall()
            if modules:
                mod_options = {m[1]: m[0] for m in modules}
                selected_mod = st.selectbox("Select Module", list(mod_options.keys()), key="upd_module_select")
                mod_data = c.execute("SELECT * FROM modules WHERE module_id=?", (mod_options[selected_mod],)).fetchone()
                title = st.text_input("Module Title", mod_data[2], key="upd_module_title")
                desc = st.text_area("Description", mod_data[3], key="upd_module_desc")
                mtype = st.selectbox("Module Type", ["Video","PDF","Link","Other"], index=["Video","PDF","Link","Other"].index(mod_data[4]), key="upd_module_type")
                file = st.file_uploader("Upload New File (optional)", key="upd_module_file")
                link = st.text_input("Link", mod_data[6], key="upd_module_link")
                if st.button("Update Module", key="upd_module_btn"):
                    update_module(mod_options[selected_mod], title, desc, mtype, convert_file_to_bytes(file) if file else mod_data[5], link)
                    st.success("Module updated!")
                if st.button("Delete Module", key="del_module_btn"):
                    delete_module(mod_options[selected_mod])
                    st.success("Module deleted!")

    with tabs[3]:
        if st.button("Logout Admin"):
            st.session_state["page"] = "home"
            st.experimental_rerun()

    render_footer()

# ---------------------------
# Main
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

page = st.session_state["page"]
if page == "home":
    page_home()
elif page == "student_dashboard":
    page_student_dashboard()
elif page == "admin_dashboard":
    page_admin_dashboard()
