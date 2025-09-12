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
    institution TEXT,
    profile_picture BLOB
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
        .unique-btn button {background-color: #4CAF50 !important; color: white !important; border-radius: 8px !important; border: none !important; padding: 10px 20px !important; font-weight: bold !important;}
        .unique-btn button:hover {background-color: #45a049 !important; color: #ffffff !important;}
        .course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
        .course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
        .course-subtitle {font-size: 16px; color: #b0b0b0;}
        .course-desc {font-size: 14px; color: #cccccc;}
        .admin-toggle button {background-color: #2e2e2e !important; color: #ffffff !important; border-radius: 8px !important; padding: 10px 16px !important; margin-right: 10px;}
        .admin-toggle button:hover {background-color: #4CAF50 !important; color: white !important;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Course Display Function
# ---------------------------
def display_courses_grid(courses, enroll_option=False, student_id=None, show_lessons=False):
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
            if enroll_option and student_id:
                if st.button(f"Enroll in {course[1]}", key=f"enroll_{course[0]}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if show_lessons:
                lessons = get_lessons(course[0])
                if lessons:
                    st.write("Lessons:")
                    for l in lessons:
                        st.write(f"- {l[2]} ({l[4]})")

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    st.header("Available Courses")
    courses = get_courses()
    display_courses_grid(courses)

def page_signup():
    st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
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
                img_bytes = convert_file_to_bytes(profile_picture)
                success = add_student(full_name, email, password, gender, profession, institution, img_bytes)
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
        if student[7]:
            st.image(Image.open(io.BytesIO(student[7])), width=150)
        st.subheader(f"{student[1]}")
        st.write(f"Email: {student[2]}")
        st.write(f"Gender: {student[4]}")
        st.write(f"Profession: {student[5]}")
        st.write(f"Institution: {student[6]}")
        st.write("---")
        st.subheader("Your Enrolled Courses")
        courses = get_student_courses(student[0])
        if not courses:
            st.info("You have not enrolled in any courses yet.")
        else:
            for course in courses:
                st.markdown(f"### {course[1]}")
                st.write(course[3])
                lessons = get_lessons(course[0])
                if lessons:
                    for l in lessons:
                        st.markdown(f"**{l[2]}** ({l[4]})")
                        st.write(l[3])
                        if l[4] == "Video" and l[5]:
                            st.video(io.BytesIO(l[5]))
                        elif l[4] == "PDF" and l[5]:
                            st.download_button(label=f"Download PDF: {l[2]}", data=l[5], file_name=f"{l[2]}.pdf")
                        elif l[4] == "PPT" and l[5]:
                            st.download_button(label=f"Download PPT: {l[2]}", data=l[5], file_name=f"{l[2]}.pptx")
                        elif l[4] == "Link" and l[6]:
                            st.markdown(f"[Open Link: {l[2]}]({l[6]})", unsafe_allow_html=True)
                st.write("---")
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

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

    # Home-style toggle buttons
    admin_pages = ["Dashboard", "Students", "Courses", "Logout"]
    if "admin_page" not in st.session_state:
        st.session_state["admin_page"] = "Dashboard"
    cols = st.columns(len(admin_pages))
    for idx, p in enumerate(admin_pages):
        if cols[idx].button(p):
            st.session_state["admin_page"] = p

    page = st.session_state["admin_page"]

    if page == "Dashboard":
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_lessons = c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        st.subheader("Summary")
        st.write(f"**Total Students:** {total_students}")
        st.write(f"**Total Courses:** {total_courses}")
        st.write(f"**Total Lessons:** {total_lessons}")

    elif page == "Students":
        st.subheader("All Students Data")
        students = c.execute("SELECT student_id, full_name, email, gender, profession, institution FROM students").fetchall()
        for s in students:
            st.write(f"ID: {s[0]}, Name: {s[1]}, Email: {s[2]}, Gender: {s[3]}, Profession: {s[4]}, Institution: {s[5]}")

    elif page == "Courses":
        st.subheader("All Courses and Add Course/Lesson")
        courses = get_courses()
        st.write("### Add Course")
        with st.form("add_course_form"):
            title = st.text_input("Course Title")
            subtitle = st.text_input("Course Subtitle")
            description = st.text_area("Course Description")
            price_type = st.selectbox("Course Type", ["Free","Paid"])
            price = 0
            if price_type=="Paid":
                price = st.number_input("Price (INR)", min_value=1)
            submit_course = st.form_submit_button("Add Course")
            if submit_course:
                add_course(title, subtitle, description, price)
                st.success("Course added successfully!")

        if courses:
            st.write("---")
            st.write("### Add Lessons to a Course")
            course_dict = {c[1]: c[0] for c in courses}
            selected_course_name = st.selectbox("Select Course", list(course_dict.keys()))
            selected_course_id = course_dict[selected_course_name]
            with st.form("add_lesson_form"):
                lesson_title = st.text_input("Lesson Title")
                lesson_description = st.text_area("Lesson Description")
                lesson_type = st.selectbox("Lesson Type", ["Video","PDF","PPT","Link"])
                uploaded_file = None
                lesson_link = ""
                if lesson_type in ["Video","PDF","PPT"]:
                    uploaded_file = st.file_uploader(f"Upload {lesson_type}")
                else:
                    lesson_link = st.text_input("Paste Link Here")
                submit_lesson = st.form_submit_button("Add Lesson")
                if submit_lesson:
                    file_bytes = convert_file_to_bytes(uploaded_file)
                    add_lesson(selected_course_id, lesson_title, lesson_description, lesson_type, file_bytes, lesson_link)
                    st.success(f"Lesson '{lesson_title}' added to course '{selected_course_name}' successfully!")

    elif page == "Logout":
        st.session_state.clear()
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
