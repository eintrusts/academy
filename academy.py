import streamlit as st
import sqlite3
import re
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

# Student-Courses relation
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
.unique-btn button {
    background-color: #4CAF50 !important; 
    color: white !important; 
    border-radius: 8px !important; 
    border: none !important; 
    padding: 12px 25px !important; 
    font-weight: bold !important;
    width: 100%;
}
.unique-btn button:hover {background-color: #45a049 !important; color: #ffffff !important;}
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc;}
.section-header {border-bottom: 1px solid #333333; padding-bottom: 8px; margin-bottom: 10px; font-size: 20px;}
.center {text-align: center;}
</style>
""", unsafe_allow_html=True)

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
                <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
            </div>
            """, unsafe_allow_html=True)
            if enroll and student_id:
                if st.button("Enroll", key=f"enroll_{course[0]}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}", use_container_width=True):
                    st.session_state["edit_course"] = course
                    st.session_state["page"] = "edit_course"
                    st.experimental_rerun()
            if show_lessons:
                lessons = get_lessons(course[0])
                if lessons:
                    st.write("Lessons:")
                    for l in lessons:
                        st.write(f"- {l[2]} ({l[4]})")

# ---------------------------
# Common Layout for All Pages
# ---------------------------
def display_logo_and_title():
    st.markdown('<div class="center">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.markdown("<h2>EinTrust Academy</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Pages
# ---------------------------
def page_home():
    display_logo_and_title()
    student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
    courses = get_courses()
    display_courses(courses, enroll=True, student_id=student_id)

def page_signup():
    display_logo_and_title()
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
    display_logo_and_title()
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
    display_logo_and_title()
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.subheader(f"Welcome, {student[1]}")
        st.write("---")
        st.subheader("Available Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])

        st.subheader("Your Enrolled Courses")
        enrolled_courses = get_student_courses(student[0])
        display_courses(enrolled_courses, show_lessons=True)

        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

# ---------------------------
# Admin Pages
# ---------------------------
def page_admin():
    display_logo_and_title()
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    display_logo_and_title()
    st.header("Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Dashboard", "Students", "Courses & Lessons"])

    with tab1:
        st.subheader("Overview")
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
        display_courses(courses, editable=True, show_lessons=True)

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

        st.markdown("---")
        st.subheader("Add New Lesson")
        with st.form("add_lesson_form"):
            course_id = st.selectbox("Select Course", [c[0] for c in get_courses()])
            title = st.text_input("Lesson Title")
            desc = st.text_area("Lesson Description")
            lesson_type = st.selectbox("Type", ["Video", "PDF", "PPT", "Link"])
            uploaded_file = st.file_uploader("Upload File (if applicable)")
            link = st.text_input("External Link (if applicable)")
            if st.form_submit_button("Add Lesson"):
                file_bytes = convert_file_to_bytes(uploaded_file)
                add_lesson(course_id, title, desc, lesson_type, file_bytes, link)
                st.success("Lesson added!")
                st.experimental_rerun()

        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()

# ---------------------------
# Edit Course Page
# ---------------------------
def page_edit_course():
    display_logo_and_title()
    course = st.session_state.get("edit_course")
    if course:
        st.header(f"Edit Course: {course[1]}")
        with st.form("edit_course_form"):
            title = st.text_input("Title", value=course[1])
            subtitle = st.text_input("Subtitle", value=course[2])
            desc = st.text_area("Description", value=course[3])
            price = st.number_input("Price", value=course[4], min_value=0.0, step=1.0)
            if st.form_submit_button("Update Course"):
                update_course(course[0], title, subtitle, desc, price)
                st.success("Course updated!")
                st.session_state["page"] = "admin_dashboard"
                st.experimental_rerun()

# ---------------------------
# Main Navigation
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# Always show logo and tabs first
display_logo_and_title()
tabs = st.tabs(["Home", "Signup", "Login", "Admin"])
with tabs[0]: st.session_state["page"] = "home"; page_home()
with tabs[1]: st.session_state["page"] = "signup"; page_signup()
with tabs[2]: st.session_state["page"] = "login"; page_login()
with tabs[3]: st.session_state["page"] = "admin"; page_admin()

# Render individual pages if navigated programmatically
if st.session_state["page"] == "student_dashboard": page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard": page_admin_dashboard()
elif st.session_state["page"] == "edit_course": page_edit_course()
