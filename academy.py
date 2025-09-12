import streamlit as st
import sqlite3
from fpdf import FPDF
import datetime

# -------------------
# Page config
# -------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon="🌍")

# -------------------
# Database setup
# -------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# -------------------
# Create Tables
# -------------------
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    sex TEXT,
    profession TEXT,
    institution TEXT,
    mobile TEXT,
    profile_pic TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    password TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL,
    category TEXT,
    banner_path TEXT
)
""")

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

c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    progress REAL DEFAULT 0,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    cert_file TEXT,
    date TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

conn.commit()

# -------------------
# Insert dummy admin & courses if not exists
# -------------------
# Admin password = admin123
c.execute("SELECT COUNT(*) FROM admin")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO admin (password) VALUES (?)", ("admin123",))
    conn.commit()

# Dummy Courses
c.execute("SELECT COUNT(*) FROM courses")
if c.fetchone()[0] == 0:
    dummy_courses = [
        ("Sustainability Basics", "Intro to Sustainability", "Learn sustainability fundamentals", 499.0, "Sustainability", "https://via.placeholder.com/350x150"),
        ("Climate Change Fundamentals", "Understand Climate Change", "Explore causes & solutions", 599.0, "Climate Change", "https://via.placeholder.com/350x150"),
        ("ESG for Beginners", "Environmental, Social, Governance", "Basics of ESG reporting & frameworks", 699.0, "ESG", "https://via.placeholder.com/350x150")
    ]
    for course in dummy_courses:
        c.execute("INSERT INTO courses (title, subtitle, description, price, category, banner_path) VALUES (?,?,?,?,?,?)", course)
    conn.commit()

# Dummy Lessons
c.execute("SELECT COUNT(*) FROM lessons")
if c.fetchone()[0] == 0:
    # Map course titles to IDs
    courses_map = {row[1]: row[0] for row in c.execute("SELECT course_id,title FROM courses").fetchall()}
    lessons_data = [
        (courses_map["Sustainability Basics"], "Introduction to Sustainability", "video", "https://sample-videos.com/video123.mp4"),
        (courses_map["Sustainability Basics"], "Sustainable Practices", "pdf", "https://samplepdf.com/sustainability.pdf"),
        (courses_map["Climate Change Fundamentals"], "Causes of Climate Change", "video", "https://sample-videos.com/video123.mp4"),
        (courses_map["Climate Change Fundamentals"], "Impacts & Solutions", "ppt", "https://sampleppt.com/climate.pptx"),
        (courses_map["ESG for Beginners"], "ESG Overview", "video", "https://sample-videos.com/video123.mp4"),
        (courses_map["ESG for Beginners"], "Reporting Frameworks", "pdf", "https://samplepdf.com/esg.pdf"),
    ]
    for l in lessons_data:
        c.execute("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)", l)
    conn.commit()

# -------------------
# Utility Functions
# -------------------
def hash_password(pw):
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_certificate(student_name, course_title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 60, "", ln=1)
    pdf.cell(0, 10, "Certificate of Completion", ln=1, align="C")
    pdf.set_font("Arial", "", 18)
    pdf.cell(0, 20, f"This certifies that {student_name}", ln=1, align="C")
    pdf.cell(0, 20, f"has successfully completed the course '{course_title}'", ln=1, align="C")
    filename = f"{student_name}_{course_title}.pdf".replace(" ","_")
    pdf.output(filename)
    return filename

# -------------------
# Authentication Pages
# -------------------
def signup_page():
    st.subheader("Create Your Account")
    full_name = st.text_input("Full Name *")
    email = st.text_input("Email *")
    password = st.text_input("Set Password *", type="password")
    st.caption("Password must be 8+ characters, 1 uppercase, 1 number, 1 special (@,#,*)")
    sex = st.selectbox("Sex", ["Prefer not to say","Male","Female"])
    profession = st.selectbox("Profession *", ["Student","Working Professional"])
    institution = st.text_input("Institution")
    mobile = st.text_input("Mobile *")
    if st.button("Create Profile"):
        if not full_name or not email or not password or not profession or not mobile:
            st.error("Please fill all mandatory fields.")
            return
        try:
            c.execute("INSERT INTO students (full_name,email,password,sex,profession,institution,mobile) VALUES (?,?,?,?,?,?,?)",
                      (full_name,email,hash_password(password),sex,profession,institution,mobile))
            conn.commit()
            st.success("Profile created! Please login now.")
        except sqlite3.IntegrityError:
            st.error("Email already exists. Try logging in.")
        st.stop()

def login_page():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT student_id,full_name,password FROM students WHERE email=?", (email,))
        user = c.fetchone()
        if user and hash_password(password) == user[2]:
            st.session_state['student_id'] = user[0]
            st.session_state['student_name'] = user[1]
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect email/password.")

def admin_login_page():
    st.subheader("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        c.execute("SELECT password FROM admin LIMIT 1")
        db_pw = c.fetchone()[0]
        if password == db_pw:
            st.session_state['admin_logged_in'] = True
        else:
            st.error("Incorrect password.")

# -------------------
# Home / Courses Pages
# -------------------
def browse_courses_page():
    st.subheader("All Courses")
    courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    for course in courses:
        st.image(course[5], width=400)
        st.markdown(f"### {course[1]}")
        st.markdown(f"_{course[2]}_")
        st.text(course[3])
        st.text(f"Price: ₹{course[4]:,.2f}")
        if st.button(f"Enroll → {course[1]}", key=course[0]):
            st.session_state['enroll_course_id'] = course[0]
            st.session_state['enroll_course_name'] = course[1]
            st.session_state['page'] = "signup"

def course_preview_page(course_id):
    course = c.execute("SELECT title,subtitle,description,price FROM courses WHERE course_id=?", (course_id,)).fetchone()
    st.subheader(course[0])
    st.markdown(f"_{course[1]}_")
    st.text(course[2])
    st.text(f"Price: ₹{course[3]:,.2f}")
    lessons = c.execute("SELECT title,content_type FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    st.markdown("**Lessons:**")
    for l in lessons:
        st.text(f"- {l[0]} ({l[1]})")

# -------------------
# Main
# -------------------
if 'page' not in st.session_state:
    st.session_state['page'] = "home"
if 'student_id' not in st.session_state:
    st.session_state['student_id'] = None
if 'student_name' not in st.session_state:
    st.session_state['student_name'] = None
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False

if st.session_state['page'] == "home":
    st.title("EinTrust Academy")
    browse_courses_page()
    st.sidebar.button("Login", on_click=lambda: st.session_state.update({'page':"login"}))
    st.sidebar.button("Admin", on_click=lambda: st.session_state.update({'page':"admin_login"}))

elif st.session_state['page'] == "signup":
    signup_page()
    st.button("Back to Login", on_click=lambda: st.session_state.update({'page':"login"}))

elif st.session_state['page'] == "login":
    login_page()
    if st.session_state.get('student_id'):
        st.session_state['page'] = "home"

elif st.session_state['page'] == "admin_login":
    admin_login_page()
    if st.session_state.get('admin_logged_in'):
        st.subheader("Admin Dashboard")
        st.text("Here admin can view courses, students, lessons, etc.")
