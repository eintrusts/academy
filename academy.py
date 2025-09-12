import streamlit as st
import sqlite3
import re
from PIL import Image
import io

# ---------------------------
# DB Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Courses table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL
)''')

# Students table
c.execute('''CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT,
    profile_picture BLOB
)''')

conn.commit()

# ---------------------------
# Utility Functions
# ---------------------------
def is_valid_email(email):
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email)

def is_valid_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

def convert_image_to_bytes(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    return None

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def add_student(full_name, email, password, gender, profession, institution, profile_picture):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,profile_picture) VALUES (?,?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution, profile_picture))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    student = c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
    return student

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

# ---------------------------
# Custom Dark Theme CSS
# ---------------------------
st.markdown("""
    <style>
        body {
            background-color: #0d0f12;
            color: #e0e0e0;
        }
        .stApp {
            background-color: #0d0f12;
            color: #e0e0e0;
        }
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > textarea {
            background-color: #1e1e1e;
            color: #f5f5f5;
            border: 1px solid #333333;
            border-radius: 6px;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
        }
        .stButton button:hover {
            background-color: #45a049;
            color: #ffffff;
        }
        .course-card {
            background: #1c1c1c;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.6);
        }
        .course-title {
            font-size: 22px;
            font-weight: bold;
            color: #f0f0f0;
        }
        .course-subtitle {
            font-size: 16px;
            color: #b0b0b0;
        }
        .course-desc {
            font-size: 14px;
            color: #cccccc;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# PAGES
# ---------------------------
def page_home():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("📚 Available Courses")
    courses = get_courses()
    if not courses:
        st.info("No courses available yet.")
    else:
        for course in courses:
            with st.container():
                st.markdown(f"""
                <div class="course-card">
                    <div class="course-title">{course[1]}</div>
                    <div class="course-subtitle">{course[2]}</div>
                    <div class="course-desc">{course[3][:150]}...</div>
                    <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Enroll in {course[1]}", key=f"enroll_{course[0]}"):
                    st.session_state["page"] = "signup"

def page_signup():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("📝 Create Profile")
    with st.form("signup_form"):
        profile_picture = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"])
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            else:
                img_bytes = convert_image_to_bytes(profile_picture)
                success = add_student(full_name, email, password, gender, profession, institution, img_bytes)
                if success:
                    st.success("✅ Profile created successfully! Please login.")
                    st.session_state["page"] = "login"
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("🔐 Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.success("✅ Login successful! Redirecting...")
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials.")

def page_student_dashboard():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("🎓 Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.write(f"Welcome, **{student[1]}** 👋")
        st.write("Your enrolled courses will appear here soon.")
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

def page_admin():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("👩‍💻 Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":  # Change this for security
            st.success("✅ Welcome Team, Redirecting...")
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("❌ Wrong admin password.")

def page_admin_dashboard():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("📊 Admin Dashboard")

    st.subheader("All Students")
    students = c.execute("SELECT full_name,email,profession,institution FROM students").fetchall()
    if students:
        for s in students:
            st.write(s)
    else:
        st.info("No students registered yet.")

    st.subheader("All Courses")
    courses = get_courses()
    if courses:
        for c_row in courses:
            st.write(c_row)
    else:
        st.info("No courses available.")

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# ---------------------------
# MAIN NAVIGATION
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    tabs = st.tabs(["Home", "Signup", "Login", "Admin"])
    with tabs[0]:
        page_home()
    with tabs[1]:
        page_signup()
    with tabs[2]:
        page_login()
    with tabs[3]:
        page_admin()

elif st.session_state["page"] == "signup":
    page_signup()
elif st.session_state["page"] == "login":
    page_login()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
