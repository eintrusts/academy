import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", page_icon="🎓", layout="wide")

# Custom CSS for dark theme & professional SaaS style
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
header, .stTabs [role="tablist"] {
    background-color: #1a1d24 !important;
    border-radius: 10px;
    padding: 10px;
}
.stTabs [role="tab"] {
    background-color: #2c3038;
    color: #ffffff;
    border-radius: 8px;
    padding: 10px 20px;
    margin: 5px;
    font-weight: 500;
}
.stTabs [role="tab"][aria-selected="true"] {
    background-color: #007bff;
    color: #ffffff !important;
}
.course-card {
    background-color: #1a1d24;
    border-radius: 15px;
    padding: 20px;
    margin: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
}
.enroll-btn {
    background-color: #007bff;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
}
.enroll-btn:hover {
    background-color: #0056b3;
}
.logo {
    font-size: 28px;
    font-weight: bold;
    color: #00d4ff;
}
.admin-login {
    position: fixed;
    bottom: 15px;
    right: 15px;
    background-color: #ff4757;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# DB FUNCTIONS
# ---------------------------
def init_db():
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    # Students
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    password TEXT,
                    created_at TEXT)""")
    # Courses
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    price REAL,
                    is_paid INTEGER DEFAULT 0)""")
    # Enrollments
    c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    progress INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id))""")
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# AUTH
# ---------------------------
def student_signup(name, email, password):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (name,email,password,created_at) VALUES (?,?,?,?)",
                  (name,email,hash_password(password),datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def student_login(email, password):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("SELECT student_id,name FROM students WHERE email=? AND password=?",
              (email, hash_password(password)))
    student = c.fetchone()
    conn.close()
    return student

def get_courses():
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("SELECT * FROM courses ORDER BY course_id DESC")
    data = c.fetchall()
    conn.close()
    return data

def enroll_course(student_id, course_id):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)",(student_id,course_id))
    conn.commit()
    conn.close()

# ---------------------------
# UI PAGES
# ---------------------------
def home_page():
    st.markdown('<div class="logo">🎓 EinTrust Academy</div>', unsafe_allow_html=True)

    courses = get_courses()
    if not courses:
        st.info("🚀 No courses available. Admin can add from dashboard.")
    else:
        cols = st.columns(2)
        for idx, course in enumerate(courses):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="course-card">
                    <h3>{course[1]}</h3>
                    <p>{course[2]}</p>
                    <p><b>{"Free" if course[3]==0 else f"₹{course[3]:,.0f}"}</b></p>
                    <div class="enroll-btn" onclick="window.location.href='?enroll={course[0]}'">Enroll</div>
                </div>
                """, unsafe_allow_html=True)

def signup_page():
    st.subheader("📝 Create Student Profile")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if student_signup(name,email,password):
            st.success("Profile created! Please log in.")
            st.session_state.page = "login"
        else:
            st.error("Email already registered.")

def login_page():
    st.subheader("🔑 Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = student_login(email,password)
        if student:
            st.session_state.student = student
            st.success(f"Welcome, {student[1]} 👋")
            st.session_state.page = "courses"
        else:
            st.error("Invalid credentials.")

def courses_page():
    st.subheader("📚 Available Courses")
    courses = get_courses()
    if not courses:
        st.info("No courses available.")
    else:
        for course in courses:
            st.markdown(f"""
            <div class="course-card">
                <h3>{course[1]}</h3>
                <p>{course[2]}</p>
                <p><b>{"Free" if course[3]==0 else f"₹{course[3]:,.0f}"}</b></p>
                <div class="enroll-btn">Enroll</div>
            </div>
            """, unsafe_allow_html=True)

def admin_page():
    st.subheader("🛠️ Admin Dashboard")
    password = st.text_input("Enter Admin Password", type="password")
    if password == "admin123":  # Change this
        st.success("Welcome Admin")
        st.markdown("### Add New Course")
        title = st.text_input("Course Title")
        desc = st.text_area("Course Description")
        price = st.number_input("Price (₹)", min_value=0.0)
        is_paid = 1 if price > 0 else 0
        if st.button("Add Course"):
            conn = sqlite3.connect("academy.db")
            c = conn.cursor()
            c.execute("INSERT INTO courses (title,description,price,is_paid) VALUES (?,?,?,?)",
                      (title,desc,price,is_paid))
            conn.commit()
            conn.close()
            st.success("Course added!")

        st.markdown("### All Students")
        conn = sqlite3.connect("academy.db")
        c = conn.cursor()
        c.execute("SELECT student_id,name,email,created_at FROM students")
        students = c.fetchall()
        conn.close()
        st.table(students)
    else:
        st.info("Enter admin password to access dashboard.")

# ---------------------------
# MAIN APP
# ---------------------------
init_db()

if "page" not in st.session_state:
    st.session_state.page = "home"
if "student" not in st.session_state:
    st.session_state.student = None

menu = st.tabs(["Home", "Sign Up", "Login", "Courses"])
with menu[0]: home_page()
with menu[1]: signup_page()
with menu[2]: login_page()
with menu[3]: 
    if st.session_state.student: 
        courses_page()
    else:
        st.warning("Please log in first.")

st.markdown('<div class="admin-login" onclick="window.location.href=\'?admin=true\'">Admin Login</div>', unsafe_allow_html=True)
if "admin" in st.query_params:
    admin_page()
