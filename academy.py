import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ------------------- STREAMLIT CONFIG -------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon="🌱", initial_sidebar_state="collapsed")

# ------------------- DATABASE SETUP -------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

def create_tables():
    # Students
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
    # Admin
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin(
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL
        )
    """)
    # Courses
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses(
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subtitle TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            banner_path TEXT
        )
    """)
    # Lessons
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
    # Enrollments
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments(
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            enrolled_on TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)
    # Progress
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress(
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            lesson_id INTEGER,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
        )
    """)
    # Certificates
    c.execute("""
        CREATE TABLE IF NOT EXISTS certificates(
            cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            cert_file TEXT,
            generated_on TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)
    conn.commit()

create_tables()

# ------------------- UTILS -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# ------------------- NAV BAR -------------------
def top_nav():
    st.markdown("""
    <style>
    .top-bar {
        background-color:#121212;
        padding:10px 20px;
        display:flex;
        align-items:center;
        justify-content:space-between;
        color:white;
    }
    .top-bar a {
        color:white;
        margin:0 10px;
        text-decoration:none;
    }
    </style>
    <div class="top-bar">
        <div>
            <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="160">
        </div>
        <div>
            <a href="#">Home</a>
            <a href="#">Courses</a>
            <a href="#">About</a>
        </div>
        <div>
            <a href="#login">Login</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------- HOME PAGE -------------------
def home_page():
    top_nav()
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Welcome to EinTrust Academy")
    st.subheader("Learn Sustainability, Climate Change and more!")

    try:
        courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
        if not courses:
            st.info("No courses uploaded yet.")
        else:
            for course in courses:
                st.markdown(f"""
                <div style="background-color:#1e1e1e; padding:15px; margin-bottom:20px; border-radius:8px;">
                    <img src="{course[5]}" width="100%">
                    <h3 style="color:white">{course[1]}</h3>
                    <p style="color:white">{course[2]}</p>
                    <p style="color:white">₹{course[4]:,.0f}</p>
                    <a href="#enroll" style="background-color:#4CAF50;color:white;padding:8px 15px;border-radius:5px;text-decoration:none;">Enroll</a>
                </div>
                """, unsafe_allow_html=True)
    except sqlite3.OperationalError as e:
        st.error("Courses not available. Database may be empty.")
        st.error(str(e))

# ------------------- STUDENT SIGNUP -------------------
def student_signup():
    st.header("Student Signup")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name *")
        email = st.text_input("Email *")
        password = st.text_input("Password *", type="password")
        st.caption("Password must be 8+ characters, contain 1 uppercase, 1 number, and 1 special char (@,#,*)")
        sex = st.selectbox("Sex", ["Prefer not to say", "Male", "Female"])
        profession = st.selectbox("Profession *", ["Student", "Working Professional"])
        institution = st.text_input("Institution")
        mobile = st.text_input("Mobile *")
        profile_pic = st.file_uploader("Profile Picture (Optional)")
        submitted = st.form_submit_button("Create Profile")
        
        if submitted:
            if not full_name or not email or not password or not profession or not mobile:
                st.error("Please fill all mandatory fields")
            else:
                try:
                    hashed_pwd = hash_password(password)
                    c.execute("INSERT INTO students(full_name,email,password,sex,profession,institution,mobile,profile_pic) VALUES(?,?,?,?,?,?,?,?)",
                              (full_name,email,hashed_pwd,sex,profession,institution,mobile,None))
                    conn.commit()
                    st.success("Profile created successfully! Redirecting to login page...")
                except sqlite3.IntegrityError:
                    st.error("Email already exists!")

# ------------------- STUDENT LOGIN -------------------
def student_login():
    st.header("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = c.execute("SELECT student_id,password FROM students WHERE email=?", (email,)).fetchone()
        if student and verify_password(password, student[1]):
            st.session_state["student_id"] = student[0]
            st.success("Login successful!")
        else:
            st.error("Incorrect email/password")

# ------------------- ADMIN LOGIN -------------------
def admin_login():
    st.header("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        admin = c.execute("SELECT * FROM admin WHERE password=?", (hash_password(password),)).fetchone()
        if admin:
            st.session_state["admin"] = True
            st.success("Admin login successful")
        else:
            st.error("Incorrect admin password")

# ------------------- MAIN -------------------
def main():
    if "student_id" not in st.session_state:
        st.session_state["student_id"] = None
    if "admin" not in st.session_state:
        st.session_state["admin"] = False
    
    page = st.sidebar.selectbox("Navigate", ["Home","Student Signup","Student Login","Admin Login"])
    
    if page=="Home":
        home_page()
    elif page=="Student Signup":
        student_signup()
    elif page=="Student Login":
        student_login()
    elif page=="Admin Login":
        admin_login()

if __name__=="__main__":
    main()
