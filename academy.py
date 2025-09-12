import streamlit as st
import sqlite3

# ------------------------------
# Database Setup
# ------------------------------
DB_FILE = "academy.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Create tables if not exist
    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
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
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        video_url TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

# ------------------------------
# Utility Functions
# ------------------------------
def fetch_courses():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT course_id, title, subtitle, description, price, category, banner_path FROM courses ORDER BY course_id DESC")
    courses = c.fetchall()
    conn.close()
    return courses

def fetch_lessons(course_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT lesson_id, title, content, video_url FROM lessons WHERE course_id=? ORDER BY lesson_id", (course_id,))
    lessons = c.fetchall()
    conn.close()
    return lessons

def insert_course(title, subtitle, description, price, category, banner_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO courses (title, subtitle, description, price, category, banner_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, subtitle, description, price, category, banner_path))
    conn.commit()
    conn.close()

def insert_lesson(course_id, title, content, video_url):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO lessons (course_id, title, content, video_url)
        VALUES (?, ?, ?, ?)
    """, (course_id, title, content, video_url))
    conn.commit()
    conn.close()

# ------------------------------
# Pages
# ------------------------------
def home_page():
    st.title("🎓 Welcome to EinTrust Academy")
    st.write("A professional LMS platform for sustainability and climate action learning.")

    courses = fetch_courses()
    if not courses:
        st.info("No courses available yet. Please add courses from the Admin section.")
    else:
        for course_id, title, subtitle, desc, price, category, banner in courses:
            with st.expander(f"{title} ({category}) - ₹{price:,.2f}"):
                st.write(subtitle)
                st.write(desc)
                if banner:
                    st.image(banner, use_container_width=True)
                if st.button("View Lessons", key=f"lessons_{course_id}"):
                    st.session_state["page"] = "course"
                    st.session_state["course_id"] = course_id
                    st.rerun()

def course_page(course_id):
    st.title("📘 Course Details")
    lessons = fetch_lessons(course_id)
    if not lessons:
        st.info("No lessons uploaded for this course yet.")
    else:
        for lesson_id, title, content, video_url in lessons:
            st.subheader(title)
            st.write(content if content else "")
            if video_url:
                st.video(video_url)

    if st.button("⬅ Back to Courses"):
        st.session_state["page"] = "home"
        st.rerun()

def admin_page():
    st.title("⚙️ Admin Panel")

    st.subheader("Add New Course")
    with st.form("add_course"):
        title = st.text_input("Course Title")
        subtitle = st.text_input("Subtitle")
        description = st.text_area("Description")
        price = st.number_input("Price (₹)", min_value=0.0, step=100.0)
        category = st.text_input("Category")
        banner_path = st.text_input("Banner Image Path (optional)")
        submitted = st.form_submit_button("Add Course")
        if submitted:
            insert_course(title, subtitle, description, price, category, banner_path)
            st.success("Course added successfully!")

    st.subheader("Add Lesson to Course")
    courses = fetch_courses()
    if courses:
        course_options = {f"{c[1]} ({c[0]})": c[0] for c in courses}
        course_choice = st.selectbox("Select Course", list(course_options.keys()))
        with st.form("add_lesson"):
            lesson_title = st.text_input("Lesson Title")
            content = st.text_area("Content")
            video_url = st.text_input("Video URL (optional)")
            submitted = st.form_submit_button("Add Lesson")
            if submitted:
                insert_lesson(course_options[course_choice], lesson_title, content, video_url)
                st.success("Lesson added successfully!")
    else:
        st.info("Please add a course first.")

# ------------------------------
# Main
# ------------------------------
def main():
    st.set_page_config(page_title="EinTrust Academy", page_icon="🎓", layout="wide")

    init_db()  # ✅ Ensures tables exist before anything else

    menu = ["Home", "Admin"]
    choice = st.sidebar.radio("Navigate", menu)

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    if choice == "Home":
        if st.session_state["page"] == "home":
            home_page()
        elif st.session_state["page"] == "course":
            course_page(st.session_state["course_id"])
    elif choice == "Admin":
        admin_page()

if __name__ == "__main__":
    main()
