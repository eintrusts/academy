import streamlit as st
import sqlite3
import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import smtplib
from email.message import EmailMessage

# ---------------------------
# Config
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
CERT_FOLDER = "certificates"
os.makedirs(CERT_FOLDER, exist_ok=True)
DB_FILE = "eintrust_academy.db"

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute("""CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'student'
)""")

c.execute("""CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    price REAL,
    total_lessons INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY,
    course_id INTEGER,
    title TEXT,
    content_type TEXT,
    content_path TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    lesson_id INTEGER,
    completed BOOLEAN
)""")

c.execute("""CREATE TABLE IF NOT EXISTS quiz_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    score REAL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    amount REAL,
    status TEXT,
    transaction_id TEXT
)""")
conn.commit()

# ---------------------------
# Session State Defaults
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "current_course" not in st.session_state:
    st.session_state.current_course = None

# ---------------------------
# Helper Functions
# ---------------------------
def generate_certificate(student_name, course_name):
    template = Image.new("RGB", (1200, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(template)
    font = ImageFont.truetype("arial.ttf", 50)
    draw.text((300, 300), "Certificate of Completion", fill="black", font=font)
    draw.text((300, 400), f"Presented to: {student_name}", fill="black", font=font)
    draw.text((300, 500), f"For completing: {course_name}", fill="black", font=font)
    draw.text((300, 600), f"Date: {datetime.date.today().strftime('%d-%m-%Y')}", fill="black", font=font)
    filename = os.path.join(CERT_FOLDER, f"{student_name}_{course_name}.png")
    template.save(filename)
    return filename

def send_certificate_email(student_email, certificate_path):
    msg = EmailMessage()
    msg['Subject'] = "Your EinTrust Academy Certificate"
    msg['From'] = "academy@eintrust.org"  # replace with your email
    msg['To'] = student_email
    msg.set_content("Congratulations! Find your certificate attached.")
    with open(certificate_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename="certificate.png")
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login("your_email@gmail.com", "app_password")  # replace with credentials
        server.send_message(msg)

def calculate_progress(student_id, course_id):
    c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,))
    total_lessons = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM progress WHERE student_id=? AND course_id=? AND completed=1", (student_id, course_id))
    completed = c.fetchone()[0]
    if total_lessons == 0:
        return 0
    return int((completed/total_lessons)*100)

# ---------------------------
# Pages
# ---------------------------
def login_signup():
    st.title("EinTrust Academy Login / Signup")
    with st.form("login_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["student", "admin"])
        submitted = st.form_submit_button("Signup / Login")
        if submitted:
            c.execute("SELECT * FROM students WHERE email=? AND password=?", (email,password))
            user = c.fetchone()
            if user:
                st.session_state.user = {"id": user[0], "name": user[1], "email": user[2], "role": user[4]}
                st.success(f"Welcome {user[1]}!")
            else:
                try:
                    c.execute("INSERT INTO students (name,email,password,role) VALUES (?,?,?,?)",
                              (name,email,password,role))
                    conn.commit()
                    st.success("Signup successful! Please login again.")
                except sqlite3.IntegrityError:
                    st.error("Email already registered. Try logging in.")

def course_catalog():
    st.title("Course Catalog")
    c.execute("SELECT * FROM courses")
    course_list = c.fetchall()
    for course in course_list:
        st.subheader(course[1])
        st.write(course[2])
        st.write(f"Lessons: {course[4]} | Price: ₹{course[3]}")
        progress = calculate_progress(st.session_state.user["id"], course[0])
        st.progress(progress)
        c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=? AND status='paid'", 
                  (st.session_state.user["id"], course[0]))
        payment_done = c.fetchone()
        if payment_done or course[3]==0:
            if st.button(f"Access {course[1]}", key=f"access_{course[0]}"):
                st.session_state.current_course = course[0]
                st.session_state.page = "Course"
        else:
            if st.button(f"Enroll / Pay ₹{course[3]}", key=f"pay_{course[0]}"):
                c.execute("INSERT INTO payments (student_id,course_id,amount,status,transaction_id) VALUES (?,?,?,?,?)", 
                          (st.session_state.user["id"], course[0], course[3], "paid", "TXN123456"))
                conn.commit()
                st.success("Payment successful! Access your course now.")

def course_page():
    course_id = st.session_state.current_course
    c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,))
    course = c.fetchone()
    st.title(course[1])
    
    c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
    lessons_list = c.fetchall()
    
    for lesson in lessons_list:
        st.subheader(lesson[2])
        if lesson[3]=="text":
            st.write(lesson[4])
        elif lesson[3]=="video":
            st.video(lesson[4])
        elif lesson[3]=="pdf":
            st.download_button("Download PDF", lesson[4])
        # Mark complete
        c.execute("SELECT * FROM progress WHERE student_id=? AND course_id=? AND lesson_id=?", 
                  (st.session_state.user["id"], course_id, lesson[0]))
        done = c.fetchone()
        if done:
            st.success("Completed ✅")
        else:
            if st.button(f"Mark '{lesson[2]}' Complete", key=f"complete_{lesson[0]}"):
                c.execute("INSERT INTO progress (student_id,course_id,lesson_id,completed) VALUES (?,?,?,?)",
                          (st.session_state.user["id"], course_id, lesson[0], 1))
                conn.commit()
                st.experimental_rerun()
    
    st.progress(calculate_progress(st.session_state.user["id"], course_id))
    if calculate_progress(st.session_state.user["id"], course_id)==100:
        if st.button("Take Quiz"):
            st.session_state.page = "Quiz"

