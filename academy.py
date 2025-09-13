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
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; 
              box-shadow: 0px 4px 10px rgba(0,0,0,0.6); cursor:pointer; transition: transform 0.2s;}
.course-card:hover {transform: scale(1.02);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc;}
.center-container {display: flex; align-items: center; justify-content: center; gap: 10px;}
.center {text-align: center;}
.logo-img {width:100px;}
.course-button {background-color:#4CAF50;color:white;border:none;padding:6px 12px;border-radius:6px;margin-top:8px;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Central Header
# ---------------------------
def display_logo_and_title_center():
    st.markdown('<div class="center-container">', unsafe_allow_html=True)
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=100)
    st.markdown("<h2 style='font-family:Times New Roman; margin:0;'>EinTrust Academy</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Display Courses as Fully Clickable Cards
# ---------------------------
def display_courses_clickable(courses):
    if not courses:
        st.info("No courses available.")
        return
    cols = st.columns(2)
    for idx, course in enumerate(courses):
        with cols[idx % 2]:
            card_html = f"""
            <div class="course-card" onclick="window.parent.postMessage({{'course_id':{course[0]}}}, '*')">
                <div class="course-title">{course[1]}</div>
                <div class="course-subtitle">{course[2]}</div>
                <div class="course-desc">{course[3][:150]}...</div>
                <p><b>Price:</b> {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
                <button class="course-button">Enroll / View</button>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            # For Streamlit redirect logic
            if f"enroll_{course[0]}" not in st.session_state:
                st.session_state[f"enroll_{course[0]}"] = False
            if st.button(f"Enroll / View", key=f"btn_{course[0]}"):
                st.session_state["selected_course"] = course
                st.session_state["page"] = "student_dashboard"
                st.experimental_rerun()

# ---------------------------
# Pages
# ---------------------------
def page_home():
    courses = get_courses()
    display_courses_clickable(courses)

def page_student_tab():
    tabs = st.tabs(["Login / Signup"])
    with tabs[0]:
        st.header("Student Login or Signup")
        choice = st.radio("Choose Action:", ["Login","Signup"])
        if choice=="Signup":
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
                        else:
                            st.error("Email already registered.")
        else:
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

def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass=="eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

# ---------------------------
# Student Dashboard
# ---------------------------
def page_student_dashboard():
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login first.")
        return

    tabs = st.tabs(["All Courses","My Courses","Edit Profile","Logout"])
    
    with tabs[0]:
        st.subheader("All Courses")
        courses = get_courses()
        display_courses_clickable(courses)

    with tabs[1]:
        st.subheader("My Courses")
        enrolled_courses = get_student_courses(student[0])
        display_courses_clickable(enrolled_courses)

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
                else:
                    st.error("Email already exists.")

    with tabs[3]:
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

# ---------------------------
# Admin Dashboard
# ---------------------------
def page_admin_dashboard():
    tabs = st.tabs(["Dashboard","Students","Courses & Modules","Logout"])
    
    with tabs[0]:
        st.subheader("Overview")
        st.write(f"Total Students: {c.execute('SELECT COUNT(*) FROM students').fetchone()[0]}")
        st.write(f"Total Courses: {c.execute('SELECT COUNT(*) FROM courses').fetchone()[0]}")
        st.write(f"Total Modules: {c.execute('SELECT COUNT(*) FROM lessons').fetchone()[0]}")
    
    with tabs[1]:
        st.subheader("Manage Students")
        students = c.execute("SELECT * FROM students").fetchall()
        for s in students:
            st.write(f"{s[0]}. {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}")
            if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
                st.experimental_rerun()
    
    with tabs[2]:
        st.subheader("Manage Courses & Modules")
        courses = get_courses()
        for course in courses:
            st.markdown(f"**{course[1]}** - {course[2]}")
            modules = get_lessons(course[0])
            for m in modules:
                st.write(f"- {m[2]} ({m[4]})")
        st.markdown("---")
        with st.form("add_course_form"):
            title = st.text_input("Title")
            subtitle = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, step=1.0)
            if st.form_submit_button("Add Course"):
                add_course(title, subtitle, desc, price)
                st.experimental_rerun()
        with st.form("add_module_form"):
            course_id = st.selectbox("Select Course", [c[0] for c in get_courses()])
            title = st.text_input("Module Title")
            desc = st.text_area("Module Description")
            lesson_type = st.selectbox("Type", ["Video","PDF","PPT","Link"])
            uploaded_file = st.file_uploader("Upload File")
            link = st.text_input("External Link")
            if st.form_submit_button("Add Module"):
                add_lesson(course_id, title, desc, lesson_type, convert_file_to_bytes(uploaded_file), link)
                st.experimental_rerun()
    
    with tabs[3]:
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

# ---------------------------
# Main Navigation
# ---------------------------
display_logo_and_title_center()

tabs = st.tabs(["Courses","Student","Admin"])
with tabs[0]:
    page_home()
with tabs[1]:
    page_student_tab()
with tabs[2]:
    page_admin()
