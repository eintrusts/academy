import streamlit as st
import sqlite3
import datetime

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Students table
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)
""")

# Courses table
c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    amount REAL
)
""")

# Lessons table
c.execute("""
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
""")

# Enrollments table
c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    enrolled_on TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
""")

conn.commit()

# ---------------------------
# Helpers
# ---------------------------
def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_student(email, password):
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def add_course(name, description, amount):
    c.execute("INSERT INTO courses (name, description, amount) VALUES (?,?,?)", (name, description, amount))
    conn.commit()

def get_courses():
    c.execute("SELECT * FROM courses")
    return c.fetchall()

def add_lesson(course_id, title, content):
    c.execute("INSERT INTO lessons (course_id, title, content) VALUES (?,?,?)", (course_id, title, content))
    conn.commit()

def get_lessons(course_id):
    c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    return c.fetchall()

def enroll_student(student_id, course_id):
    # Prevent duplicate enrollment
    c.execute("SELECT * FROM enrollments WHERE student_id=? AND course_id=?", (student_id, course_id))
    if not c.fetchone():
        c.execute("INSERT INTO enrollments (student_id, course_id, enrolled_on) VALUES (?,?,?)",
                  (student_id, course_id, str(datetime.datetime.now())))
        conn.commit()

def get_enrolled_courses(student_id):
    c.execute("""
        SELECT c.id, c.name, c.description, c.amount
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id=?
    """, (student_id,))
    return c.fetchall()

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", page_icon="🎓", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# UI Pages
# ---------------------------
def page_home():
    st.title("🎓 Welcome to EinTrust Academy")
    courses = get_courses()
    if courses:
        cols = st.columns(3)
        for idx, course in enumerate(courses):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"### {course[1]}")
                    st.markdown(f"<p style='font-size:14px;'>{course[2]}</p>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button("Enroll", key=f"enroll_home_{course[0]}"):
                            if st.session_state.user:
                                enroll_student(st.session_state.user[0], course[0])
                                st.success("Enrolled successfully!")
                            else:
                                st.session_state.page = "signup"
                                st.experimental_rerun()
                    with col2:
                        st.markdown(f"💰 ₹{course[3]:.2f}")
    else:
        st.info("No courses available yet.")

def page_signup():
    st.subheader("Sign Up")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if add_student(full_name, email, password, gender, profession, institution):
                st.success("Signup successful! Please login.")
                st.session_state.page = "login"
                st.experimental_rerun()
            else:
                st.error("Email already exists!")

def page_login():
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            student = authenticate_student(email, password)
            if student:
                st.session_state.user = student
                st.session_state.page = "student_dashboard"
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

def page_student_dashboard():
    st.title(f"👋 Welcome {st.session_state.user[1]}")
    tabs = st.tabs(["All Courses", "My Courses", "Lessons"])
    
    # All Courses
    with tabs[0]:
        courses = get_courses()
        cols = st.columns(3)
        for idx, course in enumerate(courses):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"### {course[1]}")
                    st.markdown(f"<p style='font-size:14px;'>{course[2]}</p>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button("Enroll", key=f"enroll_student_{course[0]}"):
                            enroll_student(st.session_state.user[0], course[0])
                            st.success("Enrolled successfully!")
                    with col2:
                        st.markdown(f"💰 ₹{course[3]:.2f}")

    # My Courses
    with tabs[1]:
        enrolled = get_enrolled_courses(st.session_state.user[0])
        if enrolled:
            for course in enrolled:
                st.markdown(f"### {course[1]}")
                st.write(course[2])
                st.write(f"💰 ₹{course[3]:.2f}")
        else:
            st.info("You are not enrolled in any courses yet.")

    # Lessons
    with tabs[2]:
        enrolled = get_enrolled_courses(st.session_state.user[0])
        if enrolled:
            course_ids = {c[0]: c[1] for c in enrolled}
            selected_course = st.selectbox("Select a Course", list(course_ids.values()))
            if selected_course:
                course_id = [cid for cid, name in course_ids.items() if name == selected_course][0]
                lessons = get_lessons(course_id)
                if lessons:
                    for lesson in lessons:
                        st.markdown(f"#### {lesson[2]}")
                        st.write(lesson[3])
                else:
                    st.info("No lessons added yet.")
        else:
            st.info("Enroll in a course to see lessons.")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "home"
        st.experimental_rerun()

def page_admin_dashboard():
    st.title("🔑 Admin Dashboard")

    tabs = st.tabs(["Add Course", "Add Lesson", "Manage Courses"])

    with tabs[0]:
        with st.form("course_form"):
            name = st.text_input("Course Name")
            description = st.text_area("Description")
            amount = st.number_input("Amount (₹)", min_value=0.0)
            submitted = st.form_submit_button("Add Course")
            if submitted:
                add_course(name, description, amount)
                st.success("Course added!")

    with tabs[1]:
        courses = get_courses()
        if courses:
            with st.form("lesson_form"):
                course_options = {c[1]: c[0] for c in courses}
                course_name = st.selectbox("Select Course", list(course_options.keys()))
                title = st.text_input("Lesson Title")
                content = st.text_area("Lesson Content")
                submitted = st.form_submit_button("Add Lesson")
                if submitted:
                    add_lesson(course_options[course_name], title, content)
                    st.success("Lesson added!")
        else:
            st.warning("Add a course first.")

    with tabs[2]:
        courses = get_courses()
        if courses:
            for course in courses:
                st.write(f"**{course[1]}** - ₹{course[3]:.2f}")
                st.write(course[2])
        else:
            st.info("No courses available.")

    if st.button("Logout"):
        st.session_state.page = "home"
        st.experimental_rerun()

# ---------------------------
# Navigation
# ---------------------------
menu = ["Home", "Signup", "Login", "Admin"]
choice = st.sidebar.radio("Navigate", menu)

if choice == "Home":
    page_home()
elif choice == "Signup":
    page_signup()
elif choice == "Login":
    page_login()
elif choice == "Admin":
    page_admin_dashboard()

# Redirect if session page is set
if st.session_state.page == "signup":
    page_signup()
elif st.session_state.page == "login":
    page_login()
elif st.session_state.page == "student_dashboard" and st.session_state.user:
    page_student_dashboard()
elif st.session_state.page == "admin_dashboard":
    page_admin_dashboard()
