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

# Lessons table
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    content_type TEXT,
    content BLOB,
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
        .course-title {font-size: 22px; font-weight: bold;}
        .course-subtitle {font-size: 16px; color: #cccccc;}
        .course-desc {font-size: 14px; color: #bbbbbb;}
        .action-btn {
            background: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            text-align: center;
            cursor: pointer;
            border: none;
            font-size: 14px;
        }
        .action-btn:hover {background: #45a049;}
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
        cols = st.columns(2)
        for idx, course in enumerate(courses):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="course-card">
                    <div class="course-title">{course[1]}</div>
                    <div class="course-subtitle">{course[2]}</div>
                    <div class="course-desc">{course[3][:150]}...</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
                        <button class="action-btn" onclick="window.location.href='#signup'">Enroll</button>
                        <span><b>{"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

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
        submitted = st.form_submit_button("Submit")

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
    if st.button("Login", key="student_login_btn"):
        student = authenticate_student(email, password)
        if student:
            st.success("Login successful!")
            st.session_state["student"] = student
            st.session_state["page"] = "dashboard"
        else:
            st.error("Invalid credentials.")

def page_dashboard():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.write(f"Welcome, {student[1]}!")
        st.write("Your enrolled courses will appear here.")
    else:
        st.warning("Please login first.")

def page_admin():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin", key="admin_login_btn"):
        if admin_pass == "eintrust2025":
            st.success("Welcome Team")
            st.subheader("Dashboard")
            st.write("Manage courses and students here.")

            st.subheader("All Students")
            students = c.execute("SELECT full_name,email,profession,institution FROM students").fetchall()
            for s in students:
                st.write(s)

            st.subheader("All Courses")
            courses = get_courses()
            for c_row in courses:
                st.write(c_row)
        else:
            st.error("Wrong admin password.")

# ---------------------------
# MAIN NAVIGATION
# ---------------------------
tabs = st.tabs(["Home", "Signup", "Login", "Admin"])

with tabs[0]:
    page_home()
with tabs[1]:
    page_signup()
with tabs[2]:
    if "page" in st.session_state and st.session_state["page"]=="dashboard":
        page_dashboard()
    else:
        page_login()
with tabs[3]:
    page_admin()
