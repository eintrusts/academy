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
    c.execute("UPDATE modules SET title=?, description=?, module_type=?, file=?, link=? WHERE module_id=?",
              (title, description, module_type, file, link, module_id))
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
.center-container {display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 10px;}
.center {text-align: center; font-family: 'Times New Roman', serif;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
def display_logo_and_title():
    col1, col2 = st.columns([1,4])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=120)
    with col2:
        st.markdown("<h2 class='center'>EinTrust Academy</h2>", unsafe_allow_html=True)

# ---------------------------
# Display Courses
# ---------------------------
def display_courses(courses, enroll=False, student_id=None, page_prefix="home"):
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
            # Enroll button below card
            if enroll and student_id:
                key = f"{page_prefix}_enroll_{student_id}_{course[0]}"
                if st.button("Enroll", key=key):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]} successfully!")

# ---------------------------
# Home Page
# ---------------------------
def page_home():
    display_logo_and_title()
    tabs = st.tabs(["Courses","Student","Admin"])
    with tabs[0]:
        st.subheader("All Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=st.session_state.get("student_id", 0), page_prefix="home")
    with tabs[1]:
        page_student()
    with tabs[2]:
        page_admin()

# ---------------------------
# Student Page
# ---------------------------
def page_student():
    tabs = st.tabs(["Login/Signup", "My Courses", "Edit Profile", "Logout"])
    student = st.session_state.get("student")

    # Login/Signup Tab
    with tabs[0]:
        if student:
            st.success(f"Logged in as {student[1]}")
        else:
            st.subheader("Student Login / Signup")
            with st.form("student_login"):
                email = st.text_input("Email ID")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login")
                if login_btn:
                    s = authenticate_student(email, password)
                    if s:
                        st.session_state["student"] = s
                        st.session_state["student_id"] = s[0]
                        st.success("Login Successful")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")
            with st.form("student_signup"):
                st.subheader("Signup")
                full_name = st.text_input("Full Name", key="signup_name")
                email = st.text_input("Email ID", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password")
                gender = st.selectbox("Gender", ["Male","Female","Other"])
                profession = st.text_input("Profession")
                institution = st.text_input("Institution")
                signup_btn = st.form_submit_button("Signup")
                if signup_btn:
                    if not is_valid_email(email):
                        st.error("Enter valid email")
                    elif not is_valid_password(password):
                        st.error("Password must have 8+ chars, uppercase, number, special char")
                    else:
                        if add_student(full_name,email,password,gender,profession,institution):
                            st.success("Signup successful! Login now.")
                        else:
                            st.error("Email already exists")

    # My Courses Tab
    with tabs[1]:
        if student:
            enrolled_courses = get_student_courses(student[0])
            st.subheader("My Courses")
            display_courses(enrolled_courses, enroll=False, page_prefix="student")
        else:
            st.info("Login to see your courses")

    # Edit Profile Tab
    with tabs[2]:
        if student:
            st.subheader("Edit Profile")
            s = student
            with st.form("edit_profile"):
                full_name = st.text_input("Full Name", value=s[1])
                email = st.text_input("Email", value=s[2])
                password = st.text_input("Password", type="password", value=s[3])
                gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(s[4]))
                profession = st.text_input("Profession", value=s[5])
                institution = st.text_input("Institution", value=s[6])
                update_btn = st.form_submit_button("Update Profile")
                if update_btn:
                    if update_student(s[0], full_name,email,password,gender,profession,institution):
                        st.success("Profile updated successfully")
                        st.session_state["student"] = authenticate_student(email,password)
                        st.experimental_rerun()
                    else:
                        st.error("Email already exists")

    # Logout Tab
    with tabs[3]:
        if student:
            if st.button("Logout", key="student_logout"):
                st.session_state.pop("student")
                st.session_state.pop("student_id")
                st.success("Logged out")
                st.experimental_rerun()
        else:
            st.info("You are not logged in")

# ---------------------------
# Admin Page
# ---------------------------
def page_admin():
    admin_tabs = st.tabs(["Dashboard","Manage Students","Manage Courses & Modules","Logout"])
    with admin_tabs[0]:
        admin_dashboard()
    with admin_tabs[1]:
        manage_students()
    with admin_tabs[2]:
        manage_courses_modules()
    with admin_tabs[3]:
        if st.button("Logout", key="admin_logout"):
            st.success("Logged out")
            st.experimental_rerun()

# ---------------------------
# Admin Dashboard
# ---------------------------
def admin_dashboard():
    st.subheader("Admin Dashboard")
    total_courses = len(get_courses())
    total_students = len(c.execute("SELECT * FROM students").fetchall())
    st.markdown(f"**Total Courses:** {total_courses}  |  **Total Students:** {total_students}")

# ---------------------------
# Manage Students
# ---------------------------
def manage_students():
    st.subheader("All Students")
    students = c.execute("SELECT * FROM students").fetchall()
    if students:
        for idx, s in enumerate(students):
            cols = st.columns([1,2,2,2,2,2,1])
            cols[0].write(s[0])
            cols[1].write(s[1])
            cols[2].write(s[2])
            cols[3].write(s[4])
            cols[4].write(s[5])
            cols[5].write(s[6])
            key_del = f"del_student_{s[0]}_{idx}"
            if cols[6].button("Delete", key=key_del):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
                st.experimental_rerun()
    else:
        st.info("No students available.")

# ---------------------------
# Manage Courses & Modules
# ---------------------------
def manage_courses_modules():
    st.subheader("Courses")
    courses = get_courses()
    if courses:
        for c_idx, course in enumerate(courses):
            with st.expander(f"{course[1]} ({course[2]})"):
                title = st.text_input("Title", value=course[1], key=f"course_title_{course[0]}_{c_idx}")
                subtitle = st.text_input("Subtitle", value=course[2], key=f"course_subtitle_{course[0]}_{c_idx}")
                desc = st.text_area("Description", value=course[3], key=f"course_desc_{course[0]}_{c_idx}")
                price = st.number_input("Price", min_value=0.0, value=course[4], key=f"course_price_{course[0]}_{c_idx}")
                if st.button("Update Course", key=f"update_course_{course[0]}_{c_idx}"):
                    update_course(course[0], title, subtitle, desc, price)
                    st.success("Course updated successfully")
                    st.experimental_rerun()
                if st.button("Delete Course", key=f"delete_course_{course[0]}_{c_idx}"):
                    delete_course(course[0])
                    st.success("Course deleted")
                    st.experimental_rerun()
                # Modules
                modules = get_modules(course[0])
                st.markdown("**Modules**")
                for m_idx, mod in enumerate(modules):
                    mod_title = st.text_input("Module Title", value=mod[2], key=f"mod_title_{mod[0]}_{m_idx}")
                    mod_desc = st.text_area("Module Desc", value=mod[3], key=f"mod_desc_{mod[0]}_{m_idx}")
                    mod_type = st.selectbox("Module Type", ["Video","PDF","Link"], index=["Video","PDF","Link"].index(mod[4]), key=f"mod_type_{mod[0]}_{m_idx}")
                    mod_link = st.text_input("Link (if any)", value=mod[6] if mod[6] else "", key=f"mod_link_{mod[0]}_{m_idx}")
                    if st.button("Update Module", key=f"update_mod_{mod[0]}_{m_idx}"):
                        update_module(mod[0], mod_title, mod_desc, mod_type, None, mod_link)
                        st.success("Module updated")
                        st.experimental_rerun()
                st.markdown("---")
    else:
        st.info("No courses available.")

# ---------------------------
# Run App
# ---------------------------
if "student" not in st.session_state:
    st.session_state["student"] = None
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None

page_home()
