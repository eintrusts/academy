import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ------------------- DATABASE -------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Create tables
def create_tables():
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    mobile TEXT,
                    profession TEXT,
                    institution TEXT,
                    sex TEXT,
                    profile_pic TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS admin (
                    admin_id INTEGER PRIMARY KEY,
                    password TEXT NOT NULL
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    subtitle TEXT,
                    description TEXT,
                    price REAL,
                    category TEXT,
                    banner_path TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title TEXT,
                    content_type TEXT,
                    content_path TEXT,
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS progress (
                    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    lesson_id INTEGER,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS certificates (
                    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    cert_file TEXT,
                    date_generated TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    conn.commit()

create_tables()

# ------------------- DUMMY DATA -------------------
def insert_dummy_data():
    # Admin default password
    c.execute("INSERT OR IGNORE INTO admin (admin_id, password) VALUES (1, ?)", ('admin123',))

    # Courses
    dummy_courses = [
        ("Sustainability Basics", "Intro to Sustainability", "Learn sustainability fundamentals", 499.0, "Sustainability", "https://via.placeholder.com/350x150"),
        ("Climate Change Fundamentals", "Understand Climate Change", "Explore causes & solutions", 599.0, "Climate", "https://via.placeholder.com/350x150"),
        ("ESG for Beginners", "Environmental, Social, Governance", "Basics of ESG reporting & frameworks", 699.0, "ESG", "https://via.placeholder.com/350x150")
    ]
    for course in dummy_courses:
        c.execute("""
            INSERT OR IGNORE INTO courses (title, subtitle, description, price, category, banner_path)
            VALUES (?,?,?,?,?,?)
        """, course)
    
    conn.commit()

    # Lessons
    c.execute("SELECT course_id FROM courses")
    course_ids = c.fetchall()
    for course_id_tuple in course_ids:
        course_id = course_id_tuple[0]
        lessons = [("Lesson 1: Intro", "video", "https://via.placeholder.com/640x360"),
                   ("Lesson 2: Details", "pdf", "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf")]
        for lesson in lessons:
            c.execute("""
                INSERT OR IGNORE INTO lessons (course_id, title, content_type, content_path)
                VALUES (?,?,?,?)
            """, (course_id, lesson[0], lesson[1], lesson[2]))
    conn.commit()

insert_dummy_data()

# ------------------- STREAMLIT CONFIG -------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color:#121212; color:white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
div.stButton > button:first-child {background-color:#1E88E5; color:white; border-radius:8px; height:40px;}
</style>
""", unsafe_allow_html=True)

# ------------------- TOP NAV -------------------
def top_nav():
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    with col2:
        st.markdown("<h3 style='text-align:center;'>Browse Courses | About</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("Login"):
            st.session_state['page'] = "login"

# ------------------- HOME PAGE -------------------
def home_page():
    top_nav()
    st.markdown("## Available Courses")
    courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    for course in courses:
        st.markdown(f"""
        <div style='border:1px solid #555; padding:10px; margin-bottom:10px; border-radius:10px;'>
        <h4>{course[1]}</h4>
        <p>{course[2]}</p>
        <p>{course[3]}</p>
        <p>Price: ₹{int(course[4]):,}</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------- RUN APP -------------------
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    home_page()
elif st.session_state['page'] == 'login':
    st.write("Login Page Placeholder")
