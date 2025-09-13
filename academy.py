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

# Lessons table
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    lesson_type TEXT,
    file BLOB,
    link TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)''')

# Students table
c.execute('''CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)''')

# Student-Courses relation table
c.execute('''CREATE TABLE IF NOT EXISTS student_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
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

def convert_file_to_bytes(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.read()
    return None

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def get_lessons(course_id):
    return c.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_id ASC", (course_id,)).fetchall()

def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    return c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()

def enroll_student_in_course(student_id, course_id):
    existing = c.execute("SELECT * FROM student_courses WHERE student_id=? AND course_id=?", (student_id, course_id)).fetchone()
    if not existing:
        c.execute("INSERT INTO student_courses (student_id, course_id) VALUES (?,?)", (student_id, course_id))
        conn.commit()

def get_student_courses(student_id):
    return c.execute(
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price 
           FROM courses JOIN student_courses 
           ON courses.course_id = student_courses.course_id 
           WHERE student_courses.student_id=?''', (student_id,)).fetchall()

def add_course(title, subtitle, description, price):
    c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?,?,?,?)", (title, subtitle, description, price))
    conn.commit()
    return c.lastrowid

def update_course(course_id, title, subtitle, description, price):
    c.execute("UPDATE courses SET title=?, subtitle=?, description=?, price=? WHERE course_id=?",
              (title, subtitle, description, price, course_id))
    conn.commit()

def delete_course(course_id):
    c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
    c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    conn.commit()

def add_lesson(course_id, title, description, lesson_type, file, link):
    c.execute("INSERT INTO lessons (course_id, title, description, lesson_type, file, link) VALUES (?,?,?,?,?,?)",
              (course_id, title, description, lesson_type, file, link))
    conn.commit()

def update_lesson(lesson_id, title, description, lesson_type, file, link):
    c.execute("UPDATE lessons SET title=?, description=?, lesson_type=?, file=?, link=? WHERE lesson_id=?",
              (title, description, lesson_type, file, link, lesson_id))
    conn.commit()

def delete_lesson(lesson_id):
    c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson_id,))
    conn.commit()

# ---------------------------
# Page Config + CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

st.markdown("""
    <style>
        body {background-color: #0d0f12; color: #e0e0e0;}
        .stApp {background-color: #0d0f12; color: #e0e0e0;}
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > textarea,
        .stNumberInput > div > input {
            background-color: #1e1e1e; color: #f5f5f5; border: 1px solid #333333; border-radius: 6px;
        }
        .unique-btn button {background-color: #4CAF50 !important; color: white !important; border-radius: 8px !important; border: none !important; padding: 10px 20px !important; font-weight: bold !important;}
        .unique-btn button:hover {background-color: #45a049 !important; color: #ffffff !important;}
        .course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
        .course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
        .course-subtitle {font-size: 16px; color: #b0b0b0;}
        .course-desc {font-size: 14px; color: #cccccc;}
        .course-footer {display: flex; justify-content: space-between; margin-top: 12px;}
        .admin-toggle button {background-color: #2e2e2e !important; color: #ffffff !important; border-radius: 8px !important; padding: 10px 16px !important; margin-right: 10px;}
        .admin-toggle button:hover {background-color: #4CAF50 !important; color: white !important;}
        .section-header {border-bottom: 1px solid #333333; padding-bottom: 8px; margin-bottom: 10px; font-size: 20px;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Course Display Function
# ---------------------------
def display_courses_grid(courses, student_id=None, enroll_redirect=True):
    if not courses:
        st.info("No courses available.")
        return
    cols = st.columns(2)
    for idx, course in enumerate(courses):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="course-card">
                <div class="course-title">{course[1]}</div>
                <div class="course-subtitle">{course[2]}</div>
                <div class="course-desc">{course[3]}</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button("Enroll", key=f"enroll_{course[0]}"):
                    if student_id:
                        enroll_student_in_course(student_id, course[0])
                        st.success(f"Enrolled in {course[1]}!")
                    else:
                        st.session_state["page"] = "signup"
                        st.experimental_rerun()
            with col2:
                st.markdown(f"**₹{course[4]:,.0f}**")

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Courses")
    courses = get_courses()
    display_courses_grid(courses)

def page_signup():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Create Profile")
    with st.form("signup_form"):
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
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Please login.")
                    st.session_state["page"] = "login"
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

def page_student_dashboard():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.subheader(f"Welcome, {student[1]}")
        st.write("---")
        st.subheader("Your Enrolled Courses")
        courses = get_student_courses(student[0])
        display_courses_grid(courses, student_id=student[0], enroll_redirect=False)
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

# ---------------------------
# ADMIN PAGES
# ---------------------------
def page_admin():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Admin Dashboard")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

    tab1, tab2, tab3 = st.tabs(["Dashboard", "Students", "Courses & Lessons"])

    with tab1:
        st.subheader("Dashboard Overview")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_lessons = c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        st.write(f"Total Students: {total_students}")
        st.write(f"Total Courses: {total_courses}")
        st.write(f"Total Lessons: {total_lessons}")

    with tab2:
        st.subheader("Manage Students")
        students = c.execute("SELECT * FROM students").fetchall()
        for s in students:
            st.write(f"{s[0]}. {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}")
            if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
                st.success(f"Deleted {s[1]}")
                st.experimental_rerun()

    with tab3:
        st.subheader("Manage Courses & Lessons")
        courses = get_courses()
        for course in courses:
            st.markdown(f"### {course[1]} | ₹{course[4]:,.0f}")
            st.write(course[3])
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit Course", key=f"edit_course_{course[0]}"):
                    st.session_state["edit_course"] = course[0]
                    st.session_state["page"] = "edit_course"
                    st.experimental_rerun()
            with col2:
                if st.button(f"Delete Course", key=f"del_course_{course[0]}"):
                    delete_course(course[0])
                    st.success(f"Deleted {course[1]}")
                    st.experimental_rerun()

            lessons = get_lessons(course[0])
            if lessons:
                st.markdown("**Lessons:**")
                for l in lessons:
                    st.write(f"- {l[2]} ({l[4]})")
                    col_l1, col_l2 = st.columns(2)
                    with col_l1:
                        if st.button(f"Edit Lesson {l[2]}", key=f"edit_lesson_{l[0]}"):
                            st.session_state["edit_lesson"] = l[0]
                            st.session_state["page"] = "edit_lesson"
                            st.experimental_rerun()
                    with col_l2:
                        if st.button(f"Delete Lesson {l[2]}", key=f"del_lesson_{l[0]}"):
                            delete_lesson(l[0])
                            st.success(f"Deleted lesson {l[2]}")
                            st.experimental_rerun()

        st.markdown("---")
        st.subheader("Add New Course")
        with st.form("add_course_form"):
            title = st.text_input("Title")
            subtitle = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, step=1.0)
            if st.form_submit_button("Add Course"):
                add_course(title, subtitle, desc, price)
                st.success("Course added!")
                st.experimental_rerun()

# ---------------------------
# Main Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    tabs = st.tabs(["Home", "Signup", "Login", "Admin"])
    with tabs[0]: page_home()
    with tabs[1]: page_signup()
    with tabs[2]: page_login()
    with tabs[3]: page_admin()
elif st.session_state["page"] == "signup": page_signup()
elif st.session_state["page"] == "login": page_login()
elif st.session_state["page"] == "student_dashboard": page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard": page_admin_dashboard()
