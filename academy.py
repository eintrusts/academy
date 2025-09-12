# ---------------------------
# Auto-install missing packages
# ---------------------------
import subprocess, sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from fpdf import FPDF
except ModuleNotFoundError:
    install("fpdf")
    from fpdf import FPDF

try:
    from PIL import Image
except ModuleNotFoundError:
    install("Pillow")
    from PIL import Image

# ---------------------------
# Core Imports
# ---------------------------
import streamlit as st
import sqlite3, os, datetime, uuid

# ---------------------------
# Database Setup
# ---------------------------
DB_FILE = "eintrust_academy.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# ---------------------------
# Tables Setup
# ---------------------------
def setup_db():
    c.execute("""CREATE TABLE IF NOT EXISTS students(
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        sex TEXT,
        profession TEXT,
        institution TEXT,
        mobile TEXT,
        pic TEXT,
        reset_token TEXT,
        reset_expiry TEXT
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
        content TEXT,
        content_type TEXT,
        file_path TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS quizzes(
        quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        amount REAL,
        status TEXT,
        transaction_id TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS certificates(
        cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        cert_file TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lesson_progress(
        student_id INTEGER,
        lesson_id INTEGER,
        viewed INTEGER DEFAULT 0,
        PRIMARY KEY(student_id, lesson_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz_progress(
        student_id INTEGER,
        quiz_id INTEGER,
        attempted INTEGER DEFAULT 0,
        correct INTEGER DEFAULT 0,
        PRIMARY KEY(student_id, quiz_id)
    )""")
    conn.commit()
setup_db()

# ---------------------------
# Session Defaults
# ---------------------------
if "user" not in st.session_state: st.session_state.user = None

