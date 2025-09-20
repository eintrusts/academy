import streamlit as st
import sqlite3
import re
import io
import pandas as pd

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
    try:
        c.execute("INSERT INTO students (full_name,email,password,gender,profession,institution,first_enrollment,last_login) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))",
                  (full_name, email, password, gender, profession, institution))
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
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price
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

# ---------------------------
# Page Config + CSS
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
st.markdown("""
<style>
body {background-color: #0d0f12; color: #e0e0e0;}
.stApp {background-color: #0d0f12; color: #e0e0e0;}
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
</style>
""", unsafe_allow_html=True)

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
                if st.button("Enroll", key=f"enroll_{course[0]}"):
                    enroll_student_in_course(student_id, course[0])
                    st.success(f"Enrolled in {course[1]}!")
            if editable:
                if st.button("Edit Course", key=f"edit_{course[0]}"):
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
# All other pages (home, signup, login, student dashboard, admin login) are same as your previous working version
# ---------------------------

# ---------------------------
# Admin Dashboard with Tabs
# ---------------------------
def page_admin_dashboard():
    st.header("Admin Dashboard")
    tabs = st.tabs(["Dashboard","Students Data","Courses Data","Logout"])
    
    # Dashboard Metrics
    with tabs[0]:
        st.subheader("Statistics Overview")
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        most_viewed_course = c.execute("SELECT title, views FROM courses ORDER BY views DESC LIMIT 1").fetchone()
        most_viewed_course_text = f"{most_viewed_course[0]} ({most_viewed_course[1]} views)" if most_viewed_course else "N/A"
        most_viewed_module = c.execute("SELECT title, views FROM modules ORDER BY views DESC LIMIT 1").fetchone()
        most_viewed_module_text = f"{most_viewed_module[0]} ({most_viewed_module[1]} views)" if most_viewed_module else "N/A"
        cols = st.columns(4)
        cols[0].metric("Total Students", total_students)
        cols[1].metric("Total Courses", total_courses)
        cols[2].metric("Most Viewed Course", most_viewed_course_text)
        cols[3].metric("Most Viewed Module", most_viewed_module_text)
    
    # Students Data
    with tabs[1]:
        st.subheader("Students List")
        students = c.execute("SELECT * FROM students").fetchall()
        df_students = pd.DataFrame(students, columns=["ID","Name","Email","Password","Gender","Profession","Institution","First Enrollment","Last Login"])
        st.dataframe(df_students[["ID","Name","Email","First Enrollment","Last Login"]])
        csv = df_students.to_csv(index=False).encode('utf-8')
        st.download_button("Download Students Data", data=csv, file_name="students.csv", mime="text/csv")
    
    # Courses Data
    with tabs[2]:
        st.subheader("Courses Management")
        course_tabs = st.tabs(["Add Course","Update Course"])
        
        # Add Course + Add Module form
        with course_tabs[0]:
            with st.form("add_course_form"):
                title = st.text_input("Course Title")
                subtitle = st.text_input("Subtitle")
                desc = st.text_area("Description")
                price = st.number_input("Price", min_value=0.0, step=1.0)
                add_course_btn = st.form_submit_button("Add Course")
            if add_course_btn:
                course_id = add_course(title, subtitle, desc, price)
                st.success("Course added! Now you can add modules below.")
                st.session_state["selected_course"] = course_id
                st.experimental_rerun()
            
            # Add Module form
            if "selected_course" in st.session_state:
                st.markdown(f"### Add Module to Course ID: {st.session_state['selected_course']}")
                with st.form("add_module_form"):
                    module_title = st.text_input("Module Title")
                    module_desc = st.text_area("Module Description")
                    module_type = st.selectbox("Module Type", ["Video","PPT","PDF","Task","Quiz"])
                    uploaded_file = st.file_uploader("Upload File (if applicable)")
                    link = st.text_input("External Link (if applicable)")
                    add_module_btn = st.form_submit_button("Add Module")
                if add_module_btn:
                    file_bytes = convert_file_to_bytes(uploaded_file)
                    add_module(st.session_state['selected_course'], module_title, module_desc, module_type, file_bytes, link)
                    st.success("Module added!")
        
        # Update Course + Update Module forms
        with course_tabs[1]:
            courses = get_courses()
            course_titles = [f"{c[0]} - {c[1]}" for c in courses]
            selected = st.selectbox("Select Course to Update", course_titles)
            if selected:
                course_id = int(selected.split(" - ")[0])
                course = c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
                with st.form("update_course_form"):
                    title_u = st.text_input("Course Title", value=course[1])
                    subtitle_u = st.text_input("Subtitle", value=course[2])
                    desc_u = st.text_area("Description", value=course[3])
                    price_u = st.number_input("Price", min_value=0.0, value=course[4])
                    update_course_btn = st.form_submit_button("Update Course")
                if update_course_btn:
                    update_course(course_id, title_u, subtitle_u, desc_u, price_u)
                    st.success("Course updated!")
                
                if st.button("Delete Course"):
                    delete_course(course_id)
                    st.success("Course deleted!")
                    st.experimental_rerun()
                
                st.markdown("### Modules")
                modules = get_modules(course_id)
                for m in modules:
                    st.markdown(f"**{m[2]}** ({m[4]})")
                    with st.form(f"update_module_form_{m[0]}"):
                        m_title = st.text_input("Module Title", value=m[2], key=f"title_{m[0]}")
                        m_desc = st.text_area("Module Desc", value=m[3], key=f"desc_{m[0]}")
                        m_type = st.selectbox("Module Type", ["Video","PPT","PDF","Task","Quiz"], index=["Video","PPT","PDF","Task","Quiz"].index(m[4]), key=f"type_{m[0]}")
                        m_link = st.text_input("Module Link", value=m[6] if m[6] else "", key=f"link_{m[0]}")
                        m_file = st.file_uploader("Upload File (if want to replace)", key=f"file_{m[0]}")
                        m_update_btn = st.form_submit_button("Update Module")
                    if m_update_btn:
                        file_bytes = convert_file_to_bytes(m_file)
                        update_module(m[0], m_title, m_desc, m_type, file_bytes, m_link)
                        st.success("Module updated!")
                    if st.button("Delete Module", key=f"del_{m[0]}"):
                        delete_module(m[0])
                        st.success("Module deleted!")
                        st.experimental_rerun()
    
    # Logout
    with tabs[3]:
        st.session_state.clear()
        st.info("Logged out successfully")
        st.experimental_rerun()

# ---------------------------
# Main
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()  # Your previous home page function
elif st.session_state["page"] == "student_dashboard":
    page_student_dashboard()  # Your previous student dashboard function
elif st.session_state["page"] == "admin_dashboard":
    page_admin_dashboard()
