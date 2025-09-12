import streamlit as st
import sqlite3
import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd
import uuid
import random

# ---------------------------
# Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
CERT_FOLDER = "certificates"
os.makedirs(CERT_FOLDER, exist_ok=True)
DB_FILE = "eintrust_academy.db"
PASS_MARK = 70  # Quiz pass percentage

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# ---------------------------
# Create Tables if Not Exists
# ---------------------------
c.execute("""CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, email TEXT UNIQUE, password TEXT, role TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, description TEXT, price REAL)""")
c.execute("""CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER, title TEXT, content_type TEXT, content_path TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id))""")
c.execute("""CREATE TABLE IF NOT EXISTS progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER, course_id INTEGER, lesson_id INTEGER, completed INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id))""")
c.execute("""CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER, question TEXT, option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT, answer TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id))""")
c.execute("""CREATE TABLE IF NOT EXISTS certificates (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER, course_id INTEGER, cert_file TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id))""")
c.execute("""CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER, course_id INTEGER, amount REAL, status TEXT, transaction_id TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id))""")
conn.commit()

# ---------------------------
# Session Defaults
# ---------------------------
if "user" not in st.session_state: st.session_state.user = None
if "current_course" not in st.session_state: st.session_state.current_course = None

# ---------------------------
# Dark Theme & Professional Fonts
# ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
* { font-family: 'Roboto', sans-serif; }

