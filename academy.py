# EinTrust Academy - Full Functional Streamlit App
import streamlit as st
import sqlite3, os, datetime, uuid
from fpdf import FPDF
from PIL import Image
import streamlit.components.v1 as components

# ---------------------------
# Database Setup
# ---------------------------
DB_FILE = "eintrust_academy.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# ---------------------------
# Tables
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
if "current_course" not in st.session_state: st.session_state.current_course = None

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
    c.execute("""INSERT OR REPLACE INTO quiz_progress(student_id, quiz_id, attempted, correct) VALUES (?,?,?,?)""",
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
# Main Navigation
# ---------------------------
if st.session_state.user is None:
    choice = st.radio("Navigation", ["Login", "Signup", "Forgot Password"])
    if choice=="Login": login()
    elif choice=="Signup": signup()
    else: forgot_password()

# ---------------------------
# Footer
# ---------------------------
footer()
