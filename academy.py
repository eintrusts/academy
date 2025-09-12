import streamlit as st
import sqlite3
import hashlib

# ------------------- DATABASE CONNECTION -------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# ------------------- CREATE TABLES -------------------
def create_tables():
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    mobile TEXT,
                    profession TEXT,
                    institution TEXT,
                    sex TEXT,
                    profile_pic TEXT
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS admin (
                    admin_id INTEGER PRIMARY KEY,
                    password TEXT NOT NULL
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    subtitle TEXT,
                    description TEXT,
                    price REAL,
                    category TEXT,
                    banner_path TEXT
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title TEXT,
                    content_type TEXT,
                    content_path TEXT,
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS progress (
                    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    lesson_id INTEGER,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS certificates (
                    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    cert_file TEXT,
                    date_generated TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    
    # Insert default admin if not exists
    c.execute("INSERT OR IGNORE INTO admin (admin_id, password) VALUES (1, ?)", ('admin123',))
    conn.commit()

create_tables()

# ------------------- STREAMLIT CONFIG -------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color:#121212; color:white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
div.stButton > button:first-child {background-color:#1E88E5; color:white; border-radius:8px; height:40px;}
input {color:black;}
</style>
""", unsafe_allow_html=True)

# ------------------- UTILITIES -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- NAVIGATION -------------------
def top_nav():
    col1, col2 = st.columns([1,1])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true", width=180)
    with col2:
        if st.button("Login"):
            st.session_state['page'] = "login"

# ------------------- HOME PAGE -------------------
def home_page():
    top_nav()
    st.markdown("## Available Courses")
    try:
        courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
        if not courses:
            st.info("No courses available yet. Admin can add courses.")
        for course in courses:
            st.markdown(f"""
            <div style='border:1px solid #555; padding:15px; margin-bottom:15px; border-radius:10px; background-color:#1C1C1C'>
            <h3>{course[1]}</h3>
            <p>{course[2]}</p>
            <p>{course[3]}</p>
            <p>Price: ₹{int(course[4]):,}</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error("Error loading courses. DB might be empty or corrupted.")
        st.error(str(e))

# ------------------- STUDENT SIGNUP -------------------
def student_signup():
    st.subheader("Student Sign Up")
    full_name = st.text_input("Full Name *")
    email = st.text_input("Email ID *")
    password = st.text_input("Set Password *", type='password')
    st.markdown("**Password rules:** Min 8 characters, 1 uppercase, 1 number, 1 special char (@, #, *)")
    mobile = st.text_input("Mobile")
    profession = st.selectbox("Profession", ["Student", "Working Professional"])
    institution = st.text_input("Institution")
    sex = st.selectbox("Sex", ["Male", "Female", "Prefer not to say"])
    profile_pic = st.file_uploader("Profile Picture (optional)", type=['png','jpg','jpeg'])
    
    if st.button("Create Profile"):
        if not full_name or not email or not password:
            st.error("Full Name, Email, and Password are mandatory")
            return
        hashed_pwd = hash_password(password)
        try:
            c.execute("INSERT INTO students (full_name,email,password,mobile,profession,institution,sex,profile_pic) VALUES (?,?,?,?,?,?,?,?)",
                      (full_name,email,hashed_pwd,mobile,profession,institution,sex,None))
            conn.commit()
            st.success("Profile created! Please login now.")
            st.session_state['page'] = "login"
        except sqlite3.IntegrityError:
            st.error("Email already exists.")

# ------------------- STUDENT LOGIN -------------------
def student_login():
    st.subheader("Student Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        hashed_pwd = hash_password(password)
        user = c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, hashed_pwd)).fetchone()
        if user:
            st.session_state['student_id'] = user[0]
            st.session_state['page'] = "student_dashboard"
        else:
            st.error("Incorrect email/password")

# ------------------- ADMIN LOGIN -------------------
def admin_login():
    st.subheader("Admin Login")
    password = st.text_input("Enter Admin Password", type='password')
    if st.button("Enter"):
        admin = c.execute("SELECT * FROM admin WHERE password=?", (password,)).fetchone()
        if admin:
            st.session_state['page'] = "admin_dashboard"
        else:
            st.error("Incorrect password")

# ------------------- STUDENT DASHBOARD -------------------
def student_dashboard():
    st.subheader("Student Dashboard")
    student_id = st.session_state.get('student_id')
    if not student_id:
        st.error("Student not logged in!")
        return
    st.markdown("### Your Courses")
    try:
        enrolled_courses = c.execute("""
            SELECT DISTINCT courses.course_id,courses.title FROM courses
            JOIN lessons ON courses.course_id = lessons.course_id
            JOIN progress ON lessons.lesson_id = progress.lesson_id
            WHERE progress.student_id=?
        """,(student_id,)).fetchall()
        if not enrolled_courses:
            st.info("You have not enrolled in any courses yet.")
        for course in enrolled_courses:
            st.markdown(f"**{course[1]}**")
    except:
        st.info("No progress yet.")

# ------------------- ADMIN DASHBOARD -------------------
def admin_dashboard():
    st.subheader("Admin Dashboard")
    st.markdown("### All Students")
    try:
        students = c.execute("SELECT student_id, full_name, email, mobile, profession, institution, sex FROM students").fetchall()
        st.table(students)
    except:
        st.info("No students registered yet.")

# ------------------- APP MAIN -------------------
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

page = st.session_state['page']

if page == 'home':
    home_page()
    st.sidebar.button("Admin", on_click=lambda: st.session_state.update({'page':'admin_login'}))
elif page == 'login':
    student_login()
    st.markdown("Or create a new account below:")
    student_signup()
elif page == 'admin_login':
    admin_login()
elif page == 'student_dashboard':
    student_dashboard()
elif page == 'admin_dashboard':
    admin_dashboard()
