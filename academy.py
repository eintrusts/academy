import streamlit as st
import sqlite3

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Students table
c.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    gender TEXT,
    profession TEXT,
    institution TEXT
)''')

# Courses table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    amount INTEGER
)''')

# Lessons table
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content_type TEXT,
    content TEXT,
    description TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(id)
)''')

# Enrollment table
c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)''')
conn.commit()

# ---------------------------
# Utility Functions
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

def get_courses():
    c.execute("SELECT * FROM courses")
    return c.fetchall()

def add_course(name, description, amount):
    c.execute("INSERT INTO courses (name, description, amount) VALUES (?,?,?)", (name, description, amount))
    conn.commit()

def update_course(course_id, name, description, amount):
    c.execute("UPDATE courses SET name=?, description=?, amount=? WHERE id=?", (name, description, amount, course_id))
    conn.commit()

def delete_course(course_id):
    c.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()

def add_lesson(course_id, title, content_type, content, description):
    c.execute("INSERT INTO lessons (course_id, title, content_type, content, description) VALUES (?,?,?,?,?)",
              (course_id, title, content_type, content, description))
    conn.commit()

def get_lessons(course_id):
    c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    return c.fetchall()

def enroll_student(student_id, course_id):
    c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?,?)", (student_id, course_id))
    conn.commit()

def get_student_courses(student_id):
    c.execute("SELECT courses.id, courses.name, courses.description, courses.amount FROM courses "
              "JOIN enrollments ON courses.id=enrollments.course_id WHERE enrollments.student_id=?", (student_id,))
    return c.fetchall()

# ---------------------------
# CSS Styling
# ---------------------------
st.markdown("""
<style>
body {
    background-color: #111111;
    color: white;
}
.stButton>button {
    background-color: #444444;
    color: white;
    border-radius: 8px;
    padding: 6px 16px;
    margin: 5px;
    font-size: 14px;
}
.stButton>button:hover {
    background-color: #666666;
    color: white;
}
.course-card {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 0 8px rgba(255,255,255,0.1);
    margin: 10px;
}
.course-title {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}
.course-desc {
    font-size: 14px;
    color: #cccccc;
    margin-bottom: 30px;
}
.course-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Components
# ---------------------------
def display_courses_grid(courses, student_id=None):
    cols = st.columns(3)
    for idx, course in enumerate(courses):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="course-card">
                <div class="course-title">{course[1]}</div>
                <div class="course-desc">{course[2]}</div>
                <div class="course-footer">
                    <form action="" method="post">
                        <button type="submit" name="enroll_{course[0]}">Enroll</button>
                    </form>
                    <div>₹ {course[3]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.get("page") == "student_dashboard" and student_id:
                if st.button(f"Enroll {course[0]}", key=f"enroll_{course[0]}_student"):
                    enroll_student(student_id, course[0])
                    st.success(f"Enrolled in {course[1]} successfully!")
            elif st.session_state.get("page") == "home":
                if st.button(f"Enroll {course[0]}", key=f"enroll_{course[0]}_home"):
                    st.session_state["page"] = "signup"
                    st.experimental_rerun()

# ---------------------------
# Pages
# ---------------------------
def page_home():
    st.header("Welcome to EinTrust Academy")
    courses = get_courses()
    if courses:
        display_courses_grid(courses)
    else:
        st.info("No courses available yet.")

def page_signup():
    st.header("Student Signup")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    gender = st.selectbox("Gender", ["Male","Female","Other"])
    profession = st.text_input("Profession")
    institution = st.text_input("Institution")
    if st.button("Signup"):
        success = add_student(full_name, email, password, gender, profession, institution)
        if success:
            st.success("Profile created successfully! Please login.")
            st.session_state["page"] = "login"
            st.experimental_rerun()
        else:
            st.error("Email already registered. Please login.")

def page_login():
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
    st.header("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.subheader(f"Welcome, {student[1]}")
        st.write("---")
        st.subheader("Your Enrolled Courses")
        courses = get_student_courses(student[0])
        display_courses_grid(courses, student_id=student[0])
        st.write("---")
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

def page_admin_login():
    st.header("Admin Login")
    email = st.text_input("Admin Email")
    password = st.text_input("Admin Password", type="password")
    if st.button("Login as Admin"):
        if email == "admin@example.com" and password == "admin123":
            st.session_state["admin"] = True
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid admin credentials.")

def page_admin_dashboard():
    st.sidebar.title("Admin Panel")
    choice = st.sidebar.radio("Navigation", ["Dashboard", "Courses", "Students", "Lessons", "Logout"])

    if choice == "Dashboard":
        st.subheader("Admin Dashboard")
    elif choice == "Courses":
        st.subheader("Manage Courses")
        courses = get_courses()
        for course in courses:
            st.write(f"**{course[1]}** - ₹{course[3]}")
            if st.button(f"Edit {course[0]}", key=f"edit_{course[0]}"):
                new_name = st.text_input("New Name", value=course[1], key=f"name_{course[0]}")
                new_desc = st.text_area("New Description", value=course[2], key=f"desc_{course[0]}")
                new_amt = st.number_input("New Amount", value=course[3], key=f"amt_{course[0]}")
                if st.button("Update", key=f"update_{course[0]}"):
                    update_course(course[0], new_name, new_desc, new_amt)
                    st.success("Course updated!")
            if st.button(f"Delete {course[0]}", key=f"del_{course[0]}"):
                delete_course(course[0])
                st.success("Course deleted!")

        st.write("---")
        st.subheader("Add New Course")
        name = st.text_input("Course Name", key="new_name")
        desc = st.text_area("Description", key="new_desc")
        amt = st.number_input("Amount (INR)", min_value=0, key="new_amt")
        if st.button("Add Course"):
            add_course(name, desc, amt)
            st.success("Course added!")

    elif choice == "Students":
        st.subheader("All Students")
        c.execute("SELECT full_name, email, profession FROM students")
        rows = c.fetchall()
        for row in rows:
            st.write(row)

    elif choice == "Lessons":
        st.subheader("Manage Lessons")
        courses = get_courses()
        course_options = {c[1]: c[0] for c in courses}
        selected_course = st.selectbox("Select Course", list(course_options.keys()))
        course_id = course_options[selected_course]
        lessons = get_lessons(course_id)
        for lesson in lessons:
            st.write(f"**{lesson[1]}** - {lesson[2]}")
        st.write("---")
        st.subheader("Add Lesson")
        title = st.text_input("Lesson Title")
        ctype = st.selectbox("Content Type", ["Video","PDF","PPT","Link"])
        content = st.text_input("Content (URL or Path)")
        ldesc = st.text_area("Lesson Description")
        if st.button("Add Lesson"):
            add_lesson(course_id, title, ctype, content, ldesc)
            st.success("Lesson added!")

    elif choice == "Logout":
        st.session_state.clear()
        st.session_state["page"] = "home"
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
    with tabs[3]: page_admin_login()
elif st.session_state["page"] == "signup":
    page_signup()
elif st.session_state["page"] == "login":
    page_login()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