def quiz_page():
    course_id = st.session_state.current_course
    st.title("Course Quiz")
    questions = [
        {"q":"What is sustainability?", "options":["Option A","Option B","Option C"], "answer":"Option A"},
        {"q":"Which is NOT sustainable?", "options":["Reduce","Waste","Recycle"], "answer":"Waste"}
    ]
    score = 0
    for i,q in enumerate(questions):
        ans = st.radio(q["q"], q["options"], key=f"q{i}")
        if st.button(f"Submit Q{i}", key=f"submit_{i}"):
            if ans==q["answer"]:
                st.success("Correct ✅")
                score+=1
            else:
                st.error(f"Wrong ❌. Correct: {q['answer']}")
    c.execute("INSERT INTO quiz_scores (student_id,course_id,score) VALUES (?,?,?)",
              (st.session_state.user["id"], course_id, score))
    conn.commit()
    st.write(f"Your score: {score}/{len(questions)}")
    if score >= len(questions)*0.7:
        st.success("Passed! Certificate unlocked.")
        cert_file = generate_certificate(st.session_state.user["name"], c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,)).fetchone()[0])
        st.image(cert_file)
        st.download_button("Download Certificate", cert_file, file_name=os.path.basename(cert_file))
        # send_certificate_email(st.session_state.user["email"], cert_file)
    else:
        st.warning("You need at least 70% to pass.")

# ---------------------------
# Admin Panel
# ---------------------------
def admin_panel():
    st.title("Admin Panel")
    menu = ["Courses","Lessons","Students","Payments"]
    choice = st.sidebar.selectbox("Select Section", menu)
    
    if choice=="Courses":
        st.subheader("Manage Courses")
        c.execute("SELECT * FROM courses")
        courses_list = c.fetchall()
        for course in courses_list:
            st.write(f"{course[0]} | {course[1]} | ₹{course[3]}")
            if st.button(f"Delete {course[1]}", key=f"del_course_{course[0]}"):
                c.execute("DELETE FROM courses WHERE course_id=?", (course[0],))
                conn.commit()
                st.success(f"Deleted {course[1]}")
        st.markdown("---")
        st.subheader("Add Course")
        title = st.text_input("Course Title", key="add_course_title")
        desc = st.text_area("Description")
        price = st.number_input("Price", min_value=0)
        total_lessons = st.number_input("Total Lessons", min_value=1)
        if st.button("Add Course"):
            c.execute("INSERT INTO courses (title,description,price,total_lessons) VALUES (?,?,?,?)", (title,desc,price,total_lessons))
            conn.commit()
            st.success("Course added")

    elif choice=="Lessons":
        st.subheader("Manage Lessons")
        c.execute("SELECT * FROM courses")
        courses_list = c.fetchall()
        course_name = st.selectbox("Select Course", [c[1] for c in courses_list])
        course_id = [c[0] for c in courses_list if c[1]==course_name][0]
        c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,))
        lessons_list = c.fetchall()
        for lesson in lessons_list:
            st.write(f"{lesson[0]} | {lesson[2]} | {lesson[3]}")
            if st.button(f"Delete {lesson[2]}", key=f"del_lesson_{lesson[0]}"):
                c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson[0],))
                conn.commit()
                st.success(f"Deleted {lesson[2]}")
        st.markdown("---")
        st.subheader("Add Lesson")
        l_title = st.text_input("Lesson Title", key="add_lesson_title")
        l_type = st.selectbox("Content Type", ["text","video","pdf"])
        l_content = st.text_area("Content / URL / Path")
        if st.button("Add Lesson"):
            c.execute("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)",
                      (course_id,l_title,l_type,l_content))
            conn.commit()
            st.success("Lesson added")

    elif choice=="Students":
        st.subheader("Students")
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        for s in students:
            st.write(f"{s[0]} | {s[1]} | {s[2]} | Role: {s[4]}")

    elif choice=="Payments":
        st.subheader("Payments")
        c.execute("SELECT p.payment_id,s.name,c.title,p.amount,p.status FROM payments p "
                  "JOIN students s ON p.student_id=s.student_id "
                  "JOIN courses c ON p.course_id=c.course_id")
        payments = c.fetchall()
        for p in payments:
            st.write(f"{p[0]} | {p[1]} | {p[2]} | ₹{p[3]} | {p[4]}")

# ---------------------------
# Main App
# ---------------------------
if st.session_state.user is None:
    login_signup()
else:
    if st.session_state.user["role"]=="admin":
        admin_panel()
    else:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to:", ["Course Catalog","Course","Quiz"])
        st.session_state.page = page
        if page=="Course Catalog":
            course_catalog()
        elif page=="Course":
            if st.session_state.current_course:
                course_page()
            else:
                st.write("Select a course from catalog first.")
        elif page=="Quiz":
            if st.session_state.current_course:
                quiz_page()
            else:
                st.write("Complete lessons first to access quiz.")
