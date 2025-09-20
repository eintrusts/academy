import streamlit as st
import sqlite3
import re
import io
import pandas as pd
import plotly.express as px

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
    first_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def authenticate_student(email, password):
    student = c.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
    if student:
        c.execute("UPDATE students SET last_login=CURRENT_TIMESTAMP WHERE student_id=?", (student[0],))
        conn.commit()
    return student

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

def update_lesson(lesson_id, title, description, lesson_type, file, link):
    c.execute("UPDATE lessons SET title=?, description=?, lesson_type=?, file=?, link=? WHERE lesson_id=?",
              (title, description, lesson_type, file, link, lesson_id))
    conn.commit()

def delete_lesson(lesson_id):
    c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson_id,))
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
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Display Courses
# ---------------------------
def display_courses(courses, enroll=False, student_id=None, show_lessons=False, editable=False):
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
    # Logo + Title
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
        <h1 style="margin:0; color:#ffffff;">EinTrust Academy</h1>
    </div>
    """, unsafe_allow_html=True)

    # Main Tabs
    main_tabs = st.tabs(["Courses", "Student", "Admin"])

    # Courses Tab
    with main_tabs[0]:
        st.subheader("Available Courses")
        student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)

    # Student Tab with sub-tabs
    with main_tabs[1]:
        default_student_tab = st.session_state.get("student_tab", "Signup")
        student_tabs = st.tabs(["Signup", "Login"])
        if default_student_tab == "Signup":
            with student_tabs[0]:
                page_signup()
        else:  # Login
            with student_tabs[1]:
                page_login()
        st.session_state["student_tab"] = "Signup"

    # Admin Tab
    with main_tabs[2]:
        page_admin()

    # Footer
    st.markdown("""
    <div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px;">
        &copy; 2025 EinTrust Academy. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# Signup Page
# ---------------------------
def page_signup():
    st.header("Create Profile")
    with st.form("signup_form"):
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
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Redirecting to login...")
                    st.session_state["page"] = "home"
                    st.session_state["student_tab"] = "Login"
                    st.experimental_rerun()
                else:
                    st.error("Email already registered. Please login.")

# ---------------------------
# Login Page
# ---------------------------
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
        st.subheader("Available Courses")
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student[0])

        st.subheader("Your Enrolled Courses")
        enrolled_courses = get_student_courses(student[0])
        display_courses(enrolled_courses, show_lessons=True)

        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

# ---------------------------
# Admin Page
# ---------------------------
import plotly.express as px
import pandas as pd

