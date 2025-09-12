import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# -------------------
# Database setup
# -------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# Students
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    sex TEXT,
    profession TEXT,
    institution TEXT,
    mobile TEXT,
    profile_pic TEXT
)
""")

# Courses
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

# Lessons
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

# Enrollments
c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    enroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    progress INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

# Certificates
c.execute("""
CREATE TABLE IF NOT EXISTS certificates (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    cert_file TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

conn.commit()

# -------------------
# Insert dummy data
# -------------------
def insert_dummy_data():
    # Check if courses table already has data
    try:
        existing = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    except:
        existing = 0
    if existing > 0:
        return  # Already has data

    courses = [
        {
            "title": "Sustainability Basics",
            "subtitle": "Intro to Sustainability",
            "description": "Learn fundamentals of sustainability and eco-friendly practices.",
            "price": 499.0,
            "category": "Sustainability",
            "banner_path": "https://via.placeholder.com/350x150"
        },
        {
            "title": "Climate Change Fundamentals",
            "subtitle": "Understand Climate Change",
            "description": "Explore causes, impacts, and mitigation strategies of climate change.",
            "price": 599.0,
            "category": "Climate Change",
            "banner_path": "https://via.placeholder.com/350x150"
        },
        {
            "title": "ESG & Corporate Responsibility",
            "subtitle": "Environmental, Social & Governance",
            "description": "Dive into ESG concepts, reporting standards, and real-world case studies.",
            "price": 799.0,
            "category": "ESG",
            "banner_path": "https://via.placeholder.com/350x150"
        }
    ]

    for course in courses:
        try:
            c.execute("""
                INSERT INTO courses (title, subtitle, description, price, category, banner_path)
                VALUES (?,?,?,?,?,?)
            """, (
                course['title'] or "No Title",
                course['subtitle'] or "",
                course['description'] or "",
                float(course['price'] or 0),
                course['category'] or "General",
                course['banner_path'] or ""
            ))
        except Exception as e:
            print("Error inserting course:", course['title'], e)

    conn.commit()

    # Dummy lessons
    course_ids = c.execute("SELECT course_id FROM courses").fetchall()
    for cid in course_ids:
        course_id = cid[0]
        for i in range(1, 4):  # 3 lessons each
            c.execute("""
                INSERT INTO lessons (course_id, title, content_type, content_path)
                VALUES (?,?,?,?)
            """, (course_id, f"Lesson {i}", "video", f"https://sample-videos.com/video{i}.mp4"))
    conn.commit()

insert_dummy_data()

# -------------------
# Utility functions
# -------------------
def format_inr(amount):
    return f"₹{amount:,.2f}"

def generate_certificate(student_name, course_title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 50, "Certificate of Completion", align="C", ln=1)
    pdf.set_font("Arial", '', 16)
    pdf.multi_cell(0, 10, f"This certifies that {student_name} has successfully completed the course '{course_title}'.", align="C")
    filename = f"certificate_{student_name.replace(' ', '_')}_{course_title.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# -------------------
# Session state
# -------------------
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# -------------------
# Pages
# -------------------

# Top Navigation Bar
def top_nav():
    st.markdown(
        """
        <style>
        .nav-bar{
            background-color:#111;
            padding:10px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            color:white;
        }
        .nav-bar a{
            color:white;
            text-decoration:none;
            margin:0 10px;
            font-weight:bold;
        }
        .nav-bar a:hover{
            color:#00ffcc;
        }
        </style>
        <div class="nav-bar">
            <div><img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" height="50"></div>
            <div>
                <a href="#">Browse Courses</a>
                <a href="#">About</a>
            </div>
            <div>
                <a href="#" onclick="window.location.href='#login'">Login</a>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# Home / Browse Courses
def home_page():
    st.title("EinTrust Academy")
    st.subheader("Learn Sustainability, Climate Change & ESG like a pro!")

    courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    
    for course in courses:
        course_id, title, subtitle, desc, price, banner = course
        st.markdown(f"""
        <div style='border:1px solid #333; padding:10px; margin:10px; border-radius:10px; background-color:#222; color:white'>
            <img src="{banner}" width="100%">
            <h3>{title} - {subtitle}</h3>
            <p>{desc}</p>
            <p><b>{format_inr(price)}</b></p>
            <a href="#course_{course_id}" style='color:#00ffcc; font-weight:bold;'>Preview / Enroll</a>
        </div>
        """, unsafe_allow_html=True)

# Student Signup/Login
def student_signup():
    st.subheader("Create Your Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*", type="email")
        password = st.text_input("Password* (8+ chars, 1 uppercase, 1 number, 1 special)", type="password")
        sex = st.selectbox("Sex", ["Male", "Female", "Prefer not to say"])
        profession = st.selectbox("Profession*", ["Student", "Working Professional"])
        institution = st.text_input("Institution")
        mobile = st.text_input("Mobile*")
        profile_pic = st.text_input("Profile Picture URL (optional)")
        submit = st.form_submit_button("Create Profile")
        if submit:
            try:
                c.execute("""
                    INSERT INTO students (full_name,email,password,sex,profession,institution,mobile,profile_pic)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (full_name,email,password,sex,profession,institution,mobile,profile_pic))
                conn.commit()
                st.success("Profile created! Please login now.")
            except:
                st.error("Email already exists!")
            st.experimental_rerun()

def student_login():
    st.subheader("Student Login")
    with st.form("login_form"):
        email = st.text_input("Email", type="email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            user = c.execute("SELECT student_id, full_name FROM students WHERE email=? AND password=?", (email,password)).fetchone()
            if user:
                st.session_state.student_id = user[0]
                st.session_state.student_name = user[1]
                st.success(f"Welcome {user[1]}!")
            else:
                st.error("Incorrect Email/Password")

def admin_login():
    st.subheader("Admin Login")
    with st.form("admin_form"):
        pwd = st.text_input("Enter Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if pwd=="admin123":
                st.session_state.admin_logged_in = True
                st.success("Admin logged in!")
            else:
                st.error("Incorrect password!")

# -------------------
# Main app
# -------------------
def main():
    st.set_page_config(page_title="EinTrust Academy", layout="wide")
    st.markdown("<body style='background-color:#111;color:white'>", unsafe_allow_html=True)
    
    top_nav()
    
    # Home Page / Courses
    home_page()
    
    # For simplicity, login/signup via sidebar
    if st.sidebar.button("Student Signup"):
        student_signup()
    if st.sidebar.button("Student Login"):
        student_login()
    if st.sidebar.button("Admin Login"):
        admin_login()

main()
