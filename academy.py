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
# Logo
# ---------------------------
st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png", width=200)

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
            mobile TEXT,
            pic TEXT
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
# Utility Functions
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
# Simulated Payment & Enrollment
# ---------------------------
def enroll_course(student_id, course_id, course_title, price):
    if price==0:
        st.success("Free course! You are enrolled automatically.")
    else:
        st.info(f"Paid course. Amount: {inr_format(price)}")
        if st.button(f"Simulate Payment for {course_title}"):
            st.success("Payment successful! You are now enrolled.")
    enroll_student_lessons(student_id, course_id)
    c.execute("INSERT OR IGNORE INTO payments(student_id,course_id,status) VALUES(?,?,?)",(student_id,course_id,'Success'))
    conn.commit()

# ---------------------------
# Signup Page
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
        profile_pic = st.file_uploader("Profile Picture (optional)",type=["png","jpg","jpeg"])
        submit = st.form_submit_button("Create Profile")
        if submit:
            pic_path=None
            if profile_pic:
                pic_path=f"profile_pics/{int(time.time())}_{profile_pic.name}"
                os.makedirs("profile_pics",exist_ok=True)
                with open(pic_path,"wb") as f: f.write(profile_pic.getbuffer())
            try:
                c.execute("INSERT INTO students(name,email,password,sex,profession,institution,mobile,pic) VALUES (?,?,?,?,?,?,?,?)",
                          (full_name,email,password,sex,profession,institution,mobile,pic_path))
                conn.commit()
                st.success("Profile created! Please login.")
                st.experimental_rerun()
            except sqlite3.IntegrityError: st.error("Email exists. Try login.")

# ---------------------------
# Student Login
# ---------------------------
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
    if st.button("Forgot Password?"):
        st.info("Simulated reset link. Enter new password below.")
        new_pass = st.text_input("New Password")
        if st.button("Reset Password"):
            c.execute("UPDATE students SET password=? WHERE email=?", (new_pass,email))
            conn.commit()
            st.success("Password reset! Login now.")

# ---------------------------
# Admin Login
# ---------------------------
def admin_login():
    st.subheader("Admin Login")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Enter"):
        if admin_pass=="eintrust2025":
            st.session_state['admin']=True
            st.experimental_rerun()
        else: st.error("Incorrect Password")

# ---------------------------
# Student Lessons
# ---------------------------
def student_lessons(user):
    st.subheader("My Lessons")
    c.execute("""SELECT l.lesson_id, l.title, l.course_id, l.content_type, l.content_path, c.title 
                 FROM lessons l JOIN payments p ON l.course_id=p.course_id 
                 JOIN courses c ON c.course_id=l.course_id
                 WHERE p.student_id=? AND p.status='Success'""",(user['id'],))
    lessons = c.fetchall()
    if lessons:
        for lesson in lessons:
            lesson_id,title,course_id,ctype,cpath,course_title = lesson
            st.markdown(f"<div class='card'><b>Course:</b> {course_title}<br><b>Lesson:</b> {title}</div>",unsafe_allow_html=True)
            if ctype=="video":
                st.video(cpath)
            elif ctype in ["pdf","ppt","text"]:
                st.download_button(f"Download {title}", cpath)
                st.info(f"Simulate reading {ctype.upper()} to mark complete")
            viewed = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?",(user['id'],lesson_id)).fetchone()[0]
            if viewed: st.success("Completed ✅")
            else:
                if st.button(f"Mark as Complete", key=f"lesson_{lesson_id}"):
                    mark_lesson_viewed(user['id'], lesson_id)
                    st.success("Marked complete!")
                    c.execute("SELECT COUNT(*) FROM lesson_progress lp JOIN lessons l ON lp.lesson_id=l.lesson_id WHERE lp.student_id=? AND l.course_id=? AND lp.viewed=0",(user['id'],course_id))
                    remaining = c.fetchone()[0]
                    if remaining==0:
                        cert_file = generate_certificate(user['name'], course_title, user['id'], course_id)
                        c.execute("INSERT OR REPLACE INTO certificates(student_id,course_id,cert_file) VALUES(?,?,?)",(user['id'],course_id,cert_file))
                        conn.commit()
                        st.balloons()
                        st.success(f"All lessons completed! Certificate generated: {cert_file}")
    else: st.info("Enroll in courses to see lessons.")

# ---------------------------
# Student Dashboard
# ---------------------------
def student_dashboard(user):
    st.subheader(f"Welcome, {user['name']}!")
    tabs = st.tabs(["My Profile","Courses","My Lessons","My Progress","Certificates"])
    # Profile Tab
    with tabs[0]: 
        st.markdown("### Your Profile")
        c.execute("SELECT name,email,sex,profession,institution,mobile,pic FROM students WHERE student_id=?",(user['id'],))
        profile = c.fetchone()
        if profile:
            col1,col2=st.columns([3,7])
            with col1:
                if profile[6] and os.path.exists(profile[6]): st.image(profile[6], width=150)
            with col2:
                st.write(f"**Full Name:** {profile[0]}")
                st.write(f"**Email:** {profile[1]}")
                st.write(f"**Sex:** {profile[2]}")
                st.write(f"**Profession:** {profile[3]}")
                st.write(f"**Institution:** {profile[4]}")
                st.write(f"**Mobile:** {profile[5]}")
    # Courses Tab
    with tabs[1]:
        st.markdown("### Available Courses")
        c.execute("SELECT course_id,title,description,price FROM courses")
        courses = c.fetchall()
        for course in courses:
            st.markdown(f"<div class='card'><h3>{course[1]}</h3><p>{course[2]}</p><b>Price: {inr_format(course[3])}</b></div>",unsafe_allow_html=True)
            enrolled=c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=? AND status='Success'",(user['id'],course[0])).fetchone()
            if enrolled: st.success("Enrolled ✅")
            else:
                if st.button(f"Enroll in {course[1]}",key=f"enroll_{course[0]}"):
                    enroll_course(user['id'], course[0], course[1], course[3])
    # Lessons Tab
    with tabs[2]: student_lessons(user)
    # Progress Tab
    with tabs[3]:
        st.subheader("Course Progress")
        c.execute("""SELECT c.title, COUNT(l.lesson_id) as total, SUM(lp.viewed) as completed
                     FROM lessons l JOIN courses c ON l.course_id=c.course_id
                     JOIN lesson_progress lp ON l.lesson_id=lp.lesson_id
                     WHERE lp.student_id=?
                     GROUP BY c.course_id""",(user['id'],))
        data = c.fetchall()
        if data: st.dataframe([{"Course":d[0],"Total Lessons":d[1],"Completed Lessons":d[2]} for d in data])
        else: st.info("No lessons tracked yet.")
    # Certificates Tab
    with tabs[4]:
        st.subheader("Certificates")
        c.execute("SELECT c.course_id, co.title, c.cert_file FROM certificates c JOIN courses co ON c.course_id=co.course_id WHERE c.student_id=?",(user['id'],))
        certs = c.fetchall()
        if certs:
            for cert in certs:
                st.markdown(f"<div class='card'><b>Course:</b> {cert[1]}</div>",unsafe_allow_html=True)
                st.download_button("Download Certificate", cert[2])
        else: st.info("Complete lessons to get certificates.")

# ---------------------------
# Admin Dashboard
# ---------------------------
def admin_dashboard():
    st.subheader("Admin Dashboard")
    st.info("All student data (without passwords)")
    c.execute("SELECT student_id,name,email,sex,profession,institution,mobile FROM students")
    st.dataframe(c.fetchall(),use_container_width=True)

# ---------------------------
# Main App Flow
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
