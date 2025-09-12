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

# Courses
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL
)''')

# Lessons
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)''')

# Students
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

def get_lessons(course_id):
    return c.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_id ASC", (course_id,)).fetchall()

def add_course(title, subtitle, desc, price):
    c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?,?,?,?)",
              (title, subtitle, desc, price))
    conn.commit()

def delete_course(course_id):
    c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
    c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    conn.commit()

def add_lesson(course_id, title, content):
    c.execute("INSERT INTO lessons (course_id,title,content) VALUES (?,?,?)", (course_id,title,content))
    conn.commit()

def delete_lesson(lesson_id):
    c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson_id,))
    conn.commit()

def add_student(full_name, email, password, gender, profession, institution, profile_picture):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,profile_picture) VALUES (?,?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution, profile_picture))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    return c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        body {background-color: #0e1117; color: #fafafa;}
        .stTabs [role="tablist"] {justify-content: center;}
        .stTabs [role="tab"] {font-size: 18px; padding: 12px;}
        .course-card {
            background: #1e1e1e;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
        }
        .course-title {font-size: 22px; font-weight: bold;}
        .course-subtitle {font-size: 16px; color: #cccccc;}
        .course-desc {font-size: 14px; color: #bbbbbb;}
        .enroll-btn {
            background: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            text-align: center;
            cursor: pointer;
        }
        .enroll-btn:hover {background: #45a049;}
        .center-logo {display: flex; justify-content: center;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# PAGES
# ---------------------------

def page_home():
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=220)
    st.markdown('</div>', unsafe_allow_html=True)

    st.header("Available Courses")
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
    st.header("Create Profile")
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
                    st.success("Profile created successfully! Please login.")
                    st.session_state["page"] = "login"
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.success("Login successful!")
            st.session_state["student"] = student
            st.session_state["page"] = "dashboard"
        else:
            st.error("Invalid credentials.")

def page_dashboard():
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.write(f"Welcome, {student[1]}!")
        st.write("Your enrolled courses will appear here.")
    else:
        st.warning("Please login first.")

def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "admin123":  # Secure password recommended
            st.success("Welcome Admin")
            st.subheader("Manage Courses")

            # Add Course
            with st.form("add_course_form"):
                title = st.text_input("Course Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price (0 for free)", min_value=0.0, step=100.0)
                add_course_btn = st.form_submit_button("Add Course")
                if add_course_btn:
                    add_course(title, subtitle, desc, price)
                    st.success("Course added successfully!")

            # Delete Course
            courses = get_courses()
            course_options = {f"{c[1]} (ID: {c[0]})": c[0] for c in courses}
            if courses:
                selected_course = st.selectbox("Select course to delete", list(course_options.keys()))
                if st.button("Delete Course"):
                    delete_course(course_options[selected_course])
                    st.warning("Course deleted.")

            # Add Lessons
            if courses:
                selected_course_lesson = st.selectbox("Select course to add lesson", list(course_options.keys()), key="lesson_add")
                with st.form("add_lesson_form"):
                    l_title = st.text_input("Lesson Title")
                    l_content = st.text_area("Lesson Content")
                    add_lesson_btn = st.form_submit_button("Add Lesson")
                    if add_lesson_btn:
                        add_lesson(course_options[selected_course_lesson], l_title, l_content)
                        st.success("Lesson added successfully!")

            # Delete Lesson
            lessons = []
            if courses:
                selected_course_for_lessons = st.selectbox("Select course to view lessons", list(course_options.keys()), key="lesson_view")
                lessons = get_lessons(course_options[selected_course_for_lessons])
            if lessons:
                lesson_options = {f"{l[2]} (ID: {l[0]})": l[0] for l in lessons}
                selected_lesson = st.selectbox("Select lesson to delete", list(lesson_options.keys()))
                if st.button("Delete Lesson"):
                    delete_lesson(lesson_options[selected_lesson])
                    st.warning("Lesson deleted.")

            st.subheader("All Students")
            students = c.execute("SELECT full_name,email,profession,institution FROM students").fetchall()
            for s in students:
                st.write(s)
        else:
            st.error("Wrong admin password.")

# ---------------------------
# MAIN NAVIGATION
# ---------------------------
st.markdown('<div class="center-logo">', unsafe_allow_html=True)
st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=220)
st.markdown('</div>', unsafe_allow_html=True)

tabs = st.tabs(["Home", "Signup", "Login", "Admin"])

with tabs[0]:
    page_home()
with tabs[1]:
    page_signup()
with tabs[2]:
    if "page" in st.session_state and st.session_state["page"]=="dashboard":
        page_dashboard()
    else:
        page_login()
with tabs[3]:
    page_admin()
