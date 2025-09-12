import streamlit as st
import sqlite3
from fpdf import FPDF
from datetime import datetime

# ----------------------------
# DATABASE SETUP
# ----------------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# Students table
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    sex TEXT,
    profession TEXT,
    institution TEXT,
    mobile TEXT,
    profile_pic TEXT
)
""")

# Courses table
c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    price REAL,
    category TEXT,
    banner_path TEXT
)
""")

# Lessons table
c.execute("""
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content_type TEXT, -- video/pdf/ppt/text
    content_path TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

# Enrollments table
c.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    progress REAL DEFAULT 0,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

# Certificates table
c.execute("""
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    cert_file TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

conn.commit()

# ----------------------------
# DUMMY DATA (Courses + Lessons)
# ----------------------------
def insert_dummy_data():
    # Check if courses exist
    c.execute("SELECT COUNT(*) FROM courses")
    if c.fetchone()[0] == 0:
        courses = [
            ("Sustainability Basics", "Introduction to Sustainability", 
             "Learn the fundamentals of sustainability and eco-friendly practices.", 499, "Sustainability", "https://via.placeholder.com/350x150"),
            ("Climate Change Fundamentals", "Understand Climate Change", 
             "Explore causes, impacts, and mitigation strategies of climate change.", 599, "Climate Change", "https://via.placeholder.com/350x150"),
            ("ESG & Corporate Responsibility", "Environmental, Social & Governance", 
             "Dive into ESG concepts, reporting standards, and real-world case studies.", 799, "ESG", "https://via.placeholder.com/350x150")
        ]
        for title, subtitle, desc, price, cat, banner in courses:
            c.execute("INSERT INTO courses (title, subtitle, description, price, category, banner_path) VALUES (?,?,?,?,?,?)",
                      (title, subtitle, desc, price, cat, banner))
        conn.commit()

        # Add lessons for each course
        course_ids = [1,2,3]
        lessons = {
            1: [("Introduction to Sustainability","text",""), ("Global Practices","pdf",""), ("Local Action","video","")],
            2: [("Causes of Climate Change","text",""), ("Impacts","pdf",""), ("Mitigation Strategies","video","")],
            3: [("What is ESG","text",""), ("Reporting Standards","pdf",""), ("Case Studies","video","")]
        }
        for cid, les in lessons.items():
            for title, ctype, path in les:
                c.execute("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)",
                          (cid, title, ctype, path))
        conn.commit()

insert_dummy_data()

# ----------------------------
# CSS STYLING
# ----------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon="🌱")

st.markdown("""
<style>
/* Dark Theme */
body, .stApp {
    background-color: #121212;
    color: #f0f0f0;
    font-family: 'Arial', sans-serif;
}
a {color: #00bfff; text-decoration:none;}
a:hover {color: #009acd;}
.course-card:hover {background-color:#1e1e1e; transform: scale(1.02); transition: 0.3s;}
.lesson-card:hover {background-color:#1e1e1e; transform: scale(1.01); transition: 0.2s;}
.top-nav {
    background-color:#1f1f1f; padding:10px 20px; position:sticky; top:0; z-index:9999; display:flex; align-items:center; justify-content:space-between;
    border-bottom:1px solid #333;
}
.nav-center {display:flex; gap:15px; align-items:center;}
.nav-center input, .nav-center select {padding:5px; border-radius:5px; border:none;}
.nav-link {margin-right:15px; color:#f0f0f0; font-weight:bold;}
.nav-link:hover {color:#00bfff; cursor:pointer;}
.btn-hover {background-color:#00bfff; color:#000; padding:6px 15px; border-radius:5px; font-weight:bold;}
.btn-hover:hover {background-color:#009acd; color:#fff; cursor:pointer;}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# SESSION STATE
# ----------------------------
if 'student_id' not in st.session_state:
    st.session_state.student_id = None
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# ----------------------------
# NAV BAR
# ----------------------------
def top_nav():
    st.markdown("""
    <div class="top-nav">
        <div style="display:flex; align-items:center;">
            <img src="https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png" width="180">
        </div>
        <div class="nav-center">
            <span class="nav-link" onclick="window.scrollTo(0,0)">Browse Courses</span>
            <span class="nav-link">About</span>
            <span class="nav-link">Contact</span>
            <input type="text" placeholder="Search for anything" id="search_bar">
            <select id="category_filter">
                <option value="">All Categories</option>
            </select>
        </div>
        <div>
            <button class="btn-hover" onclick="window.location.href='#'">Login</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# COURSE BROWSING PAGE
# ----------------------------
def page_courses():
    st.subheader("All Courses")
    search_query = st.text_input("Search for courses", "")
    # Dynamic categories
    c.execute("SELECT DISTINCT category FROM courses")
    categories = [row[0] for row in c.fetchall()]
    category_filter = st.selectbox("Select Category", ["All"] + categories)

    # Fetch courses
    query = "SELECT course_id, title, subtitle, description, price, category, banner_path FROM courses"
    params = []
    if category_filter != "All":
        query += " WHERE category=?"
        params.append(category_filter)
    courses = c.execute(query, params).fetchall()

    # Filter by search
    if search_query:
        courses = [crs for crs in courses if search_query.lower() in crs[1].lower()]

    # Display cards
    for crs in courses:
        st.markdown(f"""
        <div class="course-card" style="padding:15px; margin:10px; border:1px solid #333; border-radius:10px;">
            <img src="{crs[6]}" width="100%">
            <h3>{crs[1]}</h3>
            <h5>{crs[2]}</h5>
            <p>{crs[3]}</p>
            <b>₹{crs[4]:,.0f}</b>
            <br><button class="btn-hover" onclick="window.location.href='#'">Preview / Enroll</button>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------
# MAIN APP
# ----------------------------
def main():
    top_nav()
    page_courses()

main()

# Footer
st.markdown("<div style='text-align:center; padding:10px;'>© 2025 EinTrust Academy</div>", unsafe_allow_html=True)
