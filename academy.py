import streamlit as st
import sqlite3
import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import pandas as pd

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
# Session Defaults
# ---------------------------
if "user" not in st.session_state: st.session_state.user = None
if "current_course" not in st.session_state: st.session_state.current_course = None

# ---------------------------
# Indian Number Format Helper
# ---------------------------
def inr_format(number):
    if number is None: return "₹ 0"
    return "₹ {:,}".format(int(number)).replace(",", ",")

# ---------------------------
# Sidebar Branding
# ---------------------------
with st.sidebar:
    st.markdown(
        f'<div style="text-align:center;"><img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true" width="150"/></div>',
        unsafe_allow_html=True
    )
    st.write("---")
    st.write("© 2025 EinTrust")

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

def calculate_progress(student_id, course_id):
    c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM progress WHERE student_id=? AND course_id=? AND completed=1", (student_id, course_id))
    completed = c.fetchone()[0]
    return int((completed/total)*100) if total else 0

# ---------------------------
# Admin Tabs
# ---------------------------
def admin_tabs():
    tabs = st.tabs(["Dashboard","Courses","Lessons","Quizzes","Students","Payments","Revenue Chart"])
    
    # Dashboard
    with tabs[0]:
        st.subheader("Admin Dashboard")
        c.execute("SELECT COUNT(*) FROM students"); total_students=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM courses"); total_courses=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM payments WHERE status='paid'"); total_enrollments=c.fetchone()[0]
        c.execute("SELECT SUM(amount) FROM payments WHERE status='paid'"); total_revenue=c.fetchone()[0] or 0
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Total Students", total_students)
        col2.metric("Total Courses", total_courses)
        col3.metric("Paid Enrollments", total_enrollments)
        col4.metric("Revenue", inr_format(total_revenue))
    
    # Courses
    with tabs[1]:
        st.subheader("Courses")
        df_courses = pd.read_sql("SELECT * FROM courses", conn)
        search_course = st.text_input("Search Course")
        if search_course: df_courses = df_courses[df_courses['title'].str.contains(search_course, case=False)]
        df_courses['price'] = df_courses['price'].apply(inr_format)
        st.dataframe(df_courses)
    
    # Lessons
    with tabs[2]:
        st.subheader("Lessons")
        df_lessons = pd.read_sql("SELECT l.lesson_id, c.title as course, l.title, l.content_type, l.content_path FROM lessons l JOIN courses c ON l.course_id=c.course_id", conn)
        st.dataframe(df_lessons)
    
    # Quizzes
    with tabs[3]:
        st.subheader("Quizzes")
        df_quiz = pd.read_sql("SELECT q.quiz_id, c.title as course, q.question, q.option1, q.option2, q.option3, q.option4, q.answer FROM quizzes q JOIN courses c ON q.course_id=c.course_id", conn)
        st.dataframe(df_quiz)
    
    # Students
    with tabs[4]:
        st.subheader("Students")
        df_students = pd.read_sql("SELECT * FROM students", conn)
        search_student = st.text_input("Search Student")
        if search_student: df_students = df_students[df_students['name'].str.contains(search_student, case=False) | df_students['email'].str.contains(search_student, case=False)]
        st.dataframe(df_students)
    
    # Payments
    with tabs[5]:
        st.subheader("Payments (Test Mode)")
        df_payments = pd.read_sql("""SELECT p.payment_id, s.name as student, c.title as course, p.amount, p.status, p.transaction_id 
                                     FROM payments p 
                                     JOIN students s ON p.student_id=s.student_id 
                                     JOIN courses c ON p.course_id=c.course_id""", conn)
        df_payments['amount'] = df_payments['amount'].apply(inr_format)
        st.dataframe(df_payments)
    
    # Revenue Chart
    with tabs[6]:
        st.subheader("Revenue Analysis")
        df_revenue = pd.read_sql("""SELECT c.title as course, SUM(p.amount) as total_revenue 
                                    FROM payments p JOIN courses c ON p.course_id=c.course_id 
                                    WHERE p.status='paid' GROUP BY c.title""", conn)
        if not df_revenue.empty:
            st.bar_chart(df_revenue.set_index("course")["total_revenue"])

# ---------------------------
# Student Dashboard / Tabs
# ---------------------------
def student_dashboard():
    st.subheader("My Progress Dashboard")
    c.execute("SELECT course_id FROM payments WHERE student_id=? AND status='paid'", (st.session_state.user["id"],))
    enrolled_courses = [x[0] for x in c.fetchall()]
    if enrolled_courses:
        for cid in enrolled_courses:
            c.execute("SELECT title, price FROM courses WHERE course_id=?", (cid,))
            course = c.fetchone()
            title, price = course[0], course[1]
            progress = calculate_progress(st.session_state.user["id"], cid)
            st.markdown(f"**{title}** - Fee: {inr_format(price)}")
            st.progress(progress)
    else:
        st.info("You are not enrolled in any courses yet.")

