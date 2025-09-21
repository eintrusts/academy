import streamlit as st
import sqlite3
import re
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
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
   completed INTEGER DEFAULT 0,
   time_spent REAL DEFAULT 0,
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price, student_courses.completed, student_courses.time_spent
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

# Certificate generation
def generate_certificate(student_name, course_title):
    width, height = 1200, 850
    certificate = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(certificate)
    title_font = ImageFont.truetype("arialbd.ttf", 60)
    subtitle_font = ImageFont.truetype("arial.ttf", 40)
    body_font = ImageFont.truetype("arial.ttf", 30)
    draw.rectangle([(20,20),(width-20,height-20)], outline="black", width=6)
    draw.text((width/2, 150), "EinTrust Academy", font=title_font, fill="darkgreen", anchor="mm")
    draw.text((width/2, 300), "Certificate of Completion", font=subtitle_font, fill="black", anchor="mm")
    draw.text((width/2, 450), student_name, font=body_font, fill="blue", anchor="mm")
    draw.text((width/2, 550), f"has successfully completed the course:", font=body_font, fill="black", anchor="mm")
    draw.text((width/2, 600), f"{course_title}", font=body_font, fill="red", anchor="mm")
    completion_date = datetime.now().strftime("%d %B %Y")
    draw.text((width/2, 700), f"Date: {completion_date}", font=body_font, fill="black", anchor="mm")
    buf = io.BytesIO()
    certificate.save(buf, format="PDF")
    buf.seek(0)
    return buf

