import streamlit as st
import sqlite3
import re

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

# Modules table
c.execute('''CREATE TABLE IF NOT EXISTS modules (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    module_type TEXT,
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

def get_modules(course_id):
    return c.execute("SELECT * FROM modules WHERE course_id=? ORDER BY module_id ASC", (course_id,)).fetchall()

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
    c.execute("DELETE FROM modules WHERE course_id=?", (course_id,))
    conn.commit()

def add_module(course_id, title, description, module_type, file, link):
    c.execute("INSERT INTO modules (course_id, title, description, module_type, file, link) VALUES (?,?,?,?,?,?)",
              (course_id, title, description, module_type, file, link))
    conn.commit()

def update_module(module_id, title, description, module_type, file, link):
    c.execute("""UPDATE modules SET title=?, description=?, module_type=?, file=?, link=? 
                 WHERE module_id=?""", (title, description, module_type, file, link, module_id))
    conn.commit()

# ---------------------------
# Page Config + CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0; font-family: 'Arial', sans-serif;}
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
.course-desc {font-size: 14px; color: #cccccc;}
.center-container {display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 15px;}
.center {text-align: center;}
button.enroll-btn {background-color:#0066ff;color:white;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Central Header
# ---------------------------
def display_logo_and_title():
    st.markdown('<div class="center-container">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=80)
    st.markdown("<h2 style='font-family:Times New Roman; color:#f5f5f5;'>EinTrust Academy</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Display Courses
# ---------------------------
def display_courses(courses, enroll=False, student_id=None, show_modules=False, editable=False):
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
                key = f"enroll_{student_id}_{course[0]}"
                if st.button("Enroll", key=key):
                    st.session_state["enroll_course"] = course[0]
                    st.session_state["page"] = "student_dashboard"
                    st.session_state["student_id_for_enroll"] = student_id
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}"):
                    st.session_state["edit_course"] = course
                    st.session_state["page"] = "edit_course"
            if show_modules:
                modules = get_modules(course[0])
                if modules:
                    st.write("Modules:")
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")

# ---------------------------
# Pages
# ---------------------------
def page_home():
    display_logo_and_title()
    tabs = st.tabs(["Courses", "Student", "Admin"])
    with tabs[0]:
        courses = get_courses()
        display_courses(courses, enroll=True)
    with tabs[1]:
        page_student()
    with tabs[2]:
        page_admin()

def page_student():
    # Handle enroll redirect
    student_id_for_enroll = st.session_state.get("student_id_for_enroll")
    enroll_course = st.session_state.get("enroll_course")
    
    if "student" not in st.session_state and enroll_course and student_id_for_enroll:
        st.info("Please login or signup to enroll in the course.")
    
    tabs = st.tabs(["Login/Signup", "Dashboard"])
    with tabs[0]:
        st.header("Student Login / Signup")
        action = st.radio("Action", ["Login", "Signup"])
        if action=="Signup":
            with st.form("signup_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email ID")
                password = st.text_input("Password", type="password")
                gender = st.selectbox("Gender", ["Male","Female","Other"])
                profession = st.text_input("Profession")
                institution = st.text_input("Institution/College")
                submit = st.form_submit_button("Signup")
                if submit:
                    if not is_valid_email(email):
                        st.error("Invalid Email.")
                    elif not is_valid_password(password):
                        st.error("Password must contain uppercase, number, special char, min 8 chars.")
                    elif add_student(full_name,email,password,gender,profession,institution):
                        st.success("Signup successful. Please login.")
                    else:
                        st.error("Email already registered.")
        else:
            with st.form("login_form"):
                email = st.text_input("Email ID", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                submit = st.form_submit_button("Login")
                if submit:
                    student = authenticate_student(email,password)
                    if student:
                        st.session_state["student"] = student
                        st.success("Login successful.")
                    else:
                        st.error("Invalid credentials.")
    with tabs[1]:
        if "student" in st.session_state:
            student_dashboard()
        else:
            st.info("Login to access dashboard.")

def student_dashboard():
    student = st.session_state.get("student")
    if not student:
        st.info("Login first.")
        return
    tabs = st.tabs(["My Courses", "All Courses", "Edit Profile", "Logout"])
    with tabs[0]:
        my_courses = get_student_courses(student[0])
        display_courses(my_courses, show_modules=True)
    with tabs[1]:
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])
    with tabs[2]:
        st.header("Edit Profile")
        with st.form("edit_profile"):
            full_name = st.text_input("Full Name", student[1])
            email = st.text_input("Email", student[2])
            password = st.text_input("Password", student[3], type="password")
            gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(student[4]))
            profession = st.text_input("Profession", student[5])
            institution = st.text_input("Institution", student[6])
            submit = st.form_submit_button("Update")
            if submit:
                if update_student(student[0], full_name,email,password,gender,profession,institution):
                    st.success("Profile updated.")
                    st.session_state["student"] = authenticate_student(email,password)
                else:
                    st.error("Email already exists.")
    with tabs[3]:
        if st.button("Logout"):
            st.session_state.pop("student", None)
            st.success("Logged out.")
            st.experimental_rerun()

def page_admin():
    tabs = st.tabs(["Dashboard","Students","Courses & Modules","Logout"])
    with tabs[0]:
        st.header("Admin Dashboard")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        st.write(f"Total Students: {total_students}")
        st.write(f"Total Courses: {total_courses}")
        st.write(f"Total Modules: {total_modules}")
    with tabs[1]:
        st.header("Students")
        students = c.execute("SELECT * FROM students").fetchall()
        if students:
            for s in students:
                st.write(f"{s[0]} | {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}")
                if st.button(f"Delete {s[0]}", key=f"delete_student_{s[0]}"):
                    c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                    conn.commit()
                    st.success("Student deleted.")
                    st.experimental_rerun()
        else:
            st.info("No students registered.")
    with tabs[2]:
        st.header("Courses")
        courses = get_courses()
        display_courses(courses, editable=True, show_modules=True)
        st.subheader("Add New Course")
        with st.form("add_course"):
            title = st.text_input("Course Title")
            subtitle = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, step=100.0)
            submit = st.form_submit_button("Add Course")
            if submit:
                add_course(title, subtitle, desc, price)
                st.success("Course added.")
                st.experimental_rerun()
    with tabs[3]:
        if st.button("Logout"):
            st.success("Admin logged out.")
            st.experimental_rerun()

# ---------------------------
# Run App
# ---------------------------
page_home()
