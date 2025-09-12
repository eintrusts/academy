import streamlit as st
import sqlite3
from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="EinTrust Academy", page_icon="🎓", layout="wide")

# Logo
st.markdown(
    """
    <style>
    body { background-color: #121212; color: #ffffff; }
    .title { font-size:36px; font-weight:bold; color:#00FFAA; }
    </style>
    """,
    unsafe_allow_html=True
)
st.image("logo.png", width=160)  # <--- Place your logo file in same folder

# ----------------------------
# DATABASE
# ----------------------------
DB_PATH = "academy.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Courses
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subtitle TEXT,
            description TEXT,
            price REAL,
            category TEXT
        )
    """)

    # Lessons
    c.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            content TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)

    # Students
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # Enrollments
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            enroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'enrolled',
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ----------------------------
# DB Helpers
# ----------------------------
def get_courses():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM courses")
    data = c.fetchall()
    conn.close()
    return data

def add_student(name, email, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO students (name,email,password) VALUES (?,?,?)", (name,email,password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_student(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email,password))
    student = c.fetchone()
    conn.close()
    return student

# ----------------------------
# PAGES
# ----------------------------
def home_page():
    st.markdown("<div class='title'>Welcome to EinTrust Academy 🎓</div>", unsafe_allow_html=True)
    st.write("Learn sustainability, ESG, climate change, and more. Browse our courses below.")

    courses = get_courses()
    if not courses:
        st.info("No courses available yet. Please check back later.")
    else:
        for course in courses:
            cid, title, subtitle, desc, price, cat = course
            st.markdown(f"### {title}")
            st.write(subtitle)
            st.write(f"💰 {'Free' if price==0 else f'₹{price}'}")
            if st.button("📘 Enroll", key=f"enroll_{cid}"):
                if "student" not in st.session_state:
                    st.session_state.page = "signup"
                else:
                    if price == 0:
                        st.session_state.page = f"course_{cid}"
                    else:
                        st.session_state.page = f"payment_{cid}"

def signup_page():
    st.subheader("📝 Create Your Profile")
    name = st.text_input("Full Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up", key="signup_btn"):
        if add_student(name,email,password):
            st.success("Profile created! Please log in.")
            st.session_state.page = "login"
        else:
            st.error("Email already registered.")

def login_page():
    st.subheader("🔑 Student Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_btn"):
        student = login_student(email,password)
        if student:
            st.session_state.student = student
            st.success(f"Welcome, {student[1]} 👋")
            st.session_state.page = "home"
        else:
            st.error("Invalid credentials.")

def payment_page(course_id):
    st.subheader("💳 Payment Gateway (Demo)")
    st.write("This is a placeholder. Integrate Razorpay/Stripe here.")
    if st.button("Simulate Payment Success", key=f"pay_{course_id}"):
        st.success("Payment successful! Redirecting to course...")
        st.session_state.page = f"course_{course_id}"

def course_page(course_id):
    st.subheader(f"📚 Course {course_id} Lessons")
    st.write("Lesson content will be shown here.")
    st.progress(0.4)
    st.info("Certificate will be generated after completion.")

def admin_page():
    st.subheader("👨‍💻 Admin Dashboard")
    pw = st.text_input("Enter Admin Password", type="password", key="admin_pw")
    if st.button("Login as Admin", key="admin_btn"):
        if pw == "admin123":  # change this
            st.session_state.page = "admin_dashboard"
        else:
            st.error("Wrong password.")

def admin_dashboard():
    st.title("📊 Admin Dashboard")
    st.write("Here admin can manage courses, lessons, and students.")
    st.info("CRUD operations UI can be added here.")

# ----------------------------
# ROUTING
# ----------------------------
menu = st.sidebar.radio("Navigate", ["Home","Sign Up","Login","Admin"], key="menu")

if menu == "Home":
    home_page()
elif menu == "Sign Up":
    signup_page()
elif menu == "Login":
    login_page()
elif menu == "Admin":
    admin_page()

# Extra pages after state changes
if "page" in st.session_state:
    if st.session_state.page.startswith("course_"):
        cid = int(st.session_state.page.split("_")[1])
        course_page(cid)
    elif st.session_state.page.startswith("payment_"):
        cid = int(st.session_state.page.split("_")[1])
        payment_page(cid)
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "admin_dashboard":
        admin_dashboard()
