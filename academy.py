import streamlit as st
import sqlite3
from pathlib import Path

# ---------------------------
# Database Setup
# ---------------------------
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

# ---------------------------
# Streamlit Config & CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
    <style>
        body {background-color:#121212; color:white;}
        h1, h2, h3, h4 {color:white;}
        .top-nav {display:flex; justify-content:space-between; align-items:center; padding:10px; background-color:#1F1F1F;}
        .top-nav button {background-color:#0073e6; color:white; border:none; padding:6px 12px; border-radius:5px; cursor:pointer;}
        .course-card {background-color:#1f1f1f; padding:15px; margin-bottom:15px; border-radius:10px;}
        .course-card button {background-color:#0073e6; color:white; border:none; padding:6px 12px; border-radius:5px; cursor:pointer;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Top Navigation
# ---------------------------
def top_nav():
    st.markdown("""
        <div class="top-nav">
            <h2>EinTrust Academy</h2>
            <input type="text" placeholder="Search for anything..." style="padding:5px; border-radius:5px; width:300px;">
            <button onclick="window.location.href='#login'">Login</button>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------
# Home Page
# ---------------------------
def home_page():
    top_nav()
    st.markdown("## Browse Courses")

    courses = c.execute("SELECT course_id,title,subtitle,description,price FROM courses ORDER BY course_id DESC").fetchall()
    if not courses:
        st.info("No courses available yet. Admin can upload courses.")
    else:
        for course in courses:
            course_id = course[0]
            st.markdown(f"""
                <div class="course-card">
                    <h3>{course[1]}</h3>
                    <em>{course[2]}</em>
                    <p>{course[3]}</p>
                    <strong>Price: ₹{course[4]:,.2f}</strong><br>
                    <button onclick="window.location.href='#course_{course_id}'">Preview</button>
                </div>
            """, unsafe_allow_html=True)

# ---------------------------
# Course Preview Page
# ---------------------------
def course_preview(course_id, student_id=None):
    course = c.execute("SELECT title,subtitle,description,price FROM courses WHERE course_id=?",(course_id,)).fetchone()
    if course:
        st.header(course[0])
        st.subheader(course[1])
        st.write(course[2])
        st.write(f"Price: ₹{course[3]:,.2f}")

        # Enroll Button
        if student_id:
            enrolled = c.execute("SELECT * FROM enrollments WHERE student_id=? AND course_id=?",(student_id,course_id)).fetchone()
            if not enrolled:
                if st.button("Enroll"):
                    c.execute("INSERT INTO enrollments(student_id,course_id) VALUES (?,?)",(student_id,course_id))
                    conn.commit()
                    st.success("Enrolled successfully!")
            else:
                st.info("Already Enrolled")

        st.markdown("### Lessons")
        lessons = c.execute("SELECT lesson_id,title,lesson_type FROM lessons WHERE course_id=?",(course_id,)).fetchall()
        for lesson in lessons:
            st.markdown(f"- {lesson[1]} ({lesson[2]})")

# ---------------------------
# Student Signup
# ---------------------------
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

# ---------------------------
# Student Login
# ---------------------------
def student_login():
    st.header("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = c.execute("SELECT student_id FROM students WHERE email=? AND password=?", (email,password)).fetchone()
        if user:
            st.success("Login successful!")
            st.session_state['student_id'] = user[0]
        else:
            st.error("Incorrect email or password.")

# ---------------------------
# Admin Login
# ---------------------------
def admin_login():
    st.header("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        if password == "admin123":
            st.success("Admin logged in! Manage courses below.")
            # Add course upload/edit functionality here
        else:
            st.error("Incorrect password.")

# ---------------------------
# Main App
# ---------------------------
def main():
    if 'student_id' not in st.session_state:
        st.session_state['student_id'] = None

    pages = ["Home", "Signup", "Login", "Admin Login"]
    page = st.sidebar.selectbox("Navigate", pages)

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
