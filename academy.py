import streamlit as st
import sqlite3

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
    title TEXT,
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
    type TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
""")

# Student-Course enrollments
c.execute("""
CREATE TABLE IF NOT EXISTS student_courses (
    student_id INTEGER,
    course_id INTEGER,
    PRIMARY KEY (student_id, course_id)
)
""")

conn.commit()

# ---------------------------
# Helper Functions
# ---------------------------
def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except:
        return False

def login_student(email, password):
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def login_admin(email, password):
    return email == "admin@academy.com" and password == "admin123"

def add_course(title, description, amount):
    c.execute("INSERT INTO courses (title, description, amount) VALUES (?,?,?)",
              (title, description, amount))
    conn.commit()

def update_course(course_id, title, description, amount):
    c.execute("UPDATE courses SET title=?, description=?, amount=? WHERE id=?",
              (title, description, amount, course_id))
    conn.commit()

def delete_course(course_id):
    c.execute("DELETE FROM courses WHERE id=?", (course_id,))
    c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    conn.commit()

def get_courses():
    c.execute("SELECT * FROM courses")
    return c.fetchall()

def add_lesson(course_id, title, content, lesson_type):
    c.execute("INSERT INTO lessons (course_id,title,content,type) VALUES (?,?,?,?)",
              (course_id, title, content, lesson_type))
    conn.commit()

def update_lesson(lesson_id, title, content, lesson_type):
    c.execute("UPDATE lessons SET title=?, content=?, type=? WHERE id=?",
              (title, content, lesson_type, lesson_id))
    conn.commit()

def delete_lesson(lesson_id):
    c.execute("DELETE FROM lessons WHERE id=?", (lesson_id,))
    conn.commit()

def get_lessons(course_id):
    c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    return c.fetchall()

def enroll_course(student_id, course_id):
    try:
        c.execute("INSERT INTO student_courses (student_id, course_id) VALUES (?, ?)",
                  (student_id, course_id))
        conn.commit()
    except:
        pass

# ---------------------------
# Page Functions
# ---------------------------
def page_signup():
    st.subheader("Student Signup")
    with st.form("signup_form", clear_on_submit=True):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution/Organization")
        submitted = st.form_submit_button("Signup")
        if submitted:
            success = add_student(full_name, email, password, gender, profession, institution)
            if success:
                st.success("Account created successfully. Please login.")
            else:
                st.error("Email already exists or error occurred.")

def page_student_login():
    st.subheader("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = login_student(email, password)
        if student:
            st.session_state["student_id"] = student[0]
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def page_admin_login():
    st.subheader("Admin Login")
    email = st.text_input("Admin Email")
    password = st.text_input("Password", type="password")
    if st.button("Login as Admin"):
        if login_admin(email, password):
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid admin credentials")

def page_student_dashboard():
    st.title("Student Dashboard")
    courses = get_courses()

    if not courses:
        st.info("No courses available yet.")
        return

    cols = st.columns(3)
    for i, course in enumerate(courses):
        with cols[i % 3]:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background-color:#1E1E1E; padding:20px; border-radius:15px; margin-bottom:20px;'>
                        <h3 style='color:#4CAF50;'>{course[1]}</h3>
                        <p style='color:#aaa;'>{course[2]}</p>
                        <p><b>Amount:</b> {"Free" if course[3] == 0 else f"₹{course[3]:,.2f}"}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("Enroll", key=f"enroll_{course[0]}"):
                    enroll_course(st.session_state["student_id"], course[0])
                    st.success(f"Enrolled in {course[1]} successfully!")

                lessons = get_lessons(course[0])
                if lessons:
                    st.write("Lessons:")
                    for lesson in lessons:
                        st.write(f"- {lesson[2]} ({lesson[4]})")

def page_admin_dashboard():
    st.title("Admin Dashboard")
    menu = st.radio("Navigation", ["Dashboard", "All Students", "Courses", "Logout"], horizontal=True)

    if menu == "Dashboard":
        st.subheader("Overview")
        c.execute("SELECT COUNT(*) FROM students")
        total_students = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM courses")
        total_courses = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM lessons")
        total_lessons = c.fetchone()[0]
        st.write(f"Total Students: {total_students}")
        st.write(f"Total Courses: {total_courses}")
        st.write(f"Total Lessons: {total_lessons}")

    elif menu == "All Students":
        st.subheader("All Students")
        c.execute("SELECT full_name, email, gender, profession, institution FROM students")
        rows = c.fetchall()
        if rows:
            st.table(rows)
        else:
            st.info("No students registered.")

    elif menu == "Courses":
        st.subheader("Courses")
        courses = get_courses()
        for course in courses:
            with st.expander(course[1]):
                st.write("Description:", course[2])
                st.write("Amount:", "Free" if course[3] == 0 else f"₹{course[3]:,.2f}")

                # Edit Course
                with st.form(f"edit_course_{course[0]}"):
                    new_title = st.text_input("Edit Title", value=course[1])
                    new_description = st.text_area("Edit Description", value=course[2])
                    new_amount = st.number_input("Edit Amount (₹)", min_value=0.0, step=100.0, value=course[3])
                    save_changes = st.form_submit_button("Save Course Changes")
                    if save_changes:
                        update_course(course[0], new_title, new_description, new_amount)
                        st.success("Course updated successfully")
                        st.experimental_rerun()

                if st.button("Delete Course", key=f"delete_{course[0]}"):
                    delete_course(course[0])
                    st.warning("Course deleted")
                    st.experimental_rerun()

                # Lessons under course
                st.write("### Lessons")
                lessons = get_lessons(course[0])
                for lesson in lessons:
                    with st.expander(f"Lesson: {lesson[2]}"):
                        st.write("Content:", lesson[3])
                        st.write("Type:", lesson[4])
                        with st.form(f"edit_lesson_{lesson[0]}"):
                            l_title = st.text_input("Edit Lesson Title", value=lesson[2])
                            l_content = st.text_area("Edit Content", value=lesson[3])
                            l_type = st.selectbox("Type", ["Video", "PDF", "PPT", "Link"], index=["Video", "PDF", "PPT", "Link"].index(lesson[4]))
                            save_lesson = st.form_submit_button("Save Lesson Changes")
                            if save_lesson:
                                update_lesson(lesson[0], l_title, l_content, l_type)
                                st.success("Lesson updated successfully")
                                st.experimental_rerun()

                        if st.button("Delete Lesson", key=f"delete_lesson_{lesson[0]}"):
                            delete_lesson(lesson[0])
                            st.warning("Lesson deleted")
                            st.experimental_rerun()

                # Add New Lesson
                st.write("### Add New Lesson")
                with st.form(f"add_lesson_{course[0]}", clear_on_submit=True):
                    l_title = st.text_input("Lesson Title")
                    l_content = st.text_area("Lesson Content / URL")
                    l_type = st.selectbox("Lesson Type", ["Video", "PDF", "PPT", "Link"])
                    add_l = st.form_submit_button("Add Lesson")
                    if add_l:
                        add_lesson(course[0], l_title, l_content, l_type)
                        st.success("Lesson added successfully")
                        st.experimental_rerun()

        # Add New Course
        st.subheader("Add New Course")
        with st.form("add_course_form", clear_on_submit=True):
            title = st.text_input("Course Title")
            description = st.text_area("Course Description")
            amount = st.number_input("Course Amount (₹)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("Add Course")
            if submitted:
                add_course(title, description, amount)
                st.success("Course added successfully")
                st.experimental_rerun()

    elif menu == "Logout":
        st.session_state.clear()
        st.success("Logged out successfully")
        st.session_state["page"] = "home"
        st.experimental_rerun()

# ---------------------------
# App Navigation
# ---------------------------
st.set_page_config(page_title="Academy LMS", layout="wide")

if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    st.title("Academy LMS")
    tabs = st.tabs(["Home", "Signup", "Login Student", "Login Admin"])
    with tabs[0]:
        st.write("Welcome to the Learning Management System")
    with tabs[1]:
        page_signup()
    with tabs[2]:
        page_student_login()
    with tabs[3]:
        page_admin_login()

elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()

elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