def course_timeline(course_id):
    st.subheader("Course Timeline")
    
    c.execute("SELECT lesson_id, title FROM lessons WHERE course_id=? ORDER BY lesson_id", (course_id,))
    lessons = c.fetchall()
    
    student_id = st.session_state.user["id"]
    c.execute("SELECT lesson_id FROM progress WHERE student_id=? AND course_id=? AND completed=1", (student_id, course_id))
    completed_lessons = [x[0] for x in c.fetchall()]
    
    next_lesson_found = False
    for lesson in lessons:
        lid, title = lesson
        if lid in completed_lessons:
            st.markdown(f"[Completed] {title}")
        elif not next_lesson_found:
            st.markdown(f"[Next] {title}")
            next_lesson_found = True
            c.execute("SELECT content_type, content_path FROM lessons WHERE lesson_id=?", (lid,))
            content_type, content_path = c.fetchone()
            if content_type == "text":
                with open(content_path, "r") as f: st.write(f.read())
            elif content_type == "video":
                st.video(content_path)
            elif content_type == "pdf":
                st.download_button("Download PDF", open(content_path, "rb").read(), file_name=content_path.split("/")[-1])
            if st.button(f"Mark '{title}' as Completed"):
                c.execute("INSERT OR REPLACE INTO progress (student_id, course_id, lesson_id, completed) VALUES (?,?,?,1)", (student_id, course_id, lid))
                conn.commit()
                st.success(f"Lesson '{title}' marked as completed!")
                st.experimental_rerun()
        else:
            st.markdown(f"[Locked] {title}")

# ---------------------------
# Quiz & Certificate Logic
# ---------------------------
def student_quiz_tab():
    st.subheader("Course Quizzes")
    student_id = st.session_state.user["id"]
    c.execute("SELECT course_id, title FROM courses WHERE course_id IN (SELECT course_id FROM payments WHERE student_id=? AND status='paid')", (student_id,))
    enrolled_courses = c.fetchall()
    
    if not enrolled_courses:
        st.info("You have no enrolled courses with quizzes.")
        return
    
    for course in enrolled_courses:
        course_id, course_title = course
        st.markdown(f"### {course_title}")
        c.execute("SELECT quiz_id, question, option1, option2, option3, option4, answer FROM quizzes WHERE course_id=?", (course_id,))
        quizzes = c.fetchall()
        if not quizzes:
            st.write("No quizzes available for this course yet.")
            continue
        
        score = 0
        for q in quizzes:
            quiz_id, question, opt1, opt2, opt3, opt4, answer = q
            user_answer = st.radio(question, [opt1, opt2, opt3, opt4], key=f"quiz_{quiz_id}")
            if user_answer == answer:
                score += 1
        
        total = len(quizzes)
        if st.button(f"Submit Quiz for {course_title}"):
            percentage = (score / total) * 100
            st.write(f"Your Score: {score}/{total} ({percentage:.2f}%)")
            if percentage >= PASS_MARK:
                st.success("Congratulations! You passed the course.")
                # Certificate
                c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (student_id, course_id))
                existing = c.fetchone()
                if existing:
                    st.info("Certificate already generated.")
                    st.download_button("Download Certificate", open(existing[0], "rb").read(), file_name=existing[0].split("/")[-1])
                else:
                    cert_file = generate_certificate(st.session_state.user["name"], course_title)
                    c.execute("INSERT INTO certificates (student_id, course_id, cert_file) VALUES (?,?,?)",
                              (student_id, course_id, cert_file))
                    conn.commit()
                    st.success("Certificate generated automatically!")
                    st.download_button("Download Certificate", open(cert_file, "rb").read(), file_name=cert_file.split("/")[-1])
            else:
                st.warning(f"Score below passing mark ({PASS_MARK}%). Please try again.")

# ---------------------------
# Student Tabs
# ---------------------------
def student_tabs():
    tabs = st.tabs(["Course Catalog","Timeline Lessons","Quiz","Certificate","Dashboard"])
    
    with tabs[0]:
        st.subheader("Course Catalog")
        df_courses = pd.read_sql("SELECT * FROM courses", conn)
        df_courses['price'] = df_courses['price'].apply(inr_format)
        for index, row in df_courses.iterrows():
            st.markdown(f"**{row['title']}** - {row['price']}")
    
    with tabs[1]:
        c.execute("SELECT course_id, title FROM courses WHERE course_id IN (SELECT course_id FROM payments WHERE student_id=? AND status='paid')", (st.session_state.user["id"],))
        enrolled_courses = c.fetchall()
        if enrolled_courses:
            for course in enrolled_courses:
                course_id, course_title = course
                st.markdown(f"### {course_title}")
                course_timeline(course_id)
        else:
            st.info("No enrolled courses to show timeline.")
    
    with tabs[2]:
        student_quiz_tab()
    
    with tabs[3]:
        st.subheader("My Certificates")
        student_id = st.session_state.user["id"]
        c.execute("SELECT course_id, cert_file FROM certificates WHERE student_id=?", (student_id,))
        certs = c.fetchall()
        if certs:
            for course_id, cert_file in certs:
                c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,))
                title = c.fetchone()[0]
                st.markdown(f"**{title}**")
                st.download_button("Download Certificate", open(cert_file, "rb").read(), file_name=cert_file.split("/")[-1])
        else:
            st.info("No certificates available yet.")
    
    with tabs[4]:
        student_dashboard()

# ---------------------------
# Login / Signup
# ---------------------------
if st.session_state.user is None:
    st.title("EinTrust Academy Login / Signup")
    with st.form("login_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["student","admin"])
        submitted = st.form_submit_button("Signup / Login")
        if submitted:
            c.execute("SELECT * FROM students WHERE email=? AND password=?", (email,password)); user=c.fetchone()
            if user: st.session_state.user={"id":user[0],"name":user[1],"email":user[2],"role":user[4]}; st.success(f"Welcome back {user[1]}!")
            else: 
                try: c.execute("INSERT INTO students (name,email,password,role) VALUES (?,?,?,?)",(name,email,password,role)); conn.commit(); st.success("Signup complete! Please login.")
                except: st.error("Email exists. Try login.")
else:
    st.success(f"Welcome {st.session_state.user['name']}!")
    if st.session_state.user["role"]=="admin": admin_tabs()
    else: student_tabs()
