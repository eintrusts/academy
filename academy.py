import streamlit as st
import sqlite3
import re
import pandas as pd
import io
import plotly.express as px

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
        c.execute(
            "INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))",
            (full_name, email, password, gender, profession, institution))
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
st.set_page_config(page_title="EinTrust Academy", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0;}
.stApp {background-color: #0d0f12; color: #e0e0e0;}
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > textarea,
.stNumberInput > div > input,
.stFileUploader > div > input {
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
@media (max-width: 768px) {
    .course-card {padding: 10px; margin: 6px;}
    .course-title {font-size: 18px;}
    .course-subtitle {font-size: 14px;}
    .course-desc {font-size: 12px;}
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Display Courses in Cards
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
                    st.session_state["page"] = "update_course"
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
<div style="display: flex; align-items: center; margin-bottom: 20px;">
<img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
<h1 style="margin:0; color:#ffffff;">EinTrust Academy</h1>
</div>
    """, unsafe_allow_html=True)
    
    main_tabs = st.tabs(["Courses", "Student", "Admin"])
    
    # Courses Tab
    with main_tabs[0]:
        st.subheader("Available Courses")
        student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)
        
    # Student Tab
    with main_tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        if st.session_state.get("student_tab", "Signup") == "Signup":
            page_signup()
        else:
            page_login()
    
    # Admin Tab
    with main_tabs[2]:
        page_admin()

# ---------------------------
# Student Signup/Login
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
# Admin Pages
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
# Admin Dashboard
# ---------------------------
def page_admin_dashboard():
    st.header("Admin Dashboard")
    
    tabs = st.tabs(["Dashboard","Students Data","Course Data","Logout"])
    
    # Dashboard Tab
    with tabs[0]:
        st.subheader("Statistics Overview")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        most_viewed_course = c.execute("SELECT title, views FROM courses ORDER BY views DESC LIMIT 1").fetchone()
        most_viewed_course_text = f"{most_viewed_course[0]} ({most_viewed_course[1]} views)" if most_viewed_course else "N/A"
        most_viewed_module = c.execute("SELECT title, views FROM modules ORDER BY views DESC LIMIT 1").fetchone()
        most_viewed_module_text = f"{most_viewed_module[0]} ({most_viewed_module[1]} views)" if most_viewed_module else "N/A"
        cols = st.columns(4)
        cols[0].metric("Total Students", total_students)
        cols[1].metric("Total Courses", total_courses)
        cols[2].metric("Most Viewed Course", most_viewed_course_text)
        cols[3].metric("Most Viewed Module", most_viewed_module_text)

        # Example chart: students per course
        course_counts = c.execute(
            "SELECT courses.title, COUNT(student_courses.id) FROM courses LEFT JOIN student_courses ON courses.course_id=student_courses.course_id GROUP BY courses.course_id"
        ).fetchall()
        if course_counts:
            df_chart = pd.DataFrame(course_counts, columns=["Course", "Students"])
            fig = px.bar(df_chart, x="Course", y="Students", title="Students Enrolled per Course")
            st.plotly_chart(fig, use_container_width=True)

    # Students Data
    with tabs[1]:
        st.subheader("Students List")
        students = c.execute("SELECT * FROM students").fetchall()
        df_students = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
        st.dataframe(df_students[["ID","Name","Email","First Enrollment","Last Login"]])
        csv = df_students.to_csv(index=False).encode('utf-8')
        st.download_button("Download Students Data", data=csv, file_name="students.csv", mime="text/csv")

    # Course Data with Subtabs
    with tabs[2]:
        course_subtabs = st.tabs(["Add Course","Add Module","Update Course","Update Module"])

        # Add Course
        with course_subtabs[0]:
            st.markdown("### Add Course")
            with st.form("add_course_form"):
                title = st.text_input("Course Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price", min_value=0.0, step=1.0)
                if st.form_submit_button("Add Course"):
                    course_id = add_course(title, subtitle, desc, price)
                    st.success(f"Course added! ID: {course_id}")

        # Add Module
        with course_subtabs[1]:
            st.markdown("### Add Module")
            courses = get_courses()
            course_options = {f"{c[1]} (ID:{c[0]})": c[0] for c in courses}
            if courses:
                with st.form("add_module_form"):
                    selected_course = st.selectbox("Select Course", list(course_options.keys()))
                    course_id = course_options[selected_course]
                    title = st.text_input("Module Title")
                    desc = st.text_area("Description")
                    module_type = st.selectbox("Module Type", ["Video","PDF","Link"])
                    file = st.file_uploader("Upload File", type=["pdf","mp4"], key="module_file")
                    link = st.text_input("External Link (optional)")
                    if st.form_submit_button("Add Module"):
                        add_module(course_id, title, desc, module_type, convert_file_to_bytes(file), link)
                        st.success("Module added!")

        # Update Course
        with course_subtabs[2]:
            st.markdown("### Update / Delete Course")
            courses = get_courses()
            course_options = {f"{c[1]} (ID:{c[0]})": c for c in courses}
            if courses:
                selected_course = st.selectbox("Select Course", list(course_options.keys()))
                course = course_options[selected_course]
                with st.form("update_course_form"):
                    title = st.text_input("Title", value=course[1])
                    subtitle = st.text_input("Subtitle", value=course[2])
                    desc = st.text_area("Description", value=course[3])
                    price = st.number_input("Price", min_value=0.0, value=course[4])
                    submitted = st.form_submit_button("Update Course")
                    if submitted:
                        update_course(course[0], title, subtitle, desc, price)
                        st.success("Course updated!")
                    if st.form_submit_button("Delete Course"):
                        delete_course(course[0])
                        st.success("Course deleted!")
                        st.experimental_rerun()

        # Update Module
        with course_subtabs[3]:
            st.markdown("### Update / Delete Module")
            modules = c.execute("SELECT modules.module_id, modules.title, courses.title FROM modules JOIN courses ON modules.course_id=courses.course_id").fetchall()
            module_options = {f"{m[1]} (Course: {m[2]}, ID:{m[0]})": m[0] for m in modules}
            if modules:
                selected_module = st.selectbox("Select Module", list(module_options.keys()))
                module_id = module_options[selected_module]
                module = c.execute("SELECT * FROM modules WHERE module_id=?", (module_id,)).fetchone()
                with st.form("update_module_form"):
                    title = st.text_input("Module Title", value=module[2])
                    desc = st.text_area("Description", value=module[3])
                    module_type = st.selectbox("Module Type", ["Video","PDF","Link"], index=["Video","PDF","Link"].index(module[4]))
                    file = st.file_uploader("Upload File (optional)", type=["pdf","mp4"], key="update_module_file")
                    link = st.text_input("External Link", value=module[6])
                    submitted = st.form_submit_button("Update Module")
                    if submitted:
                        update_module(module_id, title, desc, module_type, convert_file_to_bytes(file) if file else module[5], link)
                        st.success("Module updated!")
                    if st.form_submit_button("Delete Module"):
                        delete_module(module_id)
                        st.success("Module deleted!")
                        st.experimental_rerun()

    # Logout Tab
    with tabs[3]:
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()

# ---------------------------
# Routing
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
