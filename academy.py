import streamlit as st
import sqlite3
import re
from PIL import Image
import io

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
    price REAL
)''')

# Students table
c.execute('''CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)''')

# Student-Course mapping
c.execute('''CREATE TABLE IF NOT EXISTS student_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER
)''')

# Lessons table
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    video_link TEXT,
    file_type TEXT,
    file_data BLOB
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

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    student = c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
    return student

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        body {background-color: #0e1117; color: #fafafa;}
        .stTabs [role="tablist"] {justify-content: center;}
        .stTabs [role="tab"] {font-size: 18px; padding: 12px;}
        .course-card {
            background: #1e1e1e;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
        }
        .course-title {font-size: 22px; font-weight: bold; color:#4CAF50;}
        .course-subtitle {font-size: 16px; color: #cccccc;}
        .course-desc {font-size: 14px; color: #bbbbbb;}
        .enroll-btn, .submit-btn {
            background: #4CAF50 !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            border: none !important;
            cursor: pointer !important;
        }
        .enroll-btn:hover, .submit-btn:hover {background: #45a049 !important;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# PAGES
# ---------------------------

def page_home():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Available Courses")
    courses = get_courses()
    if not courses:
        st.info("No courses available yet.")
    else:
        cols = st.columns(3)
        for i, course in enumerate(courses):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="course-card">
                    <div class="course-title">{course[1]}</div>
                    <div class="course-subtitle">{course[2]}</div>
                    <div class="course-desc">{course[3][:150]}...</div>
                    <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Enroll in {course[1]}", key=f"enroll_home_{course[0]}"):
                    st.session_state["page"] = "signup"

def page_signup():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Submit", use_container_width=True)

        if submitted:
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            else:
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Please login.")
                    st.session_state["page"] = "login"
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", use_container_width=True):
        student = authenticate_student(email, password)
        if student:
            st.success("Login successful!")
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
        else:
            st.error("Invalid credentials.")

def page_student_dashboard():
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login first.")
        return

    st.subheader("Available Courses")
    courses = get_courses()
    if not courses:
        st.info("No courses available yet.")
    else:
        cols = st.columns(3)
        for i, course in enumerate(courses):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="course-card">
                    <div class="course-title">{course[1]}</div>
                    <div class="course-subtitle">{course[2]}</div>
                    <div class="course-desc">{course[3][:150]}...</div>
                    <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Enroll", key=f"enroll_{course[0]}"):
                    c.execute("INSERT INTO student_courses (student_id, course_id) VALUES (?, ?)",
                              (student[0], course[0]))
                    conn.commit()
                    st.success(f"Enrolled in {course[1]} successfully!")

def page_admin():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin", use_container_width=True):
        if admin_pass == "eintrust2025":  
            st.success("Welcome Team")
            st.session_state["page"] = "admin_dashboard"
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    st.header("Admin Dashboard")
    if st.button("Logout", use_container_width=True):
        st.session_state["page"] = "home"
        return

    admin_tabs = st.tabs(["Dashboard", "All Students", "All Courses"])
    
    with admin_tabs[0]:
        st.subheader("Welcome to Admin Dashboard")
    
    with admin_tabs[1]:
        st.subheader("All Students")
        students = c.execute("SELECT full_name,email,profession,institution FROM students").fetchall()
        for s in students:
            st.write(s)

    with admin_tabs[2]:
        st.subheader("All Courses")
        courses = get_courses()
        for c_row in courses:
            st.write(c_row)

        st.subheader("Add Course")
        with st.form("add_course_form"):
            title = st.text_input("Course Title")
            subtitle = st.text_input("Course Subtitle")
            description = st.text_area("Course Description")
            price = st.number_input("Course Amount (₹)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("Add Course", use_container_width=True)
            if submitted:
                c.execute("INSERT INTO courses (title,subtitle,description,price) VALUES (?,?,?,?)",
                          (title, subtitle, description, price))
                conn.commit()
                st.success("Course added successfully!")

        st.subheader("Add Lesson")
        with st.form("add_lesson_form"):
            course_list = get_courses()
            course_options = {f"{c[1]} ({c[0]})": c[0] for c in course_list}
            course_choice = st.selectbox("Select Course", list(course_options.keys()))
            lesson_title = st.text_input("Lesson Title")
            lesson_desc = st.text_area("Lesson Description")
            video_link = st.text_input("Video Link (optional)")
            uploaded_file = st.file_uploader("Upload File (PDF/PPT)", type=["pdf", "pptx"])
            submit_lesson = st.form_submit_button("Add Lesson", use_container_width=True)

            if submit_lesson:
                file_data, file_type = None, None
                if uploaded_file:
                    file_data = uploaded_file.read()
                    file_type = uploaded_file.type
                c.execute("INSERT INTO lessons (course_id,title,description,video_link,file_type,file_data) VALUES (?,?,?,?,?,?)",
                          (course_options[course_choice], lesson_title, lesson_desc, video_link, file_type, file_data))
                conn.commit()
                st.success("Lesson added successfully!")

# ---------------------------
# MAIN NAVIGATION
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    tabs = st.tabs(["Home", "Signup", "Login", "Admin"])
    with tabs[0]:
        page_home()
    with tabs[1]:
        page_signup()
    with tabs[2]:
        page_login()
    with tabs[3]:
        page_admin()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
