import streamlit as st
import sqlite3
import re
import pandas as pd

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# Courses table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
   course_id INTEGER PRIMARY KEY AUTOINCREMENT,
   title TEXT,
   subtitle TEXT,
   description TEXT,
   price REAL,
   views INTEGER DEFAULT 0
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
   views INTEGER DEFAULT 0,
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
   first_enrollment TEXT,
   last_login TEXT
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
    return uploaded_file.read() if uploaded_file else None

# ---------------------------
# Student Functions
# ---------------------------
def add_student(full_name, email, password, gender, profession, institution):
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))",
                  (full_name, email, password, gender, profession, institution))
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

# ---------------------------
# Admin Functions
# ---------------------------
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

def delete_module(module_id):
    c.execute("DELETE FROM modules WHERE module_id=?", (module_id,))
    conn.commit()

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def get_modules(course_id):
    return c.execute("SELECT * FROM modules WHERE course_id=? ORDER BY module_id ASC", (course_id,)).fetchall()

# ---------------------------
# Streamlit Config & CSS
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
.unique-btn button {
   background-color: #4CAF50 !important;
   color: white !important;
   border-radius: 8px !important;
   border: none !important;
   padding: 12px 25px !important;
   font-weight: bold !important;
   width: 100%;
}
.unique-btn button:hover {background-color: #45a049 !important; color: #ffffff !important;}
.course-card {background: #1c1c1c; border-radius: 12px; padding: 16px; margin: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.6);}
.course-title {font-size: 22px; font-weight: bold; color: #f0f0f0;}
.course-subtitle {font-size: 16px; color: #b0b0b0;}
.course-desc {font-size: 14px; color: #cccccc;}
.section-header {border-bottom: 1px solid #333333; padding-bottom: 8px; margin-bottom: 10px; font-size: 20px;}
.block {background:#1c1c1c; padding:15px; margin-bottom:15px; border-radius:10px; box-shadow:0 4px 8px rgba(0,0,0,0.5);}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Display Courses Function
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
                if st.button("Enroll", key=f"enroll_{course[0]}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}", use_container_width=True):
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
# Pages: Home, Student Signup/Login, Student Dashboard
# ---------------------------
def page_home():
    st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between;">
<h1>EinTrust Academy</h1>
<p>Learn sustainability and more!</p>
</div>
""", unsafe_allow_html=True)

def page_student_signup():
    st.subheader("Student Signup")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        profession = st.text_input("Profession")
        institution = st.text_input("Institution/College")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if not is_valid_email(email):
                st.error("Invalid email.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, uppercase, number, special char.")
            elif add_student(full_name,email,password,gender,profession,institution):
                st.success("Signup successful! Please login.")
            else:
                st.error("Email already exists.")

def page_student_login():
    st.subheader("Student Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = authenticate_student(email, password)
            if user:
                st.session_state["student"] = user
                st.success(f"Welcome {user[1]}!")
            else:
                st.error("Invalid credentials.")

def page_student_dashboard():
    st.subheader("Student Dashboard")
    student = st.session_state.get("student")
    if student:
        st.write(f"Logged in as: {student[1]} ({student[2]})")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0], show_modules=True)

# ---------------------------
# Admin Dashboard
# ---------------------------
def page_admin_dashboard():
    st.subheader("Admin Dashboard")
    tabs = st.tabs(["Courses Data","Students Data"])
    
    # Courses Data
    with tabs[0]:
        st.subheader("Courses Management")
        course_subtabs = st.tabs(["Add Course","Add Module","Update Course","Update Module"])
        
        # ---------- Add Course ----------
        with course_subtabs[0]:
            st.markdown('<div class="block"><h4>Add Course</h4></div>', unsafe_allow_html=True)
            with st.form("add_course_form"):
                title = st.text_input("Course Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price", min_value=0.0, step=1.0)
                submitted = st.form_submit_button("Add Course")
                if submitted:
                    add_course(title, subtitle, desc, price)
                    st.success(f"Course '{title}' added!")
        
        # ---------- Add Module ----------
        with course_subtabs[1]:
            st.markdown('<div class="block"><h4>Add Module</h4></div>', unsafe_allow_html=True)
            courses = get_courses()
            if not courses:
                st.info("No courses available to add module.")
            else:
                course_select = st.selectbox("Select Course", [f"{c[0]} - {c[1]}" for c in courses])
                course_id = int(course_select.split(" - ")[0])
                with st.form("add_module_form"):
                    module_title = st.text_input("Module Title")
                    module_desc = st.text_area("Module Description")
                    module_type = st.selectbox("Module Type", ["Video","PPT","PDF","Task","Quiz"])
                    uploaded_file = st.file_uploader("Upload File (if applicable)")
                    link = st.text_input("External Link (if applicable)")
                    submitted = st.form_submit_button("Add Module")
                    if submitted:
                        file_bytes = convert_file_to_bytes(uploaded_file)
                        add_module(course_id, module_title, module_desc, module_type, file_bytes, link)
                        st.success(f"Module '{module_title}' added!")
        
        # ---------- Update Course ----------
        with course_subtabs[2]:
            st.markdown('<div class="block"><h4>Update/Delete Course</h4></div>', unsafe_allow_html=True)
            courses = get_courses()
            if not courses:
                st.info("No courses available.")
            else:
                for course in courses:
                    st.write(f"{course[0]} - {course[1]}")
                    col1, col2 = st.columns([1,1])
                    with col1:
                        with st.form(f"update_course_form_{course[0]}"):
                            new_title = st.text_input("Title", value=course[1])
                            new_subtitle = st.text_input("Subtitle", value=course[2])
                            new_desc = st.text_area("Description", value=course[3])
                            new_price = st.number_input("Price", min_value=0.0, value=course[4])
                            submitted = st.form_submit_button("Update Course")
                            if submitted:
                                update_course(course[0], new_title, new_subtitle, new_desc, new_price)
                                st.success("Course updated!")
                    with col2:
                        if st.button("Delete Course", key=f"delete_course_{course[0]}"):
                            delete_course(course[0])
                            st.success("Course deleted!")
                            st.experimental_rerun()
        
        # ---------- Update Module ----------
        with course_subtabs[3]:
            st.markdown('<div class="block"><h4>Update/Delete Module</h4></div>', unsafe_allow_html=True)
            courses = get_courses()
            for course in courses:
                st.write(f"Modules of {course[1]}")
                modules = get_modules(course[0])
                if not modules:
                    st.write("No modules.")
                else:
                    for m in modules:
                        col1, col2 = st.columns([1,1])
                        with col1:
                            with st.form(f"update_module_form_{m[0]}"):
                                new_title = st.text_input("Title", value=m[2])
                                new_desc = st.text_area("Description", value=m[3])
                                new_type = st.selectbox("Type", ["Video","PPT","PDF","Task","Quiz"], index=["Video","PPT","PDF","Task","Quiz"].index(m[4]))
                                new_link = st.text_input("Link", value=m[6] if m[6] else "")
                                submitted = st.form_submit_button("Update Module")
                                if submitted:
                                    update_module(m[0], new_title, new_desc, new_type, m[5], new_link)
                                    st.success("Module updated!")
                        with col2:
                            if st.button("Delete Module", key=f"delete_module_{m[0]}"):
                                delete_module(m[0])
                                st.success("Module deleted!")
                                st.experimental_rerun()
    
    # Students Data
    with tabs[1]:
        st.subheader("Students Management")
        students = c.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
        if not students:
            st.info("No students.")
        else:
            df = pd.DataFrame(students, columns=[desc[0] for desc in c.description])
            st.dataframe(df)
            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "students.csv", "text/csv")

# ---------------------------
# Main
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

pages = ["Home","Student Signup","Student Login","Student Dashboard","Admin Dashboard"]
page = st.sidebar.radio("Navigation", pages)

if page=="Home":
    page_home()
elif page=="Student Signup":
    page_student_signup()
elif page=="Student Login":
    page_student_login()
elif page=="Student Dashboard":
    if "student" not in st.session_state:
        st.warning("Please login first.")
    else:
        page_student_dashboard()
elif page=="Admin Dashboard":
    page_admin_dashboard()
