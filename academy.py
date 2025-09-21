import streamlit as st
import sqlite3
import re
import pandas as pd

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
    if uploaded_file is not None:
        return uploaded_file.read()
    return None

def get_courses():
    return c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()

def get_modules(course_id):
    return c.execute("SELECT * FROM modules WHERE course_id=? ORDER BY module_id ASC", (course_id,)).fetchall()

def add_student(full_name, email, password, gender, profession, institution):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,?,?)",
                  (full_name, email, password, gender, profession, institution, now, now))
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

# ---------------------------
# Header (Logo + Name)
# ---------------------------
def display_header():
    st.markdown("""
    <div style="display:flex; align-items:center; margin-bottom:20px;">
        <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right:15px;">
        <h1 style="margin:0; font-family:'Times New Roman', serif; color:#000000;">EinTrust Academy</h1>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# Display Courses
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
                if st.button("Enroll", key=f"enroll_{course[0]}_{idx}", use_container_width=True):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if show_modules:
                modules = get_modules(course[0])
                if modules:
                    st.write("Modules:")
                    for m in modules:
                        st.write(f"- {m[2]} ({m[4]})")

# ---------------------------
# Pages
# ---------------------------
def page_home():
    display_header()
    main_tabs = st.tabs(["Courses", "Student", "Admin"])
    # Courses Tab
    with main_tabs[0]:
        st.subheader("Courses")
        student_id = st.session_state.get("student", [None])[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)
    # Student Tab
    with main_tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        with student_tabs[0]:
            page_signup()
        with student_tabs[1]:
            page_login()
    # Admin Tab
    with main_tabs[2]:
        page_admin()
    st.markdown("""
<div style="text-align:center; padding:10px; color:#888888; margin-top:40px;">
&copy; 2025 EinTrust. All rights reserved.
</div>
    """, unsafe_allow_html=True)

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
                    st.success("Profile created successfully! Please login.")
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.session_state["page"] = "student_dashboard"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

def page_student_dashboard():
    display_header()
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
        display_courses(enrolled_courses, show_modules=True)
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()
    else:
        st.warning("Please login first.")

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
    display_header()
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard", "Students Data", "Courses Data", "Logout"])
    with tabs[0]:
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        cols = st.columns(3)
        cols[0].markdown(f"<div style='text-align:center; padding:20px;'><h2>{total_courses}</h2>Courses</div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div style='text-align:center; padding:20px;'><h2>{total_modules}</h2>Modules</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div style='text-align:center; padding:20px;'><h2>{total_students}</h2>Students</div>", unsafe_allow_html=True)
    with tabs[1]:
        st.subheader("Students Data")
        students = c.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
        if students:
            df = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
            st.dataframe(df)
        else:
            st.info("No students found.")
    with tabs[2]:
        course_subtabs = st.tabs(["Add Course", "Add Module", "Update Course", "Update Module"])

        # Add Course
        with course_subtabs[0]:
            st.subheader("Add New Course")
            with st.form("add_course_form"):
                title = st.text_input("Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price (₹)", min_value=0.0, value=0.0, step=1.0)
                submitted = st.form_submit_button("Add Course")
                if submitted:
                    add_course(title, subtitle, desc, price)
                    st.success(f"Course '{title}' added successfully!")

        # Add Module
        with course_subtabs[1]:
            st.subheader("Add New Module")
            courses = get_courses()
            if courses:
                course_options = {f"{c[1]} (ID:{c[0]})": c[0] for c in courses}
                with st.form("add_module_form"):
                    selected_course = st.selectbox("Select Course", list(course_options.keys()))
                    title = st.text_input("Module Title")
                    desc = st.text_area("Module Description")
                    module_type = st.selectbox("Module Type", ["Video","PDF","Quiz","Other"])
                    uploaded_file = st.file_uploader("Upload File (optional)")
                    link = st.text_input("Link (optional)")
                    submitted = st.form_submit_button("Add Module")
                    if submitted:
                        add_module(course_options[selected_course], title, desc, module_type, convert_file_to_bytes(uploaded_file), link)
                        st.success(f"Module '{title}' added successfully!")
            else:
                st.info("Add courses first to add modules.")
            # Update Course
        with course_subtabs[2]:
            st.subheader("Update Existing Course")
            courses = get_courses()
            if courses:
                course_options = {f"{c[1]} (ID:{c[0]})": c[0] for c in courses}
                selected_course = st.selectbox("Select Course to Update", list(course_options.keys()))
                course_data = c.execute("SELECT * FROM courses WHERE course_id=?", (course_options[selected_course],)).fetchone()
                with st.form("update_course_form"):
                    title = st.text_input("Title", value=course_data[1])
                    subtitle = st.text_input("Subtitle", value=course_data[2])
                    desc = st.text_area("Description", value=course_data[3])
                    price = st.number_input("Price (₹)", min_value=0.0, value=course_data[4], step=1.0)
                    submitted = st.form_submit_button("Update Course")
                    if submitted:
                        update_course(course_options[selected_course], title, subtitle, desc, price)
                        st.success(f"Course '{title}' updated successfully!")
                if st.button("Delete Course"):
                    delete_course(course_data[0])
                    st.success(f"Course '{title}' deleted successfully!")
            else:
                st.info("No courses found.")
            # Update Module
        with course_subtabs[3]:
            st.subheader("Update Existing Module")
            courses = get_courses()
            if courses:
                course_options = {f"{c[1]} (ID:{c[0]})": c[0] for c in courses}
                selected_course = st.selectbox("Select Course", list(course_options.keys()), key="update_module_course")
                modules = get_modules(course_options[selected_course])
                if modules:
                    module_options = {f"{m[2]} (ID:{m[0]})": m[0] for m in modules}
                    selected_module = st.selectbox("Select Module", list(module_options.keys()))
                    module_data = c.execute("SELECT * FROM modules WHERE module_id=?", (module_options[selected_module],)).fetchone()
                    with st.form("update_module_form"):
                        title = st.text_input("Module Title", value=module_data[2])
                        desc = st.text_area("Module Description", value=module_data[3])
                        module_type = st.selectbox("Module Type", ["Video","PDF","Quiz","Other"], index=["Video","PDF","Quiz","Other"].index(module_data[4]))
                        uploaded_file = st.file_uploader("Upload File (optional)")
                        link = st.text_input("Link (optional)", value=module_data[6] if module_data[6] else "")
                        submitted = st.form_submit_button("Update Module")
                        if submitted:
                            file_bytes = convert_file_to_bytes(uploaded_file) if uploaded_file else module_data[5]
                            update_module(module_data[0], title, desc, module_type, file_bytes, link)
                            st.success(f"Module '{title}' updated successfully!")
                    if st.button("Delete Module"):
                        delete_module(module_data[0])
                        st.success(f"Module '{module_data[2]}' deleted successfully!")
                else:
                    st.info("No modules found for this course.")
            else:
                st.info("No courses found.")
        
    with tabs[3]:
        if st.button("Logout Admin"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.experimental_rerun()

# ---------------------------
# Router
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