/* Dark Background & Text */
body, .main, .block-container { background-color: #121212 !important; color: #E0E0E0 !important; }
h1,h2,h3,h4,h5,h6 { color: #ffffff !important; }

/* Buttons */
.stButton>button { background-color: #1E88E5; color: white; border-radius: 8px; padding: 0.5em 1em; border: none; font-weight:500; }
.stButton>button:hover { background-color: #1565C0 !important; transform: scale(1.03); transition: all 0.2s ease-in-out; }

/* Inputs */
.stTextInput>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div>span { background-color:#1A1A1A !important; color:#E0E0E0 !important; border:1px solid #333 !important; border-radius:6px; }

/* Tables */
.stDataFrame th { background-color: #1E1E1E !important; color:#ffffff !important; }
.stDataFrame td { background-color: #1A1A1A !important; color:#E0E0E0 !important; }

/* Course & Lesson Cards Hover */
.course-card { background-color:#1A1A1A; border:1px solid #333; border-radius:8px; padding:15px; margin-bottom:15px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.course-card:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
.lesson-card { background-color:#1E1E1E; border-left:4px solid #1E88E5; padding:12px; margin-bottom:10px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.lesson-card:hover { transform: translateX(5px); box-shadow:0 2px 10px rgba(0,0,0,0.3); }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def inr_format(number):
    if number is None: return "₹ 0"
    return "₹ {:,}".format(int(number)).replace(",", ",")

def page_header():
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:20px;">
            <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="200"/>
        </div>
    """, unsafe_allow_html=True)

def page_footer():
    st.markdown("""
        <hr style="border-color:#333;">
        <div style="text-align:center; color:#888; font-size:12px; margin-top:10px;">
            © 2025 EinTrust. All Rights Reserved.
        </div>
    """, unsafe_allow_html=True)

def generate_certificate(student_name, course_name):
    template = Image.new("RGB", (1200,800), color=(255,255,255))
    draw = ImageDraw.Draw(template)
    font = ImageFont.truetype("arial.ttf",50)
    draw.text((300,300),"Certificate of Completion", fill="black", font=font)
    draw.text((300,400),f"Presented to: {student_name}", fill="black", font=font)
    draw.text((300,500),f"For completing: {course_name}", fill="black", font=font)
    draw.text((300,600),f"Date: {datetime.date.today().strftime('%d-%m-%Y')}", fill="black", font=font)
    filename = os.path.join(CERT_FOLDER,f"{student_name}_{course_name}.png")
    template.save(filename)
    return filename

def calculate_progress(student_id, course_id):
    c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM progress WHERE student_id=? AND course_id=? AND completed=1", (student_id, course_id))
    completed = c.fetchone()[0]
    return int((completed/total)*100) if total else 0

def course_timeline(course_id):
    st.subheader("Course Timeline")
    c.execute("SELECT lesson_id, title FROM lessons WHERE course_id=? ORDER BY lesson_id", (course_id,))
    lessons = c.fetchall()
    student_id = st.session_state.user["id"]
    c.execute("SELECT lesson_id FROM progress WHERE student_id=? AND course_id=? AND completed=1", (student_id, course_id))
    completed_lessons = [x[0] for x in c.fetchall()]
    next_lesson_found=False
    for lesson in lessons:
        lid,title=lesson
        if lid in completed_lessons:
            st.markdown(f"<div class='lesson-card'>✅ {title} (Completed)</div>", unsafe_allow_html=True)
        elif not next_lesson_found:
            st.markdown(f"<div class='lesson-card'>⏳ {title} (Next)</div>", unsafe_allow_html=True)
            next_lesson_found=True
            c.execute("SELECT content_type, content_path FROM lessons WHERE lesson_id=?", (lid,))
            content_type, content_path = c.fetchone()
            if content_type=="text":
                with open(content_path,"r") as f: st.write(f.read())
            elif content_type=="video":
                st.video(content_path)
            elif content_type=="pdf":
                st.download_button("Download PDF", open(content_path,"rb").read(), file_name=content_path.split("/")[-1], use_container_width=True)
            if st.button(f"Mark '{title}' as Completed", use_container_width=True):
                c.execute("INSERT OR REPLACE INTO progress (student_id, course_id, lesson_id, completed) VALUES (?,?,?,1)", (student_id, course_id, lid))
                conn.commit()
                st.success(f"Lesson '{title}' marked as completed!")
                st.experimental_rerun()
        else:
            st.markdown(f"<div class='lesson-card'>🔒 {title} (Locked)</div>", unsafe_allow_html=True)

# ---------------------------
# Student Quiz & Certificate
# ---------------------------
def student_quiz_tab():
    st.subheader("Course Quizzes")
    student_id=st.session_state.user["id"]
    c.execute("SELECT course_id, title FROM courses WHERE course_id IN (SELECT course_id FROM payments WHERE student_id=? AND status='paid')", (student_id,))
    enrolled_courses=c.fetchall()
    if not enrolled_courses:
        st.info("You have no enrolled courses with quizzes.")
        return
    for course in enrolled_courses:
        course_id,course_title=course
        st.markdown(f"### {course_title}")
        c.execute("SELECT quiz_id, question, option1, option2, option3, option4, answer FROM quizzes WHERE course_id=?", (course_id,))
        quizzes=c.fetchall()
        if not quizzes:
            st.write("No quizzes available for this course yet.")
            continue
        score=0
        for q in quizzes:
            quiz_id,question,opt1,opt2,opt3,opt4,answer=q
            user_answer=st.radio(question,[opt1,opt2,opt3,opt4], key=f"quiz_{quiz_id}")
            if user_answer==answer:
                score+=1
        if st.button(f"Submit Quiz for {course_title}", use_container_width=True):
            total=len(quizzes)
            percentage=(score/total)*100
            st.write(f"Your Score: {score}/{total} ({percentage:.2f}%)")
            if percentage>=PASS_MARK:
                st.success("Congratulations! You passed the course.")
                c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (student_id, course_id))
                existing=c.fetchone()
                if existing:
                    st.info("Certificate already generated.")
                    st.download_button("Download Certificate", open(existing[0],"rb").read(), file_name=existing[0].split("/")[-1], use_container_width=True)
                else:
                    cert_file=generate_certificate(st.session_state.user["name"], course_title)
                    c.execute("INSERT INTO certificates (student_id, course_id, cert_file) VALUES (?,?,?)", (student_id, course_id, cert_file))
                    conn.commit()
                    st.success("Certificate generated automatically!")
                    st.download_button("Download Certificate", open(cert_file,"rb").read(), file_name=cert_file.split("/")[-1], use_container_width=True)
            else:
                st.warning(f"Score below passing mark ({PASS_MARK}%). Please try again.")

# ---------------------------
# Student Dashboard Tabs
# ---------------------------
def student_dashboard():
    st.subheader("My Progress Dashboard")
    student_id=st.session_state.user["id"]
    c.execute("SELECT course_id FROM payments WHERE student_id=? AND status='paid'", (student_id,))
    enrolled_courses=[x[0] for x in c.fetchall()]
    if enrolled_courses:
        for cid in enrolled_courses:
            c.execute("SELECT title, price FROM courses WHERE course_id=?", (cid,))
            title,price=c.fetchone()
            progress=calculate_progress(student_id, cid)
            st.markdown(f"**{title}** - Fee: {inr_format(price)}")
            st.progress(progress)
    else:
        st.info("You are not enrolled in any courses yet.")

def student_tabs():
    tabs=st.tabs(["Course Catalog","Timeline Lessons","Quiz","Certificate","Dashboard"])
    with tabs[0]:
        st.subheader("Course Catalog")
        df_courses=pd.read_sql("SELECT * FROM courses", conn)
        df_courses['price']=df_courses['price'].apply(inr_format)
        for index,row in df_courses.iterrows():
            st.markdown(f"""
                <div class="course-card">
                    <h3>{row['title']}</h3>
                    <p>Fee: {row['price']}</p>
                </div>
            """, unsafe_allow_html=True)
            student_id=st.session_state.user["id"]
            c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=?", (student_id, row['course_id']))
            if not c.fetchone():
                if st.button(f"Buy {row['title']}", key=f"buy_{row['course_id']}", use_container_width=True):
                    order_id=str(uuid.uuid4())[:8].upper()
                    st.info(f"Payment Order Created: {order_id} for {row['price']}")
                    outcome=st.selectbox("Select Payment Outcome (for testing):", ["Success","Pending","Failed"], key=f"outcome_{row['course_id']}")
                    if st.button("Pay Now", key=f"paynow_{row['course_id']}", use_container_width=True):
                        txn_id=f"TXN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                        if outcome=="Success": status="paid"; st.success(f"Payment successful! Transaction ID: {txn_id}")
                        elif outcome=="Pending": status="pending"; st.warning(f"Payment pending. Transaction ID: {txn_id}. Retry later.")
                        else: status="failed"; st.error(f"Payment failed. Transaction ID: {txn_id}. Try again.")
                        c.execute("INSERT INTO payments (student_id, course_id, amount, status, transaction_id) VALUES (?,?,?,?,?)", (student_id, row['course_id'], row['price'], status, txn_id))
                        conn.commit(); st.experimental_rerun()
    with tabs[1]:
        c.execute("SELECT course_id, title FROM courses WHERE course_id IN (SELECT course_id FROM payments WHERE student_id=? AND status='paid')", (st.session_state.user["id"],))
        enrolled_courses=c.fetchall()
        if enrolled_courses:
            for course_id, course_title in enrolled_courses:
                st.markdown(f"### {course_title}")
                course_timeline(course_id)
        else: st.info("No enrolled courses to show timeline.")
    with tabs[2]:
        student_quiz_tab()
    with tabs[3]:
        st.subheader("My Certificates")
        student_id=st.session_state.user["id"]
        c.execute("SELECT course_id, cert_file FROM certificates WHERE student_id=?", (student_id,))
        certs=c.fetchall()
        if certs:
            for course_id, cert_file in certs:
                c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,))
                title=c.fetchone()[0]
                st.markdown(f"**{title}**")
                st.download_button("Download Certificate", open(cert_file,"rb").read(), file_name=cert_file.split("/")[-1], use_container_width=True)
        else: st.info("No certificates available yet.")
    with tabs[4]:
        student_dashboard()

# ---------------------------
# Admin Tabs
# ---------------------------
def admin_tabs():
    tabs=st.tabs(["Dashboard","Students","Courses","Payments","Revenue Chart"])
    with tabs[0]:
        st.subheader("Admin Dashboard")
        c.execute("SELECT COUNT(*) FROM students"); total_students=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM courses"); total_courses=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM payments WHERE status='paid'"); total_enrollments=c.fetchone()[0]
        c.execute("SELECT SUM(amount) FROM payments WHERE status='paid'"); total_revenue=c.fetchone()[0] or 0
        col1,col2,col3,col4=st.columns(4)
        col1.metric("Total Students", total_students)
        col2.metric("Total Courses", total_courses)
        col3.metric("Paid Enrollments", total_enrollments)
        col4.metric("Revenue", inr_format(total_revenue))
    with tabs[1]:
        st.subheader("All Registered Students")
        c.execute("SELECT student_id, name, email, role FROM students")
        df=pd.DataFrame(c.fetchall(), columns=["ID","Name","Email","Role"])
        st.dataframe(df)
    with tabs[2]:
        st.subheader("All Courses")
        c.execute("SELECT course_id,title,description,price FROM courses")
        df=pd.DataFrame(c.fetchall(), columns=["ID","Title","Description","Price"])
        df["Price"]=df["Price"].apply(inr_format)
        st.dataframe(df)
    with tabs[3]:
        st.subheader("Payments")
        c.execute("SELECT student_id, course_id, amount, status, transaction_id FROM payments")
        df=pd.DataFrame(c.fetchall(), columns=["Student ID","Course ID","Amount","Status","Transaction ID"])
        df["Amount"]=df["Amount"].apply(inr_format)
        st.dataframe(df)
    with tabs[4]:
        st.subheader("Revenue Chart")
        c.execute("SELECT title, SUM(amount) FROM courses LEFT JOIN payments ON courses.course_id=payments.course_id WHERE status='paid' GROUP BY courses.course_id")
        data=c.fetchall()
        if data:
            df=pd.DataFrame(data, columns=["Course","Revenue"])
            df["Revenue"]=df["Revenue"].apply(lambda x: x or 0)
            st.bar_chart(df.set_index("Course"))
        else: st.info("No revenue data yet.")

# ---------------------------
# Login / Signup
# ---------------------------
def login_signup():
    st.subheader("Login")
    email=st.text_input("Email")
    password=st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT student_id,name,email,role FROM students WHERE email=? AND password=?", (email,password))
        user=c.fetchone()
        if user:
            st.session_state.user={"id":user[0],"name":user[1],"email":user[2],"role":user[3]}
            st.success(f"Welcome, {user[1]}!")
            st.experimental_rerun()
        else: st.error("Invalid credentials.")
    st.subheader("Sign Up")
    name=st.text_input("Full Name")
    email_su=st.text_input("Email for Signup")
    password_su=st.text_input("Password for Signup", type="password")
    if st.button("Sign Up"):
        role="student"
        try:
            c.execute("INSERT INTO students (name,email,password,role) VALUES (?,?,?,?)", (name,email_su,password_su,role))
            conn.commit()
            st.success("Signup successful! Please login now.")
        except:
            st.error("Email already registered.")

# ---------------------------
# Main App
# ---------------------------
page_header()
if not st.session_state.user:
    login_signup()
else:
    if st.session_state.user["role"]=="admin":
        admin_tabs()
    else:
        student_tabs()
page_footer()
