import streamlit as st
import sqlite3
import re
import pandas as pd

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
        now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,?,?)",
            (full_name, email, password, gender, profession, institution, now, now)
        )
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
<div style="margin-bottom: 20px;">
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

    st.markdown("""
<div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px;">
&copy; 2025 EinTrust. 
All rights reserved.
</div>
    """, unsafe_allow_html=True)

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
                    st.experimental_rerun()
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
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
            st.session_state["page"] = "home"
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard", "Students Data", "Courses Data", "Logout"])

    # Dashboard
    with tabs[0]:
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]

        cols = st.columns(3)
        cols[0].markdown(f"<div class='card'><div class='card-title'>{total_courses}</div><div class='card-subtitle'>Courses</div></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='card'><div class='card-title'>{total_modules}</div><div class='card-subtitle'>Modules</div></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='card'><div class='card-title'>{total_students}</div><div class='card-subtitle'>Students</div></div>", unsafe_allow_html=True)

    # Students Data
    with tabs[1]:
        st.subheader("Students Data")
        students = c.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
        if students:
            df = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
            st.dataframe(df)
        else:
            st.info("No students found.")

    # Courses Data
    with tabs[2]:
        admin_courses_modules()

    # Logout
    with tabs[3]:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()

# ---------------------------
# Admin Courses & Modules Functions
# ---------------------------
def admin_courses_modules():
    st.subheader("Courses Management")
    
    # Add new course
    with st.expander("Add New Course"):
        title = st.text_input("Course Title", key="new_course_title")
        subtitle = st.text_input("Subtitle", key="new_course_subtitle")
        description = st.text_area("Description", key="new_course_desc")
        price = st.number_input("Price (₹)", min_value=0.0, key="new_course_price")
        if st.button("Add Course", key="add_course"):
            if title:
                add_course(title, subtitle, description, price)
                st.success("Course added successfully!")
                st.experimental_rerun()
            else:
                st.error("Course title is required.")

    # Edit / Delete existing courses
    courses = get_courses()
    for course in courses:
        st.markdown(f"**{course[1]}** ({course[2]}) - Price: {'Free' if course[4]==0 else f'₹{course[4]:,.0f}'}")
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            if st.button("Edit", key=f"edit_{course[0]}"):
                st.session_state["edit_course"] = course
                st.session_state["page"] = "edit_course"
                st.experimental_rerun()
        with col2:
            if st.button("Delete", key=f"del_{course[0]}"):
                delete_course(course[0])
                st.success("Course deleted successfully!")
                st.experimental_rerun()
        with col3:
            if st.button("View Modules", key=f"view_mod_{course[0]}"):
                st.session_state["view_modules_course"] = course
                st.session_state["page"] = "admin_modules"
                st.experimental_rerun()

def page_edit_course():
    course = st.session_state.get("edit_course")
    if course:
        st.subheader(f"Edit Course: {course[1]}")
        title = st.text_input("Course Title", value=course[1])
        subtitle = st.text_input("Subtitle", value=course[2])
        description = st.text_area("Description", value=course[3])
        price = st.number_input("Price (₹)", min_value=0.0, value=course[4])
        if st.button("Update Course"):
            update_course(course[0], title, subtitle, description, price)
            st.success("Course updated successfully!")
            st.session_state.pop("edit_course")
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        if st.button("Cancel"):
            st.session_state.pop("edit_course")
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()

def page_admin_modules():
    course = st.session_state.get("view_modules_course")
    if course:
        st.subheader(f"Modules of {course[1]}")
        
        # Add module
        with st.expander("Add Module"):
            title = st.text_input("Module Title", key="mod_title")
            description = st.text_area("Description", key="mod_desc")
            module_type = st.selectbox("Type", ["Video","Document","Link"], key="mod_type")
            file = st.file_uploader("Upload File", type=["pdf","mp4","pptx"], key="mod_file")
            link = st.text_input("Link (optional)", key="mod_link")
            if st.button("Add Module"):
                file_bytes = convert_file_to_bytes(file)
                add_module(course[0], title, description, module_type, file_bytes, link)
                st.success("Module added successfully!")
                st.experimental_rerun()

        # Edit/Delete existing modules
        modules = get_modules(course[0])
        for m in modules:
            st.markdown(f"- **{m[2]}** ({m[4]})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit", key=f"edit_mod_{m[0]}"):
                    st.session_state["edit_module"] = m
                    st.session_state["page"] = "edit_module"
                    st.experimental_rerun()
            with col2:
                if st.button("Delete", key=f"del_mod_{m[0]}"):
                    delete_module(m[0])
                    st.success("Module deleted successfully!")
                    st.experimental_rerun()
        
        if st.button("Back to Courses"):
            st.session_state.pop("view_modules_course")
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()

def page_edit_module():
    module = st.session_state.get("edit_module")
    if module:
        st.subheader(f"Edit Module: {module[2]}")
        title = st.text_input("Module Title", value=module[2])
        description = st.text_area("Description", value=module[3])
        module_type = st.selectbox("Type", ["Video","Document","Link"], index=["Video","Document","Link"].index(module[4]))
        file = st.file_uploader("Upload File", type=["pdf","mp4","pptx"])
        link = st.text_input("Link (optional)", value=module[6])
        if st.button("Update Module"):
            file_bytes = convert_file_to_bytes(file) if file else module[5]
            update_module(module[0], title, description, module_type, file_bytes, link)
            st.success("Module updated successfully!")
            st.session_state.pop("edit_module")
            st.session_state["page"] = "admin_modules"
            st.experimental_rerun()
        if st.button("Cancel"):
            st.session_state.pop("edit_module")
            st.session_state["page"] = "admin_modules"
            st.experimental_rerun()

# ---------------------------
# Run Pages
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
elif st.session_state["page"] == "edit_course":
    page_edit_course()
elif st.session_state["page"] == "admin_modules":
    page_admin_modules()
elif st.session_state["page"] == "edit_module":
    page_edit_module()
