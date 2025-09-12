import streamlit as st
import sqlite3, os, time
from fpdf import FPDF

# ---------------------------
# CSS Styling
# ---------------------------
st.markdown("""
<style>
body {background-color:#121212; color:#ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
h1,h2,h3,h4,h5,h6 {color:#f5f5f5;}
div.card {background-color:#1e1e1e; padding:15px; margin:10px 0; border-radius:10px; transition: transform 0.2s;}
div.card:hover {transform: scale(1.02); background-color:#2a2a2a;}
.stButton>button {background-color:#ff9900; color:#000000; font-weight:bold; border-radius:8px; padding:10px; margin:5px 0;}
.stButton>button:hover {background-color:#ffaa33;}
a {color:#ff9900;}
hr {border:1px solid #555;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Logo + Header
# ---------------------------
st.image("https://raw.githubusercontent.com/eintrusts/CAP/main/EinTrust%20%20(2).png", width=250)
st.markdown("<h2 style='text-align:center; color:#ff9900;'>EinTrust Academy</h2>", unsafe_allow_html=True)
st.markdown("<hr style='border:1px solid #555;'>",unsafe_allow_html=True)

# ---------------------------
# Database Connection
# ---------------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# ---------------------------
# Create Tables
# ---------------------------
c.execute("""CREATE TABLE IF NOT EXISTS students(
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            sex TEXT,
            profession TEXT,
            institution TEXT,
            mobile TEXT
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS courses(
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price REAL
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS lessons(
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            content_type TEXT,
            content_path TEXT
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS lesson_progress(
            student_id INTEGER,
            lesson_id INTEGER,
            viewed INTEGER DEFAULT 0,
            PRIMARY KEY(student_id,lesson_id)
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS certificates(
            student_id INTEGER,
            course_id INTEGER,
            cert_file TEXT,
            PRIMARY KEY(student_id,course_id)
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS payments(
            student_id INTEGER,
            course_id INTEGER,
            status TEXT,
            PRIMARY KEY(student_id,course_id)
            )""")
conn.commit()

# ---------------------------
# Dummy Data
# ---------------------------
def load_dummy_data():
    c.execute("INSERT OR IGNORE INTO students(name,email,password,sex,profession,institution,mobile) VALUES(?,?,?,?,?,?,?)",
              ("Test Student","student@example.com","1234","Male","Student","ABC University","9999999999"))
    c.execute("INSERT OR IGNORE INTO courses(title,description,price) VALUES(?,?,?)",
              ("Basics of Sustainability","Learn sustainability fundamentals",0))
    c.execute("INSERT OR IGNORE INTO courses(title,description,price) VALUES(?,?,?)",
              ("Advanced ESG","In-depth ESG course",5000))
    c.execute("INSERT OR IGNORE INTO lessons(course_id,title,content_type,content_path) VALUES(?,?,?,?)",
              (1,"Introduction","text","This is the introduction text."))
    c.execute("INSERT OR IGNORE INTO lessons(course_id,title,content_type,content_path) VALUES(?,?,?,?)",
              (1,"Sustainability Video","video","https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"))
    c.execute("INSERT OR IGNORE INTO lessons(course_id,title,content_type,content_path) VALUES(?,?,?,?)",
              (2,"ESG PDF","pdf","This is a dummy pdf content."))
    conn.commit()
load_dummy_data()

# ---------------------------
# Utilities
# ---------------------------
def inr_format(amount):
    return f"₹{amount:,.0f}"

def enroll_student_lessons(student_id, course_id):
    c.execute("SELECT lesson_id FROM lessons WHERE course_id=?", (course_id,))
    lessons = c.fetchall()
    for lesson in lessons:
        c.execute("INSERT OR IGNORE INTO lesson_progress(student_id, lesson_id, viewed) VALUES (?,?,0)", (student_id, lesson[0]))
    conn.commit()

def mark_lesson_viewed(student_id, lesson_id):
    c.execute("UPDATE lesson_progress SET viewed=1 WHERE student_id=? AND lesson_id=?", (student_id, lesson_id))
    conn.commit()

def generate_certificate(student_name, course_title, student_id, course_id):
    file_name = f"certificate_{student_id}_{course_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",20)
    pdf.cell(0,20,"Certificate of Completion",ln=True,align='C')
    pdf.set_font("Arial","",16)
    pdf.ln(10)
    pdf.multi_cell(0,10,f"This certifies that {student_name} has successfully completed the course '{course_title}'.")
    pdf.output(file_name)
    return file_name

# ---------------------------
# Student Dashboard
# ---------------------------
def student_dashboard(user):
    st.subheader(f"Welcome, {user['name']}!")
    tabs = st.tabs(["Courses","Lessons","Certificates","Profile"])
    
    # Courses Tab
    with tabs[0]:
        c.execute("SELECT * FROM courses")
        courses = c.fetchall()
        for course in courses:
            st.markdown(f"<div class='card'><h3>{course[1]}</h3><p>{course[2]}</p><b>Price: {inr_format(course[3])}</b></div>",unsafe_allow_html=True)
            enrolled=c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=? AND status='Success'",(user['id'],course[0])).fetchone()
            if enrolled: st.success("Enrolled ✅")
            else:
                if st.button(f"Enroll in {course[1]}",key=f"enroll_{course[0]}"):
                    st.success("Simulated Payment Done")
                    enroll_student_lessons(user['id'], course[0])
                    c.execute("INSERT OR IGNORE INTO payments(student_id,course_id,status) VALUES(?,?,?)",(user['id'],course[0],'Success'))
                    conn.commit()
    
    # Lessons Tab
    with tabs[1]:
        st.subheader("My Lessons")
        c.execute("""SELECT l.lesson_id, l.title, l.content_type, l.content_path, c.course_id, c.title 
                     FROM lessons l JOIN payments p ON l.course_id=p.course_id 
                     JOIN courses c ON c.course_id=l.course_id
                     WHERE p.student_id=? AND p.status='Success'""",(user['id'],))
        lessons = c.fetchall()
        for lesson in lessons:
            lesson_id,title,ctype,cpath,course_id,course_title = lesson
            st.markdown(f"<div class='card'><b>Course:</b> {course_title} | <b>Lesson:</b> {title}</div>",unsafe_allow_html=True)
            if ctype=="video": st.video(cpath)
            else: st.write(cpath)
            viewed = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?",(user['id'],lesson_id)).fetchone()[0]
            if viewed: st.success("Completed ✅")
            else:
                if st.button(f"Mark as Complete", key=f"lesson_{lesson_id}"):
                    mark_lesson_viewed(user['id'], lesson_id)
                    st.success("Marked complete!")
        
        # Auto-generate certificates
        c.execute("SELECT course_id FROM payments WHERE student_id=? AND status='Success'", (user['id'],))
        enrolled_courses = c.fetchall()
        for course in enrolled_courses:
            course_id = course[0]
            c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,))
            total_lessons = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM lesson_progress WHERE student_id=? AND lesson_id IN (SELECT lesson_id FROM lessons WHERE course_id=?) AND viewed=1", (user['id'], course_id))
            completed_lessons = c.fetchone()[0]
            if total_lessons==completed_lessons:
                c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (user['id'], course_id))
                cert_exist = c.fetchone()
                if not cert_exist:
                    c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,))
                    course_title = c.fetchone()[0]
                    cert_file = generate_certificate(user['name'], course_title, user['id'], course_id)
                    c.execute("INSERT INTO certificates(student_id, course_id, cert_file) VALUES (?,?,?)", (user['id'], course_id, cert_file))
                    conn.commit()
                    st.success(f"Certificate generated for {course_title}!")
    
    # Certificates Tab
    with tabs[2]:
        st.subheader("My Certificates")
        c.execute("""SELECT c.cert_file, crs.title FROM certificates c 
                     JOIN courses crs ON crs.course_id=c.course_id
                     WHERE c.student_id=?""",(user['id'],))
        certs = c.fetchall()
        if certs:
            for cert_file,course_title in certs:
                st.markdown(f"<div class='card'>Certificate for {course_title}</div>",unsafe_allow_html=True)
                with open(cert_file,"rb") as f:
                    st.download_button(label="Download PDF",data=f,file_name=cert_file)
        else:
            st.info("No certificates yet.")
    
    # Profile Tab
    with tabs[3]:
        st.subheader("My Profile")
        c.execute("SELECT name,email,sex,profession,institution,mobile FROM students WHERE student_id=?",(user['id'],))
        profile = c.fetchone()
        st.write("**Full Name:**", profile[0])
        st.write("**Email:**", profile[1])
        st.write("**Sex:**", profile[2])
        st.write("**Profession:**", profile[3])
        st.write("**Institution:**", profile[4])
        st.write("**Mobile:**", profile[5])
        st.info("Profile editing feature can be added here.")

# ---------------------------
# Admin Dashboard
# ---------------------------
def admin_dashboard():
    tabs = st.tabs(["Students","Courses","Lessons"])
    with tabs[0]:
        st.subheader("All Students")
        c.execute("SELECT student_id,name,email,sex,profession,institution,mobile FROM students")
        st.dataframe(c.fetchall(),use_container_width=True)
    with tabs[1]:
        st.subheader("All Courses")
        c.execute("SELECT * FROM courses")
        st.dataframe(c.fetchall(),use_container_width=True)
    with tabs[2]:
        st.subheader("All Lessons")
        c.execute("""SELECT l.lesson_id, l.title, l.content_type, c.title 
                     FROM lessons l JOIN courses c ON c.course_id=l.course_id""")
        st.dataframe(c.fetchall(),use_container_width=True)

# ---------------------------
# Signup / Login
# ---------------------------
def signup_page():
    st.subheader("Create Student Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password",type="password")
        sex = st.radio("Sex",["Male","Female","Prefer not to say"])
        profession = st.selectbox("Profession",["Student","Working Professional"])
        institution = st.text_input("Institution (optional)")
        mobile = st.text_input("Mobile")
        submit = st.form_submit_button("Create Profile")
        if submit:
            try:
                c.execute("INSERT INTO students(name,email,password,sex,profession,institution,mobile) VALUES (?,?,?,?,?,?,?)",
                          (full_name,email,password,sex,profession,institution,mobile))
                conn.commit()
                st.success("Profile created! Please login.")
                st.experimental_rerun()
            except sqlite3.IntegrityError: st.error("Email exists. Try login.")

def login_page():
    st.subheader("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")
    if login_button:
        c.execute("SELECT student_id,name,password FROM students WHERE email=?", (email,))
        user = c.fetchone()
        if user and user[2]==password:
            st.session_state['student']={"id":user[0],"name":user[1],"email":email}
            st.experimental_rerun()
        else: st.error("Incorrect email/password")

def admin_login():
    st.subheader("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        if admin_pass=="EinTrustAdmin123":
            st.session_state['admin']=True
            st.experimental_rerun()
        else: st.error("Incorrect Password")

# ---------------------------
# Main Flow
# ---------------------------
if 'student' not in st.session_state and 'admin' not in st.session_state:
    choice = st.radio("Login as:",["Student","Admin"])
    if choice=="Student":
        option = st.radio("Option:",["Login","Signup"])
        if option=="Login": login_page()
        else: signup_page()
    else: admin_login()
elif 'student' in st.session_state: student_dashboard(st.session_state['student'])
elif 'admin' in st.session_state: admin_dashboard()

# ---------------------------
# Footer
# ---------------------------
st.markdown("<hr>",unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>© EinTrust 2025</p>",unsafe_allow_html=True)