def page_admin_dashboard():
    st.header("Admin Dashboard")
    tab_dashboard, tab_students, tab_courses, tab_logout = st.tabs(["Dashboard","Students Data","Courses Data","Logout"])
    
    # ---------------- Dashboard Tab ----------------
    with tab_dashboard:
        st.subheader("Overview Metrics")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", total_students)
        col2.metric("Total Courses", total_courses)
        col3.metric("Total Modules", total_modules)

        # Most Enrolled Courses Graph
        enroll_data = c.execute("""
            SELECT courses.title, COUNT(student_courses.id) as enroll_count 
            FROM courses LEFT JOIN student_courses 
            ON courses.course_id = student_courses.course_id
            GROUP BY courses.course_id
        """).fetchall()
        if enroll_data:
            df_enroll = pd.DataFrame(enroll_data, columns=["Course","Enrollments"])
            fig_course = px.bar(df_enroll, x="Course", y="Enrollments", title="Most Enrolled Courses", text="Enrollments", color="Enrollments")
            st.plotly_chart(fig_course, use_container_width=True)

        # Most Viewed Modules Graph (simulated, as we don't track views yet)
        modules_data = c.execute("SELECT title FROM lessons").fetchall()
        if modules_data:
            df_mod = pd.DataFrame(modules_data, columns=["Module"])
            df_mod["Views"] = 1  # placeholder
            fig_mod = px.bar(df_mod, x="Module", y="Views", title="Most Viewed Modules", text="Views")
            st.plotly_chart(fig_mod, use_container_width=True)

    # ---------------- Students Data Tab ----------------
    with tab_students:
        st.subheader("Students List")
        students = c.execute("SELECT * FROM students ORDER BY student_id ASC").fetchall()
        if students:
            st.write("### Students Table")
            for idx, s in enumerate(students, start=1):
                st.markdown(f"**{idx}. {s[1]} | {s[2]} | {s[4]} | {s[5]} | {s[6]}**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Edit {s[1]}", key=f"edit_student_{s[0]}"):
                        with st.form(f"edit_student_form_{s[0]}"):
                            full_name = st.text_input("Full Name", value=s[1])
                            email = st.text_input("Email", value=s[2])
                            gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(s[4]))
                            profession = st.text_input("Profession", value=s[5])
                            institution = st.text_input("Institution", value=s[6])
                            if st.form_submit_button("Update Student"):
                                c.execute("""
                                    UPDATE students SET full_name=?, email=?, gender=?, profession=?, institution=? WHERE student_id=?
                                """, (full_name, email, gender, profession, institution, s[0]))
                                conn.commit()
                                st.success("Student updated successfully!")
                                st.experimental_rerun()
                with col2:
                    if st.button(f"Delete {s[1]}", key=f"del_student_{s[0]}"):
                        c.execute("DELETE FROM students WHERE student_id=?", (s[0],))
                        conn.commit()
                        st.success("Student deleted!")
                        st.experimental_rerun()
        else:
            st.info("No students found.")

    # ---------------- Courses Data Tab ----------------
    with tab_courses:
        course_subtabs = st.tabs(["Add Course","Update Course"])
        
        # ---- Add Course ----
        with course_subtabs[0]:
            st.subheader("Add New Course")
            with st.form("add_course_form"):
                title = st.text_input("Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price", min_value=0.0, step=1.0)
                submitted = st.form_submit_button("Add Course")
                
                if submitted:
                    course_id = add_course(title, subtitle, desc, price)
                    st.success("Course added successfully!")
                    st.experimental_rerun()

            st.markdown("---")
            st.subheader("Add Modules")
            courses_list = get_courses()
            if courses_list:
                selected_course_name = st.selectbox("Select Course for Modules", [c[1] for c in courses_list])
                course_id = [c[0] for c in courses_list if c[1] == selected_course_name][0]

                with st.form("add_module_form"):
                    mod_title = st.text_input("Module Title")
                    mod_type = st.selectbox("Type", ["Video","PPT","PDF","Task","Quiz"])
                    mod_desc = st.text_area("Module Description")
                    uploaded_file = None
                    link = None
                    task_deadline = None
                    quiz_questions = None

                    if mod_type in ["Video","PPT","PDF"]:
                        uploaded_file = st.file_uploader(f"Upload {mod_type} file")
                    elif mod_type == "Task":
                        task_deadline = st.date_input("Task Deadline")
                    elif mod_type == "Quiz":
                        quiz_questions = st.text_area("Quiz Questions")

                    if st.form_submit_button("Add Module"):
                        file_bytes = convert_file_to_bytes(uploaded_file)
                        extra_info = ""
                        if mod_type == "Task":
                            extra_info = str(task_deadline)
                        elif mod_type == "Quiz":
                            extra_info = quiz_questions
                        add_lesson(course_id, mod_title, mod_desc, mod_type, file_bytes if file_bytes else extra_info, extra_info)
                        st.success("Module added successfully!")
                        st.experimental_rerun()

        # ---- Update Course ----
        with course_subtabs[1]:
            st.subheader("Update Existing Course")
            courses_list = get_courses()
            if courses_list:
                selected_course_name = st.selectbox("Select Course to Update", [c[1] for c in courses_list])
                course_id = [c[0] for c in courses_list if c[1] == selected_course_name][0]
                course = c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()

                # Edit Course Info
                with st.form("update_course_form"):
                    title = st.text_input("Title", value=course[1])
                    subtitle = st.text_input("Subtitle", value=course[2])
                    desc = st.text_area("Description", value=course[3])
                    price = st.number_input("Price", value=course[4], min_value=0.0, step=1.0)
                    if st.form_submit_button("Update Course"):
                        update_course(course_id, title, subtitle, desc, price)
                        st.success("Course updated successfully!")
                        st.experimental_rerun()

                st.markdown("---")
                st.subheader("Modules in this Course")
                lessons = get_lessons(course_id)
                if lessons:
                    for l in lessons:
                        with st.expander(f"{l[2]} ({l[4]}) - Edit Module"):
                            with st.form(f"edit_module_form_{l[0]}"):
                                mod_title = st.text_input("Module Title", value=l[2])
                                mod_type = st.selectbox("Type", ["Video","PPT","PDF","Task","Quiz"], index=["Video","PPT","PDF","Task","Quiz"].index(l[4]))
                                mod_desc = st.text_area("Module Description", value=l[3])
                                uploaded_file = None
                                task_deadline = None
                                quiz_questions = None

                                if mod_type in ["Video","PPT","PDF"]:
                                    st.write("File already uploaded. Upload new to replace.")
                                    uploaded_file = st.file_uploader(f"Upload new {mod_type} file", key=f"file_{l[0]}")
                                elif mod_type == "Task":
                                    task_deadline = st.date_input("Task Deadline", value=pd.to_datetime(l[5]) if l[5] else pd.to_datetime("today"))
                                elif mod_type == "Quiz":
                                    quiz_questions = st.text_area("Quiz Questions", value=l[5] if l[5] else "")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button(f"Update Module {l[0]}"):
                                        file_bytes = convert_file_to_bytes(uploaded_file)
                                        extra_info = ""
                                        if mod_type == "Task":
                                            extra_info = str(task_deadline)
                                        elif mod_type == "Quiz":
                                            extra_info = quiz_questions
                                        add_or_update_file = file_bytes if file_bytes else l[5] if l[4] in ["Video","PPT","PDF"] else extra_info
                                        update_lesson(l[0], mod_title, mod_desc, mod_type, add_or_update_file, extra_info)
                                        st.success("Module updated successfully!")
                                        st.experimental_rerun()
                                with col2:
                                    if st.button(f"Delete Module {l[0]}"):
                                        delete_lesson(l[0])
                                        st.success("Module deleted successfully!")
                                        st.experimental_rerun()
                else:
                    st.info("No modules added yet.")

    # ---------------- Logout Tab ----------------
    with tab_logout:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()

# ---------------------------
# Main Routing
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
