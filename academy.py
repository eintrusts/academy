# academy.py

import streamlit as st
import sqlite3
from pathlib import Path

# -------------------
# Database Setup
# -------------------
DB_PATH = "academy.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses(
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subtitle TEXT,
            description TEXT,
            price REAL DEFAULT 0,
            category TEXT,
            banner_path TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS lessons(
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            lesson_type TEXT,
            content_path TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS students(
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic TEXT,
            sex TEXT,
            profession TEXT,
            institution TEXT,
            mobile TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments(
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            progress REAL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS certificates(
            cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            cert_file TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)
    conn.commit()

create_tables()

# -------------------
# Top Navigation Bar
# -------------------
def top_nav():
    st.markdown(
        """
        <style>
        .top-bar {
            background-color:#1F1F1F;
            padding:15px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            color:white;
        }
        .top-bar h1 {
            margin:0;
            font-size:24px;
        }
        .top-bar button {
            background-color:#0073e6;
            color:white;
            border:none;
            padding:8px 15px;
            border-radius:5px;
            cursor:pointer;
        }
        </style>
        <div class="top-bar">
            <h1>EinTrust Academy</h1>
            <div>
                <button onclick="window.location.href='#login'">Login</button>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# -------------------
# Home Page
# -------------------
def home_page():
    top_nav()
    st.markdown("## Browse Courses")
    try:
        courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
    except sqlite3.OperationalError:
        st.warning("Courses table is missing or columns are incorrect.")
        return

    if not courses:
        st.info("No courses available yet. Admin can upload courses.")
    else:
        for course in courses:
            st.markdown(f"### {course[1]}")
            st.markdown(f"_{course[2]}_")
            st.markdown(course[3])
            st.markdown(f"**Price:** ₹{course[4]:,.2f}")
            st.button("Enroll", key=f"enroll_{course[0]}")

# -------------------
# Student Signup
# -------------------
def student_signup():
    st.header("Student Signup")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Set Password", type="password")
    st.markdown("**Password must:** 8+ chars, 1 number, 1 uppercase, 1 special char (@#*)")
    sex = st.selectbox("Sex", ["Male","Female","Prefer not to say"])
    profession = st.selectbox("Profession", ["Student","Working Professional"])
    institution = st.text_input("Institution")
    mobile = st.text_input("Mobile Number")

    if st.button("Submit"):
        if full_name and email and password and profession:
            try:
                c.execute("INSERT INTO students(full_name,email,password,sex,profession,institution,mobile) VALUES (?,?,?,?,?,?,?)",
                          (full_name,email,password,sex,profession,institution,mobile))
                conn.commit()
                st.success("Profile created! Please login now.")
            except sqlite3.IntegrityError:
                st.error("Email already exists.")
        else:
            st.error("Please fill all mandatory fields.")

# -------------------
# Student Login
# -------------------
def student_login():
    st.header("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = c.execute("SELECT student_id FROM students WHERE email=? AND password=?", (email,password)).fetchone()
        if user:
            st.success("Login successful!")
        else:
            st.error("Incorrect email or password.")

# -------------------
# Admin Login
# -------------------
def admin_login():
    st.header("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        if password == "admin123":  # Replace with your real password
            st.success("Admin logged in!")
        else:
            st.error("Incorrect password.")

# -------------------
# Main
# -------------------
def main():
    st.set_page_config(page_title="EinTrust Academy", layout="wide")
    st.markdown("<style>body{background-color:#121212;color:white;}</style>",unsafe_allow_html=True)

    # Home / Login / Signup
    page = st.sidebar.selectbox("Navigate", ["Home","Signup","Login","Admin Login"])
    if page=="Home":
        home_page()
    elif page=="Signup":
        student_signup()
    elif page=="Login":
        student_login()
    elif page=="Admin Login":
        admin_login()

if __name__=="__main__":
    main()