# ---------------------------
# Page Config + CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0; font-family: 'Times New Roman', serif;}
.stApp {background-color: #0d0f12; color: #e0e0e0; font-family: 'Times New Roman', serif;}
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
.card {background:#1e1e1e; border-radius:10px; padding:20px; text-align:center; margin:10px;}
.card-title {font-size:26px; font-weight:bold; color:#4CAF50;}
.card-subtitle {font-size:16px; color:#bbbbbb;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Sample Data for Testing
# ---------------------------
def add_sample_courses():
    if not get_courses():
        course1 = add_course("Basics of Sustainability", "Introduction to ESG & Climate", "Learn the fundamentals of sustainability, ESG frameworks, and climate action.", 0)
        course2 = add_course("Climate Change & Action", "Global Warming Explained", "Understand climate change, its impacts, and mitigation strategies.", 0)
        add_module(course1, "What is Sustainability?", "Introduction to Sustainability", "Video", None, "https://www.youtube.com/watch?v=example1")
        add_module(course1, "ESG Overview", "Learn ESG frameworks and compliance", "PDF", None, None)
        add_module(course2, "Climate Science Basics", "Understanding climate change", "Video", None, "https://www.youtube.com/watch?v=example2")
        add_module(course2, "Mitigation & Adaptation", "How we can act", "PDF", None, None)

add_sample_courses()

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
                if st.button("Enroll", key=f"enroll_{course[0]}_{idx}"):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}_{idx}"):
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
# Pages
# ---------------------------
def render_logo_name():
    st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
<img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="60" style="margin-right: 15px;">
<h1 style="margin:0; font-family:'Times New Roman', serif; color:#ffffff;">EinTrust Academy</h1>
</div>
""", unsafe_allow_html=True)

def render_footer():
    st.markdown("""
<div style="position: relative; bottom: 0; width: 100%; text-align: center; padding: 10px; color: #888888; margin-top: 40px;">
&copy; 2025 EinTrust. All rights reserved.
</div>
""", unsafe_allow_html=True)

# --- Home, Signup, Login ---
def page_home():
    render_logo_name()
    main_tabs = st.tabs(["Courses", "Student", "Admin"])

    with main_tabs[0]:
        st.subheader("Courses")
        student_id = st.session_state.get("student")[0] if "student" in st.session_state else None
        courses = get_courses()
        display_courses(courses, enroll=True, student_id=student_id)

    with main_tabs[1]:
        student_tabs = st.tabs(["Signup", "Login"])
        with student_tabs[0]:
            page_signup()
        with student_tabs[1]:
            page_login()

    with main_tabs[2]:
        page_admin()

    render_footer()

def page_signup():
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email ID", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        gender = st.selectbox("Gender", ["Male","Female","Other"], key="signup_gender")
        profession = st.text_input("Profession", key="signup_prof")
        institution = st.text_input("Institution", key="signup_inst")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not is_valid_email(email):
                st.error("Enter a valid email address.")
            elif not is_valid_password(password):
                st.error("Password must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            else:
                success = add_student(full_name, email, password, gender, profession, institution)
                if success:
                    st.success("Profile created successfully! Please login below.")
                else:
                    st.error("Email already registered. Please login.")

def page_login():
    st.header("Student Login")
    email = st.text_input("Email ID", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        student = authenticate_student(email, password)
        if student:
            st.session_state["student"] = student
            st.experimental_rerun()  # Redirect to student dashboard
        else:
            st.error("Invalid credentials.")

# --- Student Dashboard with sub-tabs ---
def page_student_dashboard():
    student = st.session_state.get("student")
    if not student:
        st.error("Please login first")
        return

    st.title(f"Welcome {student[1]}")

    tabs = st.tabs(["Courses", "My Learning", "My Achievements", "Profile", "Logout"])

    # Courses Tab
    with tabs[0]:
        courses = get_courses()
        for c in courses:
            st.markdown(f"### {c[1]} - {c[2]}")
            st.write(c[3])
            st.write(f"Price: {c[4]}")
            if st.button(f"Enroll in {c[1]}", key=f"enroll_{c[0]}"):
                conn = sqlite3.connect("academy.db")
                cur = conn.cursor()
                cur.execute("INSERT OR IGNORE INTO student_courses (student_id, course_id) VALUES (?, ?)", (student[0], c[0]))
                conn.commit()
                conn.close()
                st.success(f"Enrolled in {c[1]}")

    # My Learning Tab
    with tabs[1]:
        enrolled_courses = get_student_courses(student[0])
        if enrolled_courses:
            for ec in enrolled_courses:
                st.markdown(f"### {ec[1]} - {ec[2]}")
                st.write(ec[3])
                st.write(f"Status: {'Completed' if ec[5] else 'In Progress'}")
                st.write(f"Time Spent: {ec[6]} seconds")
                if not ec[5]:
                    if st.button(f"Mark {ec[1]} as Completed", key=f"complete_{ec[0]}"):
                        conn = sqlite3.connect("academy.db")
                        cur = conn.cursor()
                        cur.execute("UPDATE student_courses SET completed=1 WHERE student_id=? AND course_id=?", (student[0], ec[0]))
                        conn.commit()
                        conn.close()
                        st.success(f"{ec[1]} marked as completed")
                        st.rerun()
        else:
            st.info("You are not enrolled in any courses yet.")

    # My Achievements Tab
    with tabs[2]:
        conn = sqlite3.connect("academy.db")
        cur = conn.cursor()
        completed_courses = cur.execute(
            '''SELECT courses.course_id, courses.title, courses.subtitle, student_courses.time_spent
               FROM courses JOIN student_courses ON courses.course_id = student_courses.course_id
               WHERE student_courses.student_id=? AND student_courses.completed=1''',
            (student[0],)
        ).fetchall()
        conn.close()

        if completed_courses:
            st.subheader("Your Achievements")
            for cc in completed_courses:
                st.markdown(f"### {cc[1]} - {cc[2]}")
                st.write(f"Time Spent: {cc[3]} seconds")

                cert_key = f"cert_{student[0]}_{cc[0]}"
                if st.button(f"Download Certificate for {cc[1]}", key=cert_key):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(200, 20, "Certificate of Completion", ln=True, align="C")
                    pdf.ln(20)
                    pdf.set_font("Arial", '', 12)
                    pdf.multi_cell(0, 10, f"This is to certify that {student[1]} has successfully completed the course '{cc[1]}'.")
                    pdf.ln(10)
                    pdf.cell(0, 10, f"Time Spent: {cc[3]} seconds", ln=True)
                    pdf.ln(20)
                    pdf.cell(0, 10, "EinTrust Academy", ln=True, align="R")

                    cert_file = f"certificate_{student[0]}_{cc[0]}.pdf"
                    pdf.output(cert_file)

                    with open(cert_file, "rb") as f:
                        st.download_button(
                            label="Download Certificate",
                            data=f,
                            file_name=cert_file,
                            mime="application/pdf"
                        )
        else:
            st.info("No achievements yet. Complete courses to earn certificates.")

    # Profile Tab
    with tabs[3]:
        st.subheader("Edit Profile")
        new_name = st.text_input("Name", value=student[1])
        new_email = st.text_input("Email", value=student[2])
        new_password = st.text_input("Password", type="password", value=student[3])
        if st.button("Update Profile"):
            conn = sqlite3.connect("academy.db")
            cur = conn.cursor()
            cur.execute("UPDATE students SET name=?, email=?, password=? WHERE student_id=?", (new_name, new_email, new_password, student[0]))
            conn.commit()
            conn.close()
            st.success("Profile updated successfully")
            st.session_state["student"] = (student[0], new_name, new_email, new_password)
            st.rerun()

    # Logout Tab
    with tabs[4]:
        if st.button("Logout"):
            st.session_state.pop("student", None)
            st.session_state["page"] = "home"
            st.rerun()

# --- Admin ---
def page_admin():
    st.header("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password", key="admin_pass")
    if st.button("Login as Admin", key="admin_btn"):
        if admin_pass == "eintrust2025":
            st.session_state["page"] = "admin_dashboard"
            st.experimental_rerun()
        else:
            st.error("Wrong admin password.")

# --- Admin Dashboard ---
def page_admin_dashboard():
    render_logo_name()
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard", "Students Data", "Courses Data", "Logout"])

    with tabs[0]:
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_modules = c.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        cols = st.columns(3)
        cols[0].markdown(f"<div class='card'><div class='card-title'>{total_courses}</div><div class='card-subtitle'>Courses</div></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='card'><div class='card-title'>{total_modules}</div><div class='card-subtitle'>Modules</div></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='card'><div class='card-title'>{total_students}</div><div class='card-subtitle'>Students</div></div>", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Students Data")
        students = c.execute("SELECT * FROM students").fetchall()
        df = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
        st.dataframe(df)

    with tabs[2]:
        st.subheader("Courses Data")
        courses = get_courses()
        display_courses(courses, show_modules=True, editable=True)

    with tabs[3]:
        if st.button("Logout Admin"):
            del st.session_state["page"]
            st.experimental_rerun()

# ---------------------------
# Main Execution
# ---------------------------
if "student" in st.session_state:
    page_student_dashboard()
elif st.session_state.get("page") == "admin_dashboard":
    page_admin_dashboard()
else:
    page_home()
