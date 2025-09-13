import streamlit as st
import sqlite3
import re

# ---------------------------
# DB Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL
)''')

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

c.execute('''CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)''')

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
    return uploaded_file.read() if uploaded_file else None

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

def update_student(student_id, full_name, email, password, gender, profession, institution):
    try:
        c.execute("""UPDATE students SET full_name=?, email=?, password=?, gender=?, profession=?, institution=? 
                     WHERE student_id=?""",
                  (full_name, email, password, gender, profession, institution, student_id))
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

def format_price(price):
    return "Free" if price==0 else f"₹{price:,.0f}"

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
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc; margin-bottom: 12px;}
.enroll-btn {background-color:#0a84ff;color:white;border:none;padding:6px 10px;border-radius:6px; cursor:pointer;}
.center-container {display: flex; flex-direction: row; align-items: center; justify-content: flex-start; gap:15px;}
.center-title {font-size:28px; font-weight:bold; color:#f0f0f0; font-family:'Times New Roman', serif;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Central Header (Logo + Name)
# ---------------------------
def display_logo_and_title_center():
    st.markdown('<div class="center-container">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=50)
    st.markdown("<div class='center-title'>EinTrust Academy</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Pages: Signup/Login
# ---------------------------
def page_signup():
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        if st.form_submit_button("Submit"):
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Weak password (8+ chars, uppercase, number, special char).")
            else:
                if add_student(full_name, email, password, gender, profession, institution):
                    st.success("Profile created! Please login.")
                    st.session_state["page"] = "home"
                    st.session_state["active_tab"] = "Student"
                    st.session_state["student_tab"] = "Login"
                else:
                    st.error("Email already registered.")

def page_login(course_to_enroll=None):
    st.header("Student Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            if course_to_enroll:
                enroll_student_in_course(student[0], course_to_enroll)
                st.success("Enrolled successfully!")
        else:
            st.error("Invalid credentials.")

# ---------------------------
# Display Courses
# ---------------------------
def display_courses(courses, enroll=False, student_id=None, show_lessons=False, editable=False):
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
                <div class="course-desc">{course[3][:150]}...</div>
                <p><b>Price:</b> {format_price(course[4])}</p>
            </div>
            """, unsafe_allow_html=True)
            if enroll:
                if st.button("Enroll", key=f"enroll_{course[0]}"):
                    if "student" not in st.session_state:
                        st.session_state["page"] = "home"
                        st.session_state["active_tab"] = "Student"
                        st.session_state["student_tab"] = "Login"
                        st.session_state["course_to_enroll"] = course[0]
                    else:
                        enroll_student_in_course(st.session_state["student"][0], course[0])
                        st.success(f"Enrolled in {course[1]}")
                        st.session_state["page"] = "student_dashboard"

# ---------------------------
# Student Dashboard
# ---------------------------
def page_student_dashboard():
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login first.")
        return
    tabs = st.tabs(["All Courses", "My Courses", "Edit Profile", "Logout"])
    with tabs[0]:
        display_courses(get_courses(), enroll=True, student_id=student[0])
    with tabs[1]:
        display_courses(get_student_courses(student[0]), show_lessons=True)
    with tabs[2]:
        with st.form("edit_profile_form"):
            full_name = st.text_input("Full Name", value=student[1])
            email = st.text_input("Email ID", value=student[2])
            password = st.text_input("Password", type="password", value=student[3])
            gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(student[4]))
            profession = st.text_input("Profession", value=student[5])
            institution = st.text_input("Institution", value=student[6])
            if st.form_submit_button("Update Profile"):
                if update_student(student[0], full_name, email, password, gender, profession, institution):
                    st.success("Profile updated!")
                    st.session_state["student"] = authenticate_student(email, password)
                else:
                    st.error("Email already exists.")
    with tabs[3]:
        st.info("Logged out successfully.")
        st.session_state.clear()
        st.session_state["page"] = "home"

# ---------------------------
# Admin Pages
# ---------------------------
def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    tabs = st.tabs(["Dashboard", "Students", "Courses & Lessons", "Logout"])
    with tabs[0]:
        st.subheader("Overview")
        st.write(f"Total Students: {c.execute('SELECT COUNT(*) FROM students').fetchone()[0]}")
        st.write(f"Total Courses: {c.execute('SELECT COUNT(*) FROM courses').fetchone()[0]}")
        st.write(f"Total Lessons: {c.execute('SELECT COUNT(*) FROM lessons').fetchone()[0]}")
    with tabs[1]:
        st.subheader("Manage Students")
        students = c.execute("SELECT * FROM students").fetchall()
        for s in students:
            st.write(f"{s[0]}. {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}")
            if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
    with tabs[2]:
        st.subheader("Manage Courses & Lessons")
        display_courses(get_courses(), editable=True, show_lessons=True)
    with tabs[3]:
        st.info("Admin logged out successfully.")
        st.session_state.clear()
        st.session_state["page"] = "home"

# ---------------------------
# Main Home Page
# ---------------------------
def page_home():
    active_tab = st.session_state.get("active_tab", "Courses")
    student_tab = st.session_state.get("student_tab", "Login")
    course_to_enroll = st.session_state.get("course_to_enroll")
    tabs = st.tabs(["Courses", "Student", "Admin"])
    with tabs[0]:
        display_courses(get_courses(), enroll=True)
    with tabs[1]:
        sub_tabs = st.tabs(["Login", "Signup"])
        if student_tab=="Login":
            with sub_tabs[0]:
                page_login(course_to_enroll)
        else:
            with sub_tabs[1]:
                page_signup()
    with tabs[2]:
        page_admin()

# ---------------------------
# Main
# ---------------------------
display_logo_and_title_center()
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"]=="home":
    page_home()
elif st.session_state["page"]=="student_dashboard":
    page_student_dashboard()
elif st.session_state["page"]=="admin_dashboard":
    page_admin_dashboard()
