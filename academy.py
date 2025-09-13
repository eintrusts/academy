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

# Modules (lessons) table
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

def update_module(module_id, title, description, module_type):
    c.execute("UPDATE modules SET title=?, description=?, module_type=? WHERE module_id=?",
              (title, description, module_type, module_id))
    conn.commit()

def delete_module(module_id):
    c.execute("DELETE FROM modules WHERE module_id=?", (module_id,))
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
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc;}
.center-container {display: flex; flex-direction: row; align-items: center; justify-content: center; gap:10px;}
.center {text-align: center;}
button.enroll-btn {background-color:#4CAF50;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;}
</style>
""", unsafe_allow_html=True)

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
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}"):
                    st.session_state["edit_course"] = course
                    st.session_state["page"] = "edit_course"
                    st.experimental_rerun()
            if show_modules:
                modules = get_modules(course[0])
                if modules:
                    st.write("Modules:")
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")

# ---------------------------
# Central Header
# ---------------------------
def display_logo_and_title_center():
    st.markdown('<div class="center-container">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=80)
    st.markdown("<h2 style='font-family:Times New Roman;'>EinTrust Academy</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Home Page
# ---------------------------
def page_home():
    display_logo_and_title_center()
    tabs = st.tabs(["Courses", "Student", "Admin"])
    with tabs[0]:
        st.subheader("All Courses")
        display_courses(get_courses(), enroll=True, student_id=st.session_state.get("student", [None])[0] if "student" in st.session_state else None)
    with tabs[1]:
        page_student()
    with tabs[2]:
        page_admin()

# ---------------------------
# Student Page
# ---------------------------
def page_student():
    if "student" not in st.session_state:
        st.subheader("Student Access")
        sub_tabs = st.tabs(["Login", "Signup"])
        with sub_tabs[0]:
            email = st.text_input("Email ID", key="stu_login_email")
            password = st.text_input("Password", type="password", key="stu_login_pass")
            if st.button("Login", key="stu_login_btn"):
                student = authenticate_student(email, password)
                if student:
                    st.session_state["student"] = student
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials.")
        with sub_tabs[1]:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name", key="stu_signup_name")
                email = st.text_input("Email ID", key="stu_signup_email")
                password = st.text_input("Password", type="password", key="stu_signup_pass")
                gender = st.selectbox("Gender", ["Male","Female","Other"], key="stu_signup_gender")
                profession = st.text_input("Profession", key="stu_signup_prof")
                institution = st.text_input("Institution", key="stu_signup_inst")
                if st.form_submit_button("Signup"):
                    if not is_valid_email(email):
                        st.error("Enter a valid email address.")
                    elif not is_valid_password(password):
                        st.error("Weak password (8+ chars, uppercase, number, special char).")
                    else:
                        if add_student(full_name, email, password, gender, profession, institution):
                            st.success("Profile created! Please login.")
                            st.experimental_rerun()
                        else:
                            st.error("Email already registered.")
    else:
        student_dashboard()

def student_dashboard():
    student = st.session_state.get("student")
    tabs = st.tabs(["All Courses", "My Courses", "Edit Profile", "Logout"])
    with tabs[0]:
        st.subheader("All Courses")
        display_courses(get_courses(), enroll=True, student_id=student[0])
    with tabs[1]:
        st.subheader("My Courses")
        display_courses(get_student_courses(student[0]), show_modules=True)
    with tabs[2]:
        st.subheader("Edit Profile")
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
                    st.experimental_rerun()
                else:
                    st.error("Email already exists.")
    with tabs[3]:
        st.session_state.pop("student", None)
        st.success("Logged out successfully.")
        st.experimental_rerun()

# ---------------------------
# Admin Page
# ---------------------------
def page_admin():
    if "admin" not in st.session_state:
        st.subheader("Admin Login")
        admin_pass = st.text_input("Enter Admin Password", type="password")
        if st.button("Login as Admin"):
            if admin_pass == "eintrust2025":
                st.session_state["admin"] = True
                st.experimental_rerun()
            else:
                st.error("Wrong admin password.")
    else:
        admin_dashboard()

def admin_dashboard():
    tabs = st.tabs(["Dashboard", "Students", "Courses & Modules", "Logout"])
    with tabs[0]:
        st.subheader("Overview")
        st.write(f"Total Students: {c.execute('SELECT COUNT(*) FROM students').fetchone()[0]}")
        st.write(f"Total Courses: {c.execute('SELECT COUNT(*) FROM courses').fetchone()[0]}")
        st.write(f"Total Modules: {c.execute('SELECT COUNT(*) FROM modules').fetchone()[0]}")
    with tabs[1]:
        st.subheader("Students List")
        students = c.execute("SELECT * FROM students").fetchall()
        st.table([[s[0], s[1], s[2], s[4], s[5], s[6]] for s in students])
        for s in students:
            if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
                st.experimental_rerun()
    with tabs[2]:
        st.subheader("Manage Courses & Modules")
        courses = get_courses()
        display_courses(courses, editable=True, show_modules=True)
        st.markdown("---")
        with st.form("add_course_form"):
            title = st.text_input("Title", key="add_course_title")
            subtitle = st.text_input("Subtitle", key="add_course_sub")
            desc = st.text_area("Description", key="add_course_desc")
            price = st.number_input("Price", min_value=0.0, step=1.0, key="add_course_price")
            if st.form_submit_button("Add Course"):
                add_course(title, subtitle, desc, price)
                st.success("Course added!")
                st.experimental_rerun()
        with st.form("add_module_form"):
            if courses:
                course_id = st.selectbox("Select Course", [c[0] for c in courses], format_func=lambda x: c.execute("SELECT title FROM courses WHERE course_id=?", (x,)).fetchone()[0])
                mod_title = st.text_input("Module Title")
                mod_desc = st.text_area("Module Description")
                mod_type = st.selectbox("Module Type", ["Video","PDF","Quiz"])
                mod_file = st.file_uploader("Upload File", type=["pdf","mp4"], key="mod_file")
                mod_link = st.text_input("Module Link (Optional)")
                if st.form_submit_button("Add Module"):
                    file_bytes = convert_file_to_bytes(mod_file)
                    add_module(course_id, mod_title, mod_desc, mod_type, file_bytes, mod_link)
                    st.success("Module added!")
                    st.experimental_rerun()
    with tabs[3]:
        st.session_state.pop("admin", None)
        st.success("Admin logged out.")
        st.experimental_rerun()

# ---------------------------
# Run App
# ---------------------------
page_home()
