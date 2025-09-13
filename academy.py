import streamlit as st
import sqlite3

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute("""CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    lesson_type TEXT,
    file BLOB,
    link TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER
)""")

conn.commit()

# ---------------------------
# Helper Functions
# ---------------------------
def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name, email, password, gender, profession, institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except:
        return False

def authenticate_student(email, password):
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def update_student(student_id, full_name, email, password, gender, profession, institution):
    try:
        c.execute("""UPDATE students 
                     SET full_name=?, email=?, password=?, gender=?, profession=?, institution=? 
                     WHERE student_id=?""",
                  (full_name, email, password, gender, profession, institution, student_id))
        conn.commit()
        return True
    except:
        return False

def get_courses():
    return c.execute("SELECT * FROM courses").fetchall()

def add_course(title, subtitle, desc, price):
    c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?,?,?,?)",
              (title, subtitle, desc, price))
    conn.commit()

def update_course(course_id, title, subtitle, desc, price):
    c.execute("UPDATE courses SET title=?, subtitle=?, description=?, price=? WHERE course_id=?",
              (title, subtitle, desc, price, course_id))
    conn.commit()

def add_lesson(course_id, title, desc, lesson_type, file, link):
    c.execute("INSERT INTO lessons (course_id, title, description, lesson_type, file, link) VALUES (?,?,?,?,?,?)",
              (course_id, title, desc, lesson_type, file, link))
    conn.commit()

def get_lessons(course_id):
    return c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,)).fetchall()

def enroll_student(student_id, course_id):
    c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?,?)", (student_id, course_id))
    conn.commit()

def get_student_courses(student_id):
    return c.execute("""SELECT c.* FROM courses c 
                        JOIN enrollments e ON c.course_id=e.course_id 
                        WHERE e.student_id=?""", (student_id,)).fetchall()

def convert_file_to_bytes(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.read()
    return None

# ---------------------------
# UI Components
# ---------------------------
def display_logo_and_title_center():
    st.markdown("<h1 style='text-align: center;'>🌍</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>EinTrust Academy</h2>", unsafe_allow_html=True)

def display_courses(courses, enroll=False, editable=False, show_lessons=False, student_id=None):
    for course in courses:
        with st.expander(f"{course[1]} - {course[2]}"):
            st.write(course[3])
            st.write(f"💰 Price: ₹{course[4]:,.2f}")

            if enroll and student_id:
                enrolled_courses = [c[0] for c in get_student_courses(student_id)]
                if course[0] in enrolled_courses:
                    st.success("✅ Already Enrolled")
                else:
                    if st.button(f"Enroll in {course[1]}", key=f"enroll_{course[0]}"):
                        enroll_student(student_id, course[0])
                        st.success("Enrolled successfully!")
                        st.experimental_rerun()

            if show_lessons:
                lessons = get_lessons(course[0])
                for lesson in lessons:
                    st.write(f"📘 {lesson[2]} - {lesson[3]} ({lesson[4]})")
                    if lesson[5]:
                        st.download_button("Download File", lesson[5], file_name=f"{lesson[2]}")
                    if lesson[6]:
                        st.markdown(f"[Open Resource]({lesson[6]})")

            if editable:
                if st.button("✏️ Edit Course", key=f"edit_{course[0]}"):
                    st.session_state["edit_course"] = course
                    st.session_state["page"] = "edit_course"
                    st.experimental_rerun()

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.subheader("Welcome to EinTrust Academy")
    st.write("Your sustainability learning hub.")

    courses = get_courses()
    if courses:
        st.subheader("Available Courses")
        display_courses(courses)
    else:
        st.info("No courses available yet.")

def page_signup():
    st.header("Signup")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution")
        if st.form_submit_button("Signup"):
            if add_student(full_name, email, password, gender, profession, institution):
                st.success("Signup successful! Please login.")
            else:
                st.error("Email already exists.")

def page_login():
    st.header("Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def page_student_dashboard():
    student = st.session_state.get("student")
    if not student:
        st.warning("Please login first.")
        return

    tabs = st.tabs(["All Courses", "My Courses", "Edit Profile", "Logout"])

    with tabs[0]:
        st.subheader("All Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])

    with tabs[1]:
        st.subheader("My Courses")
        enrolled_courses = get_student_courses(student[0])
        display_courses(enrolled_courses, show_lessons=True)

    with tabs[2]:
        st.subheader("Edit Profile")
        with st.form("edit_profile_form"):
            full_name = st.text_input("Full Name", value=student[1])
            email = st.text_input("Email ID", value=student[2])
            password = st.text_input("Password", type="password", value=student[3])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(student[4]))
            profession = st.text_input("Profession", value=student[5])
            institution = st.text_input("Institution", value=student[6])
            if st.form_submit_button("Update Profile"):
                success = update_student(student[0], full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile updated successfully!")
                    st.session_state["student"] = authenticate_student(email, password)
                    st.experimental_rerun()
                else:
                    st.error("Email already exists. Please try a different one.")

    with tabs[3]:
        st.success("You have been logged out.")
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

def page_admin_dashboard():
    tabs = st.tabs(["Dashboard", "Students", "Courses & Lessons", "Logout"])

    with tabs[0]:
        st.subheader("Overview")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_lessons = c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        st.write(f"Total Students: {total_students}")
        st.write(f"Total Courses: {total_courses}")
        st.write(f"Total Lessons: {total_lessons}")

    with tabs[1]:
        st.subheader("Manage Students")
        students = c.execute("SELECT * FROM students").fetchall()
        for s in students:
            st.write(f"{s[0]}. {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}")
            if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                conn.commit()
                st.success(f"Deleted {s[1]}")
                st.experimental_rerun()

    with tabs[2]:
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

    with tabs[3]:
        st.success("You have been logged out.")
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.experimental_rerun()

def page_edit_course():
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
display_logo_and_title_center()

if "student" not in st.session_state and st.session_state.get("page") not in ["student_dashboard", "admin_dashboard", "edit_course"]:
    tabs = st.tabs(["Home", "Signup", "Login", "Admin"])
    with tabs[0]: page_home()
    with tabs[1]: page_signup()
    with tabs[2]: page_login()
    with tabs[3]: page_admin()
else:
    if st.session_state.get("page") == "student_dashboard": page_student_dashboard()
    elif st.session_state.get("page") == "admin_dashboard": page_admin_dashboard()
    elif st.session_state.get("page") == "edit_course": page_edit_course()