# ---------------------------
# Dark Theme + Hover Buttons
# ---------------------------
st.markdown("""
<style>
body {background-color:#121212; color:#E0E0E0; font-family:Helvetica, Arial, sans-serif;}
input, button, select, textarea { background-color:#1A1A1A !important; color:#E0E0E0 !important; border:1px solid #333 !important; border-radius:6px; }
.stButton>button { background-color: #1E88E5; color:white; border-radius:8px; padding:0.6em 1.2em; font-weight:500; transition: transform 0.2s ease-in-out;}
.stButton>button:hover { background-color:#1565C0 !important; transform: scale(1.05); }
.card { background-color:#1A1A1A; padding:15px; margin-bottom:15px; border-radius:12px; box-shadow:0 4px 8px rgba(0,0,0,0.5); transition: transform 0.2s ease-in-out; }
.card:hover { transform: scale(1.02); }
.stDataFrame {background-color:#1A1A1A; color:#E0E0E0;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Logo + Footer
# ---------------------------
st.markdown("""
<div style="text-align:center; margin-bottom:30px;">
    <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="200"/>
    <h2 style="color:#E0E0E0; margin-top:15px;">EinTrust Academy</h2>
    <p style="color:#888; font-size:16px;">Engage • Enlighten • Empower</p>
</div>
""", unsafe_allow_html=True)

def footer():
    st.markdown("""
    <hr style="border-color:#333;">
    <div style="text-align:center; color:#888; font-size:12px; margin-top:10px;">
        © 2025 EinTrust. All Rights Reserved.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# Utilities
# ---------------------------
def inr_format(x): return f"₹ {int(x):,}"

def mark_lesson_viewed(student_id, lesson_id):
    c.execute("""INSERT OR REPLACE INTO lesson_progress(student_id, lesson_id, viewed) 
                 VALUES (?,?,?)""", (student_id, lesson_id, 1))
    conn.commit()

def mark_quiz_attempt(student_id, quiz_id, correct):
    c.execute("""INSERT OR REPLACE INTO quiz_progress(student_id, quiz_id, attempted, correct) VALUES(?,?,?,?)""",
              (student_id, quiz_id, 1, correct))
    conn.commit()

def generate_certificate(student_name, course_title, student_id, course_id):
    cert_folder = "certificates"
    os.makedirs(cert_folder, exist_ok=True)
    cert_file = f"{cert_folder}/Certificate_{student_id}_{course_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 80, "", ln=True)
    pdf.cell(0, 10, "Certificate of Completion", ln=True, align="C")
    pdf.set_font("Arial", "", 18)
    pdf.ln(20)
    pdf.multi_cell(0, 10, f"This is to certify that {student_name} has successfully completed the course '{course_title}'.", align="C")
    pdf.ln(20)
    pdf.cell(0, 10, f"Date: {datetime.date.today().strftime('%d-%m-%Y')}", ln=True, align="C")
    pdf.output(cert_file)
    c.execute("INSERT OR REPLACE INTO certificates (student_id, course_id, cert_file) VALUES (?,?,?)", (student_id, course_id, cert_file))
    conn.commit()
    return cert_file

# ---------------------------
# Signup/Login/Forgot Password
# ---------------------------
def signup():
    st.subheader("Create Student Profile")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Set Password", type="password")
        sex = st.selectbox("Sex", ["Male", "Female", "Prefer not to say"])
        profession = st.selectbox("Profession", ["Student", "Working Professional"])
        institution = st.text_input("Institution (Optional)")
        mobile = st.text_input("Mobile Number")
        pic = st.file_uploader("Profile Picture (Optional)", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Submit")
        if submitted:
            pic_path = ""
            if pic:
                os.makedirs("profile_pics", exist_ok=True)
                pic_path = f"profile_pics/{email}_{pic.name}"
                with open(pic_path, "wb") as f: f.write(pic.getbuffer())
            try:
                c.execute("INSERT INTO students(name,email,password,sex,profession,institution,mobile,pic,role) VALUES(?,?,?,?,?,?,?,?,?)",
                          (name,email,password,sex,profession,institution,mobile,pic_path,"student"))
                conn.commit()
                st.success("Profile created! Please login now.")
            except:
                st.error("Email already exists.")

def login():
    st.subheader("Student / Admin Login")
    with st.form("login_form"):
        email = st.text_input("Email ID / Admin")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Student", "Admin"])
        submitted = st.form_submit_button("Login")
        if submitted:
            if role=="Student":
                c.execute("SELECT * FROM students WHERE email=? AND password=?", (email,password))
                user = c.fetchone()
                if user:
                    st.session_state.user = {"id":user[0],"name":user[1],"email":user[2],"role":"student"}
                    st.success("Logged in successfully!")
                else: st.error("Incorrect Email/Password")
            else:
                if password=="admin123":
                    st.session_state.user = {"id":0,"name":"Admin","email":"admin@eintrusts.com","role":"admin"}
                    st.success("Admin logged in!")
                else: st.error("Incorrect Admin Password")

def forgot_password():
    st.subheader("Forgot Password")
    email = st.text_input("Enter registered Email ID")
    if st.button("Send Reset Link"):
        c.execute("SELECT student_id FROM students WHERE email=?", (email,))
        row = c.fetchone()
        if row:
            token = str(uuid.uuid4())
            expiry = (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE students SET reset_token=?, reset_expiry=? WHERE email=?", (token, expiry, email))
            conn.commit()
            reset_link = f"https://eintrustacademy.com/reset_password?token={token}"
            st.success(f"Reset link (simulated): {reset_link}")
        else: st.error("Email not found!")

# ---------------------------
# Student Dashboard
# ---------------------------
def student_dashboard(user):
    st.subheader(f"Welcome, {user['name']}")
    
    tabs = st.tabs(["All Courses", "My Courses", "Profile"])
    
    # ---------------------------
    # All Courses Tab
    # ---------------------------
    with tabs[0]:
        c.execute("SELECT * FROM courses")
        courses = c.fetchall()
        for course in courses:
            enrolled = c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=? AND status='Completed'",
                                 (user['id'], course[0])).fetchone()
            st.markdown(f"<div class='card'><h3>{course[1]}</h3><p>{course[2]}</p><b>Price: {inr_format(course[3])}</b></div>", unsafe_allow_html=True)
            
            if enrolled:
                st.success("✅ Already Enrolled")
            else:
                if course[3]==0:
                    if st.button(f"Enroll for Free", key=f"enroll_{course[0]}"):
                        c.execute("INSERT INTO payments(student_id,course_id,amount,status,transaction_id) VALUES(?,?,?,?,?)",
                                  (user['id'], course[0], 0, "Completed", str(uuid.uuid4())))
                        conn.commit()
                        st.success("Enrolled Successfully!")
                else:
                    if st.button(f"Pay & Enroll {inr_format(course[3])}", key=f"pay_{course[0]}"):
                        transaction_id = str(uuid.uuid4())
                        c.execute("INSERT INTO payments(student_id,course_id,amount,status,transaction_id) VALUES(?,?,?,?,?)",
                                  (user['id'], course[0], course[3], "Completed", transaction_id))
                        conn.commit()
                        st.success(f"Payment Successful! Transaction ID: {transaction_id}")
    
    # ---------------------------
    # My Courses Tab
    # ---------------------------
    with tabs[1]:
        c.execute("""SELECT c.course_id, c.title, c.description 
                     FROM courses c 
                     JOIN payments p ON c.course_id=p.course_id 
                     WHERE p.student_id=? AND p.status='Completed'""", (user['id'],))
        my_courses = c.fetchall()
        if not my_courses:
            st.info("No courses enrolled yet!")
        else:
            for course in my_courses:
                st.markdown(f"<div class='card'><h3>{course[1]}</h3><p>{course[2]}</p></div>", unsafe_allow_html=True)
                lessons = c.execute("SELECT * FROM lessons WHERE course_id=?", (course[0],)).fetchall()
                all_complete = True
                for lesson in lessons:
                    viewed = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?", (user['id'], lesson[0])).fetchone()
                    completed = viewed[0]==1 if viewed else False
                    col1, col2 = st.columns([6,1])
                    with col1: st.write(f"📖 {lesson[2]}")
                    with col2:
                        if not completed and st.button(f"Mark Complete ({lesson[2]})", key=f"lesson_{lesson[0]}"):
                            mark_lesson_viewed(user['id'], lesson[0])
                            st.success("Lesson marked complete!")
                            completed=True
                    if not completed: all_complete=False
                # Quizzes per lesson
                quizzes = []
                for lesson in lessons:
                    quizzes.extend(c.execute("SELECT * FROM quizzes WHERE lesson_id=?", (lesson[0],)).fetchall())
                for quiz in quizzes:
                    attempt = c.execute("SELECT attempted FROM quiz_progress WHERE student_id=? AND quiz_id=?", (user['id'], quiz[0])).fetchone()
                    attempted = attempt[0]==1 if attempt else False
                    if not attempted:
                        with st.expander(f"Attempt Quiz: {quiz[2]}"):
                            options = [quiz[3], quiz[4], quiz[5], quiz[6]]
                            ans = st.radio("Choose answer", options, key=f"quiz_{quiz[0]}")
                            if st.button("Submit Answer", key=f"submit_quiz_{quiz[0]}"):
                                correct = options.index(ans)+1 == quiz[7]
                                mark_quiz_attempt(user['id'], quiz[0], int(correct))
                                if correct: st.success("Correct Answer! ✅")
                                else: st.error(f"Wrong Answer! Correct is: {options[quiz[7]-1]}")
                                all_complete=False
                # Certificate generation
                if all_complete:
                    existing_cert = c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (user['id'], course[0])).fetchone()
                    if existing_cert:
                        st.success("🎓 Certificate already generated!")
                        st.download_button("Download Certificate", data=open(existing_cert[0], "rb").read(), file_name=os.path.basename(existing_cert[0]), mime="application/pdf")
                    else:
                        cert_file = generate_certificate(user['name'], course[1], user['id'], course[0])
                        st.success("🎓 Certificate generated!")
                        st.download_button("Download Certificate", data=open(cert_file, "rb").read(), file_name=os.path.basename(cert_file), mime="application/pdf")
    
    # ---------------------------
    # Profile Tab
    # ---------------------------
    with tabs[2]:
        c.execute("SELECT name,email,sex,profession,institution,mobile,pic FROM students WHERE student_id=?", (user['id'],))
        profile = c.fetchone()
        st.subheader("My Profile")
        col1, col2 = st.columns([3,7])
        with col1:
            if profile[6] and os.path.exists(profile[6]):
                st.image(profile[6], width=150)
        with col2:
            st.write(f"**Full Name:** {profile[0]}")
            st.write(f"**Email:** {profile[1]}")
            st.write(f"**Sex:** {profile[2]}")
            st.write(f"**Profession:** {profile[3]}")
            st.write(f"**Institution:** {profile[4]}")
            st.write(f"**Mobile:** {profile[5]}")

# ---------------------------
# Admin Dashboard
# ---------------------------
def admin_dashboard():
    st.subheader("Admin Dashboard")
    
    tabs = st.tabs(["Students", "Courses & Enrollments", "Lesson & Quiz Progress", "Certificates"])
    
    # Students
    with tabs[0]:
        st.markdown("### Registered Students")
        c.execute("SELECT student_id, name, email, sex, profession, institution, mobile FROM students")
        students = c.fetchall()
        if students:
            st.dataframe(students, use_container_width=True)
        else:
            st.info("No students registered yet.")
    
    # Courses & Enrollments
    with tabs[1]:
        st.markdown("### Course Enrollments & Payments")
        c.execute("""
        SELECT p.payment_id, s.name, c.title, p.amount, p.status, p.transaction_id
        FROM payments p
        JOIN students s ON p.student_id = s.student_id
        JOIN courses c ON p.course_id = c.course_id
        """)
        enrollments = c.fetchall()
        if enrollments:
            st.dataframe(enrollments, use_container_width=True)
        else:
            st.info("No enrollments yet.")
    
    # Lesson & Quiz Progress
    with tabs[2]:
        st.markdown("### Lesson Progress")
        c.execute("""
        SELECT s.name, l.title, lp.viewed
        FROM lesson_progress lp
        JOIN students s ON lp.student_id = s.student_id
        JOIN lessons l ON lp.lesson_id = l.lesson_id
        """)
        lesson_progress = c.fetchall()
        st.dataframe(lesson_progress, use_container_width=True)
        
        st.markdown("### Quiz Progress")
        c.execute("""
        SELECT s.name, q.question, qp.attempted, qp.correct
        FROM quiz_progress qp
        JOIN students s ON qp.student_id = s.student_id
        JOIN quizzes q ON qp.quiz_id = q.quiz_id
        """)
        quiz_progress = c.fetchall()
        st.dataframe(quiz_progress, use_container_width=True)
    
    # Certificates
    with tabs[3]:
        st.markdown("### Generated Certificates")
        c.execute("""
        SELECT s.name, c.title, cert_file
        FROM certificates cf
        JOIN students s ON cf.student_id = s.student_id
        JOIN courses c ON cf.course_id = c.course_id
        """)
        certs = c.fetchall()
        if certs:
            for cert in certs:
                st.write(f"Student: {cert[0]} | Course: {cert[1]}")
                if os.path.exists(cert[2]):
                    st.download_button("Download Certificate", data=open(cert[2], "rb").read(), file_name=os.path.basename(cert[2]), mime="application/pdf")
                else:
                    st.warning("Certificate file missing!")
        else:
            st.info("No certificates generated yet.")

# ---------------------------
# Main App
# ---------------------------
if not st.session_state.user:
    st.session_state.user = None
    st.subheader("Welcome to EinTrust Academy")
    st.write("Login or Create Profile to continue.")
    signup()
    login()
    forgot_password()
else:
    user = st.session_state.user
    if user["role"]=="student": student_dashboard(user)
    else: admin_dashboard()

footer()
