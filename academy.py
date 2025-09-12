import streamlit as st
import sqlite3
import re

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT,
    profile_pic TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL,
    banner_path TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    course_id INTEGER,
    progress INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

conn.commit()

# ---------------------------
# Helper Functions
# ---------------------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_password(password):
    return (len(password) >= 8 and
            re.search(r"[0-9]", password) and
            re.search(r"[A-Z]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)

    st.markdown("<h2 style='text-align:center;'>Welcome to EinTrust Academy</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    courses = c.execute("SELECT * FROM courses").fetchall()
    if courses:
        for course in courses:
            st.subheader(course[1])
            st.write(course[3])
            if course[4] == 0:
                st.success("Free Course")
            else:
                st.warning(f"Paid Course: ₹{course[4]}")
            if st.button("Enroll", key=f"enroll_{course[0]}"):
                st.session_state["page"] = "signup"
                st.experimental_rerun()
    else:
        st.info("No courses available yet. Please check back soon!")

def page_signup():
    st.title("Sign Up")
    with st.form("signup_form"):
        profile_pic = st.text_input("Profile Picture (URL)")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Create Profile")

        if submitted:
            if not is_valid_email(email):
                st.error("Please enter a valid email ID.")
            elif not is_valid_password(password):
                st.error("Password must be 8+ chars, include uppercase, number, and special character.")
            else:
                try:
                    c.execute("INSERT INTO users(full_name,email,password,gender,profession,institution,profile_pic) VALUES (?,?,?,?,?,?,?)",
                              (full_name, email, password, gender, profession, institution, profile_pic))
                    conn.commit()
                    st.success("Profile created successfully! Please log in.")
                    st.session_state["page"] = "login"
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error("This email is already registered. Please log in.")

def page_login():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
            if user:
                st.session_state["user"] = user
                st.session_state["page"] = "student_dashboard"
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

def page_student_dashboard():
    st.title("Student Dashboard")
    user = st.session_state.get("user")
    st.write(f"Welcome, {user[1]}!")

    enrollments = c.execute("SELECT * FROM enrollments WHERE user_id=?", (user[0],)).fetchall()
    if not enrollments:
        st.info("You have not enrolled in any courses yet.")
    else:
        for e in enrollments:
            course = c.execute("SELECT * FROM courses WHERE course_id=?", (e[2],)).fetchone()
            st.subheader(course[1])
            st.progress(e[3] / 100)
            if e[4]:
                st.success("Completed! Certificate available.")

    st.button("Logout", on_click=lambda: st.session_state.clear())

def page_admin_login():
    st.title("Admin Login")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == "admin123":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid password")

def page_admin_dashboard():
    st.title("Admin Dashboard")
    st.subheader("Manage Courses")

    with st.form("add_course"):
        title = st.text_input("Course Title")
        subtitle = st.text_input("Subtitle")
        description = st.text_area("Description")
        price = st.number_input("Price (₹)", min_value=0.0, step=0.01)
        banner = st.text_input("Banner Path (URL)")
        submitted = st.form_submit_button("Add Course")
        if submitted:
            c.execute("INSERT INTO courses(title,subtitle,description,price,banner_path) VALUES (?,?,?,?,?)",
                      (title, subtitle, description, price, banner))
            conn.commit()
            st.success("Course added!")

    courses = c.execute("SELECT * FROM courses").fetchall()
    for course in courses:
        st.markdown(f"**{course[1]}** - {course[3]}")
        if st.button("Delete", key=f"del_{course[0]}"):
            c.execute("DELETE FROM courses WHERE course_id=?", (course[0],))
            conn.commit()
            st.warning("Course deleted!")
            st.experimental_rerun()

    st.subheader("All Students")
    users = c.execute("SELECT full_name,email,profession,institution FROM users").fetchall()
    for u in users:
        st.write(f"{u[0]} | {u[1]} | {u[2]} | {u[3]}")

# ---------------------------
# Navigation
# ---------------------------
menu_tabs = ["Home", "Sign Up", "Login", "Admin Login"]
choice = st.sidebar.radio("Navigate", menu_tabs)

if "page" not in st.session_state:
    st.session_state["page"] = "home"

if choice == "Home":
    page_home()
elif choice == "Sign Up":
    page_signup()
elif choice == "Login":
    page_login()
elif choice == "Admin Login":
    page_admin_login()

if st.session_state.get("page") == "student_dashboard":
    page_student_dashboard()
elif st.session_state.get("page") == "admin_dashboard":
    page_admin_dashboard()
