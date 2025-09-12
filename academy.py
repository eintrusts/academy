import streamlit as st
import sqlite3
from datetime import datetime

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# Students table
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    sex TEXT,
    profession TEXT NOT NULL,
    institution TEXT,
    mobile TEXT NOT NULL,
    profile_pic TEXT
)
""")

# Admin table (simple password protection)
c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    password TEXT NOT NULL
)
""")

# Courses table
c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    price REAL,
    category TEXT,
    banner_path TEXT
)
""")

# Lessons table
c.execute("""
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content_type TEXT,
    content_path TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

# Enrollments table
c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    progress INTEGER DEFAULT 0,
    enrolled_on TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")
conn.commit()

# -----------------------------
# INSERT DUMMY DATA (ONLY ONCE)
# -----------------------------
def insert_dummy_data():
    # Dummy admin password
    c.execute("INSERT OR IGNORE INTO admin (admin_id, password) VALUES (1, 'admin123')")
    
    # Dummy courses
    dummy_courses = [
        ("Sustainability Basics", "Intro to Sustainability", "Learn sustainability fundamentals", 499.0, "Sustainability", "https://via.placeholder.com/350x150"),
        ("Climate Change Fundamentals", "Understand Climate Change", "Explore causes & solutions", 599.0, "Climate Change", "https://via.placeholder.com/350x150"),
        ("ESG for Beginners", "Environmental, Social, Governance", "Basics of ESG reporting & frameworks", 699.0, "ESG", "https://via.placeholder.com/350x150")
    ]
    
    for course in dummy_courses:
        title, subtitle, desc, price, cat, banner = course
        c.execute("""
            INSERT OR IGNORE INTO courses 
            (title, subtitle, description, price, category, banner_path)
            VALUES (?,?,?,?,?,?)
        """, (title, subtitle, desc, float(price), cat, banner))
    conn.commit()
    
    # Dummy lessons for courses
    c.execute("SELECT course_id FROM courses")
    courses = c.fetchall()
    for course in courses:
        course_id = course[0]
        c.execute("INSERT OR IGNORE INTO lessons (course_id, title, content_type, content_path) VALUES (?,?,?,?)",
                  (course_id, "Lesson 1: Introduction", "video", "https://via.placeholder.com/640x360"))
        c.execute("INSERT OR IGNORE INTO lessons (course_id, title, content_type, content_path) VALUES (?,?,?,?)",
                  (course_id, "Lesson 2: Details", "pdf", "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"))
    conn.commit()

insert_dummy_data()

# -----------------------------
# STYLING
# -----------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon="🌍")
st.markdown("""
<style>
body {background-color:#121212; color:white; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
a {color: #1DB954; text-decoration:none;}
.card {background-color:#1E1E1E; padding:15px; border-radius:10px; margin-bottom:15px;}
button:hover {background-color:#333;}
input, select {background-color:#1E1E1E; color:white; border:1px solid #444; padding:5px; border-radius:5px;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

# -----------------------------
# NAVIGATION
# -----------------------------
def top_nav():
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png", width=150)
    with col2:
        st.markdown("<h3 style='text-align:center'>Browse Courses | About</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("Login"):
            st.session_state['page'] = "login"

# -----------------------------
# HOME PAGE
# -----------------------------
def home_page():
    top_nav()
    st.markdown("---")
    
    st.subheader("All Courses")
    courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    
    for course in courses:
        course_id, title, subtitle, description, price, banner = course
        st.markdown(f"""
        <div class='card'>
        <img src="{banner}" width='100%'/>
        <h4>{title}</h4>
        <i>{subtitle}</i>
        <p>{description}</p>
        <b>₹{price:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Preview & Enroll: {title}", key=course_id):
            st.session_state['selected_course'] = course_id
            st.session_state['page'] = "course_preview"

# -----------------------------
# COURSE PREVIEW
# -----------------------------
def course_preview_page():
    course_id = st.session_state.get('selected_course')
    course = c.execute("SELECT title,subtitle,description,price FROM courses WHERE course_id=?", (course_id,)).fetchone()
    lessons = c.execute("SELECT title,content_type,content_path FROM lessons WHERE course_id=? ORDER BY lesson_id ASC", (course_id,)).fetchall()
    
    st.subheader(f"{course[0]} - {course[1]}")
    st.write(course[2])
    st.write(f"Price: ₹{course[3]:,.0f}")
    
    st.markdown("**Lessons:**")
    for idx, lesson in enumerate(lessons, 1):
        st.write(f"{idx}. {lesson[0]} ({lesson[1]})")
    
    if st.button("Enroll Now"):
        st.session_state['page'] = "signup"

# -----------------------------
# SIGNUP & LOGIN
# -----------------------------
def signup_page():
    st.subheader("Student Signup")
    full_name = st.text_input("Full Name *")
    email = st.text_input("Email ID *")
    password = st.text_input("Set Password *", type="password")
    st.markdown("Password must be 8 chars, include 1 uppercase, 1 number, 1 special char (@,#,*)")
    sex = st.selectbox("Sex", ["Male", "Female", "Prefer not to say"])
    profession = st.selectbox("Profession *", ["Student","Working Professional"])
    institution = st.text_input("Institution")
    mobile = st.text_input("Mobile *")
    
    if st.button("Create Profile"):
        hashed_pw = hash_password(password)
        try:
            c.execute("INSERT INTO students (full_name,email,password,sex,profession,institution,mobile) VALUES (?,?,?,?,?,?,?)",
                     (full_name,email,hashed_pw,sex,profession,institution,mobile))
            conn.commit()
            st.success("Profile created! Please login.")
            st.session_state['page'] = "login"
        except sqlite3.IntegrityError:
            st.error("Email already exists!")

def login_page():
    st.subheader("Student Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = c.execute("SELECT student_id,password FROM students WHERE email=?", (email,)).fetchone()
        if user and verify_password(user[1], password):
            st.success("Logged in!")
            st.session_state['student_id'] = user[0]
            st.session_state['page'] = "student_dashboard"
        else:
            st.error("Incorrect email/password")

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
def student_dashboard():
    st.subheader("Student Dashboard")
    student_id = st.session_state['student_id']
    
    enrollments = c.execute("""
        SELECT e.course_id, c.title, c.price, e.progress
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        WHERE e.student_id=?
    """, (student_id,)).fetchall()
    
    st.markdown("**Your Courses:**")
    for e in enrollments:
        st.write(f"{e[1]} - ₹{e[2]:,.0f} - Progress: {e[3]}%")

# -----------------------------
# ADMIN LOGIN & DASHBOARD
# -----------------------------
def admin_login_page():
    st.subheader("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        stored_pw = c.execute("SELECT password FROM admin WHERE admin_id=1").fetchone()[0]
        if password == stored_pw:
            st.session_state['page'] = "admin_dashboard"
        else:
            st.error("Incorrect password")

def admin_dashboard():
    st.subheader("Admin Dashboard")
    courses = c.execute("SELECT course_id,title FROM courses").fetchall()
    st.markdown("**All Courses:**")
    for cdata in courses:
        st.write(f"{cdata[0]} - {cdata[1]}")

# -----------------------------
# MAIN
# -----------------------------
if 'page' not in st.session_state:
    st.session_state['page'] = "home"

page = st.session_state['page']

if page == "home":
    home_page()
elif page == "course_preview":
    course_preview_page()
elif page == "signup":
    signup_page()
elif page == "login":
    login_page()
elif page == "student_dashboard":
    student_dashboard()
elif page == "admin_login":
    admin_login_page()
elif page == "admin_dashboard":
    admin_dashboard()
