import streamlit as st
import sqlite3
from fpdf import FPDF
import hashlib
from datetime import datetime

# -------------------- DB Setup --------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Users Table
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    mobile TEXT,
    profession TEXT,
    institution TEXT,
    sex TEXT,
    profile_pic TEXT
)
""")

# Admin Table
c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY,
    password TEXT NOT NULL
)
""")

# Courses Table
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

# Lessons Table
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

# Progress Table
c.execute("""
CREATE TABLE IF NOT EXISTS progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    lesson_id INTEGER,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
)
""")

# Certificates Table
c.execute("""
CREATE TABLE IF NOT EXISTS certificates (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    cert_file TEXT,
    date_generated TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")
conn.commit()

# -------------------- Dummy Data --------------------
def insert_dummy_data():
    # Admin
    c.execute("INSERT OR IGNORE INTO admin (admin_id, password) VALUES (1, 'admin123')")

    dummy_courses = [
        {"title": "Sustainability Basics",
         "subtitle": "Intro to Sustainability",
         "description": "Learn sustainability fundamentals",
         "price": 499.0,
         "category": "Sustainability",
         "banner_path": "https://via.placeholder.com/350x150"},

        {"title": "Climate Change Fundamentals",
         "subtitle": "Understand Climate Change",
         "description": "Explore causes & solutions",
         "price": 599.0,
         "category": "Climate Change",
         "banner_path": "https://via.placeholder.com/350x150"},

        {"title": "ESG for Beginners",
         "subtitle": "Environmental, Social, Governance",
         "description": "Basics of ESG reporting & frameworks",
         "price": 699.0,
         "category": "ESG",
         "banner_path": "https://via.placeholder.com/350x150"}
    ]

    for course in dummy_courses:
        try:
            c.execute("""
                INSERT OR IGNORE INTO courses (title, subtitle, description, price, category, banner_path)
                VALUES (?,?,?,?,?,?)
            """, (course['title'], course['subtitle'], course['description'],
                  float(course['price']), course['category'], course['banner_path']))
        except:
            continue

    conn.commit()

    # Dummy lessons
    c.execute("SELECT course_id FROM courses")
    course_ids = c.fetchall()
    for course_id_tuple in course_ids:
        course_id = course_id_tuple[0]
        try:
            c.execute("""
                INSERT OR IGNORE INTO lessons (course_id, title, content_type, content_path)
                VALUES (?,?,?,?)
            """, (course_id, "Lesson 1: Introduction", "video", "https://via.placeholder.com/640x360"))
            c.execute("""
                INSERT OR IGNORE INTO lessons (course_id, title, content_type, content_path)
                VALUES (?,?,?,?)
            """, (course_id, "Lesson 2: Details", "pdf", "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"))
        except:
            continue
    conn.commit()

insert_dummy_data()

# -------------------- Utilities --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# -------------------- Streamlit Layout --------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
body {
    background-color:#121212;
    color:white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
div.stButton > button:first-child {
    background-color:#1E88E5;
    color:white;
    border-radius:8px;
    height:40px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Top Navigation --------------------
def top_nav():
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=150)
    with col2:
        st.markdown("<h3 style='text-align:center;'>Browse Courses | About</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("Login"):
            st.session_state['page'] = "login"

# -------------------- Home Page --------------------
def home_page():
    top_nav()
    st.markdown("## Available Courses")
    courses = c.execute("SELECT course_id,title,subtitle,description,price,category,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    for course in courses:
        st.markdown(f"""
        <div style='border:1px solid #555; padding:10px; margin-bottom:10px; border-radius:10px;'>
        <h4>{course[1]}</h4>
        <p>{course[2]}</p>
        <p>{course[3]}</p>
        <p>Price: ₹{int(course[4]):,}</p>
        <button onclick="window.location.href='?course_id={course[0]}'">Preview / Enroll</button>
        </div>
        """, unsafe_allow_html=True)

# -------------------- Run App --------------------
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    home_page()
elif st.session_state['page'] == 'login':
    st.write("Login Page Here")
