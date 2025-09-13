import streamlit as st
import sqlite3

# ---------------------------
# DB Setup
# ---------------------------
def init_db():
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT,
                    email TEXT UNIQUE,
                    password TEXT,
                    gender TEXT,
                    profession TEXT,
                    institution TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    amount INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title TEXT,
                    content_type TEXT,
                    content TEXT,
                    description TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Helpers
# ---------------------------
def add_student(full_name, email, password, gender, profession, institution):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution) VALUES (?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_student(email, password):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
    data = c.fetchone()
    conn.close()
    return data

def validate_admin(username, password):
    return username == "admin" and password == "admin123"

def add_course(name, description, amount):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("INSERT INTO courses (name, description, amount) VALUES (?,?,?)", (name, description, amount))
    conn.commit()
    conn.close()

def get_courses():
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("SELECT * FROM courses")
    data = c.fetchall()
    conn.close()
    return data

def add_lesson(course_id, title, content_type, content, description):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("INSERT INTO lessons (course_id,title,content_type,content,description) VALUES (?,?,?,?,?)",
              (course_id, title, content_type, content, description))
    conn.commit()
    conn.close()

def get_lessons(course_id):
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()
    c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    data = c.fetchall()
    conn.close()
    return data

# ---------------------------
# UI Styling
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

BUTTON_STYLE = """
<style>
.stButton>button {
    background-color: #1e40af;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
    width: 100%;
}
.stButton>button:hover {
    background-color: #3749b5;
    color: white;
}
.course-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 20px;
    background-color: #f9f9f9;
}
.course-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
}
.course-desc {
    font-size: 14px;
    margin-bottom: 16px;
}
.course-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
"""
st.markdown(BUTTON_STYLE, unsafe_allow_html=True)

# ---------------------------
# Pages
# ---------------------------
def home_page():
    st.title("Welcome to EinTrust Academy")

    courses = get_courses()
    if not courses:
        st.info("No courses available yet.")
    else:
        cols = st.columns(2)
        for idx, course in enumerate(courses):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="course-card">
                    <div class="course-title">{course[1]}</div>
                    <div class="course-desc">{course[2]}</div>
                    <div class="course-footer">
                        <form action="#" method="get">
                            <button type="submit" formaction="/?page=signup">Enroll</button>
                        </form>
                        <div><b>₹{course[3]}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def signup_page():
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
                st.success("Signup successful. You can now log in.")
            else:
                st.error("Email already exists.")

def login_page():
    st.subheader("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = validate_student(email, password)
        if student:
            st.session_state["page"] = "student_dashboard"
            st.session_state["student"] = student
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def admin_login_page():
    st.subheader("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login as Admin"):
        if validate_admin(username, password):
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid admin credentials")

def student_dashboard():
    st.title("Student Dashboard")
    courses = get_courses()
    st.subheader("Available Courses")
    cols = st.columns(2)
    for idx, course in enumerate(courses):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="course-card">
                <div class="course-title">{course[1]}</div>
                <div class="course-desc">{course[2]}</div>
                <div class="course-footer">
                    <form action="#" method="get">
                        <button type="submit" formaction="/?page=signup">Enroll</button>
                    </form>
                    <div><b>₹{course[3]}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def admin_dashboard():
    st.title("Admin Dashboard")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Course", "Add Lesson", "Logout"])

    if menu == "Dashboard":
        st.subheader("All Courses Data")
        courses = get_courses()
        for c in courses:
            st.write(f"📘 {c[1]} - ₹{c[3]}")

    elif menu == "Add Course":
        st.subheader("Add New Course")
        with st.form("course_form"):
            name = st.text_input("Course Name")
            desc = st.text_area("Description")
            amt = st.number_input("Course Amount (₹)", min_value=0)
            submitted = st.form_submit_button("Add Course")
            if submitted:
                add_course(name, desc, amt)
                st.success("Course added successfully")

    elif menu == "Add Lesson":
        st.subheader("Add Lesson to Course")
        courses = get_courses()
        if not courses:
            st.warning("No courses available.")
        else:
            course = st.selectbox("Select Course", courses, format_func=lambda x: x[1])
            with st.form("lesson_form"):
                title = st.text_input("Lesson Title")
                content_type = st.selectbox("Content Type", ["Video", "PDF", "PPT", "Link"])
                content = st.text_input("Content (URL/Path)")
                desc = st.text_area("Lesson Description")
                submitted = st.form_submit_button("Add Lesson")
                if submitted:
                    add_lesson(course[0], title, content_type, content, desc)
                    st.success("Lesson added successfully")

    elif menu == "Logout":
        st.session_state.clear()
        st.experimental_rerun()

# ---------------------------
# Routing
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

page = st.session_state["page"]

if page == "home":
    tabs = st.tabs(["Home", "Signup", "Student Login", "Admin Login"])
    with tabs[0]: home_page()
    with tabs[1]: signup_page()
    with tabs[2]: login_page()
    with tabs[3]: admin_login_page()
elif page == "student_dashboard":
    student_dashboard()
elif page == "admin_dashboard":
    admin_dashboard()
