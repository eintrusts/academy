import streamlit as st
import sqlite3
import hashlib

# ----------------------------
# DATABASE SETUP
# ----------------------------
conn = sqlite3.connect("eintrust_academy.db", check_same_thread=False)
c = conn.cursor()

# ----------------------------
# TABLES
# ----------------------------
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

c.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    subtitle TEXT,
    description TEXT,
    price REAL,
    category TEXT,
    banner_path TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    content_type TEXT,
    content_path TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")
conn.commit()

# ----------------------------
# INSERT DUMMY DATA
# ----------------------------
def insert_dummy_data():
    courses = [
        ("Sustainability Basics", "Intro to Sustainability",
         "Learn fundamentals of sustainability and eco-friendly practices.", 499.0, "Sustainability", "https://via.placeholder.com/350x150"),
        ("Climate Change Fundamentals", "Understand Climate Change",
         "Explore causes, impacts, and mitigation strategies of climate change.", 599.0, "Climate Change", "https://via.placeholder.com/350x150"),
        ("ESG & Corporate Responsibility", "Environmental, Social & Governance",
         "Dive into ESG concepts, reporting standards, and real-world case studies.", 799.0, "ESG", "https://via.placeholder.com/350x150")
    ]
    for title, subtitle, desc, price, cat, banner in courses:
        c.execute("""
        INSERT OR IGNORE INTO courses (title, subtitle, description, price, category, banner_path)
        VALUES (?,?,?,?,?,?)
        """, (title, subtitle, desc, price, cat, banner))
    conn.commit()

    lessons = {
        1: [("Intro","text",""), ("Global Practices","pdf",""), ("Local Action","video","")],
        2: [("Causes","text",""), ("Impacts","pdf",""), ("Mitigation","video","")],
        3: [("What is ESG","text",""), ("Reporting","pdf",""), ("Case Studies","video","")]
    }
    for cid, les in lessons.items():
        for title, ctype, path in les:
            c.execute("""
            INSERT OR IGNORE INTO lessons (course_id,title,content_type,content_path)
            VALUES (?,?,?,?)
            """, (cid, title, ctype, path))
    conn.commit()

insert_dummy_data()

# ----------------------------
# SESSION STATE
# ----------------------------
if 'student_id' not in st.session_state: st.session_state.student_id = None
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False
if 'page' not in st.session_state: st.session_state.page = "home"

# ----------------------------
# STYLING
# ----------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon="🌱")
st.markdown("""
<style>
body, .stApp {background-color: #121212; color: #f0f0f0; font-family: 'Arial', sans-serif;}
a {color: #00bfff; text-decoration:none;}
a:hover {color: #009acd;}
.course-card:hover {background-color:#1e1e1e; transform: scale(1.02); transition: 0.3s;}
.top-nav {background-color:#1f1f1f; padding:10px 20px; position:sticky; top:0; z-index:9999; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #333;}
.nav-center {display:flex; gap:15px; align-items:center;}
.nav-center input, .nav-center select {padding:5px; border-radius:5px; border:none;}
.nav-link {margin-right:15px; color:#f0f0f0; font-weight:bold; cursor:pointer;}
.nav-link:hover {color:#00bfff;}
.btn-hover {background-color:#00bfff; color:#000; padding:6px 15px; border-radius:5px; font-weight:bold;}
.btn-hover:hover {background-color:#009acd; color:#fff; cursor:pointer;}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# UTILITIES
# ----------------------------
def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()
def verify_password(pw, hashed): return hash_password(pw) == hashed

# ----------------------------
# TOP NAV
# ----------------------------
def top_nav():
    try:
        c.execute("SELECT DISTINCT category FROM courses")
        categories = [row[0] for row in c.fetchall() if row[0] is not None]
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        categories = []
    categories = ["All"] + categories

    col1, col2, col3 = st.columns([2,5,2])
    with col1:
        st.image("https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png", width=180)
    with col2:
        st.markdown("""
            <span class="nav-link">Browse Courses</span>
            <span class="nav-link">About</span>
            <span class="nav-link">Contact</span>
        """, unsafe_allow_html=True)
        search_query = st.text_input("Search for anything", key="search")
        category_filter = st.selectbox("Category", categories, key="cat_filter")
    with col3:
        if st.session_state.student_id is None:
            if st.button("Login", key="login_btn_top"): st.session_state.page = "login"
        if st.button("Admin", key="admin_btn"): st.session_state.page = "admin_login"
    return search_query, category_filter

# ----------------------------
# DISPLAY COURSES
# ----------------------------
def display_courses(search_query="", category_filter="All"):
    query = "SELECT course_id, title, subtitle, description, price, category, banner_path FROM courses"
    params = []
    if category_filter != "All":
        query += " WHERE category=?"
        params.append(category_filter)
    courses = c.execute(query, params).fetchall()
    if search_query:
        courses = [crs for crs in courses if search_query.lower() in crs[1].lower()]
    for crs in courses:
        st.markdown(f"""
        <div class="course-card" style="padding:15px; margin:10px; border:1px solid #333; border-radius:10px;">
            <img src="{crs[6]}" width="100%">
            <h3>{crs[1]}</h3>
            <h5>{crs[2]}</h5>
            <p>{crs[3]}</p>
            <b>₹{crs[4]:,.0f}</b>
            <br><button class="btn-hover" onclick="window.alert('Enroll/Login first')">Preview / Enroll</button>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------
# HOME PAGE
# ----------------------------
def home_page():
    search_query, category_filter = top_nav()
    display_courses(search_query, category_filter)
    st.markdown("<div style='text-align:center; padding:10px;'>© 2025 EinTrust Academy</div>", unsafe_allow_html=True)

# ----------------------------
# MAIN
# ----------------------------
def main():
    if st.session_state.page == "home": home_page()

main()
