"""EinTrust Academy: learning management system for EinTrust (www.eintrusts.com).

Run locally with:  streamlit run academy.py
"""
import streamlit as st

from lms import config, db, ui
from lms.views import admin, public, student

st.set_page_config(page_title=config.BRAND_NAME, page_icon="🌿", layout="wide")


@st.cache_resource
def _init_database():
    db.init_db()
    return True


_init_database()
ui.apply_styles()


def _sign_out():
    ui.sign_out()
    st.switch_page(ui.PAGES["catalog"])


pages = {
    "catalog": st.Page(public.page_catalog, title="Courses", icon="📚", default=True),
    "course": st.Page(public.page_course, title="Course", icon="📘", url_path="course", visibility="hidden"),
    "verify": st.Page(public.page_verify, title="Verify certificate", icon="✅", url_path="verify"),
    "auth": st.Page(public.page_auth, title="Sign in", icon="🔑", url_path="signin"),
    "my_learning": st.Page(student.page_my_learning, title="My learning", icon="🎯", url_path="my-learning"),
    "certificates": st.Page(student.page_certificates, title="My certificates", icon="🎓", url_path="certificates"),
    "profile": st.Page(student.page_profile, title="Profile", icon="👤", url_path="profile"),
    "admin_dashboard": st.Page(admin.page_dashboard, title="Dashboard", icon="📊", url_path="admin"),
    "admin_courses": st.Page(admin.page_courses, title="Manage courses", icon="🛠️", url_path="admin-courses"),
    "admin_learners": st.Page(admin.page_learners, title="Learners", icon="👥", url_path="admin-learners"),
    "admin_enrollments": st.Page(admin.page_enrollments, title="Enrollments & payments", icon="💳",
                                 url_path="admin-enrollments"),
    "admin_certificates": st.Page(admin.page_certificates, title="Certificates issued", icon="📜",
                                  url_path="admin-certificates"),
    "sign_out": st.Page(_sign_out, title="Sign out", icon="🚪", url_path="signout"),
}
ui.PAGES.update(pages)

if ui.is_admin():
    menu = [pages[k] for k in ("admin_dashboard", "admin_courses", "admin_learners", "admin_enrollments",
                               "admin_certificates", "catalog", "sign_out")]
elif ui.current_student():
    menu = [pages[k] for k in ("catalog", "my_learning", "certificates", "profile", "sign_out")]
else:
    menu = [pages[k] for k in ("catalog", "verify", "auth")]

# The course page is opened by link (/course?id=...) and is hidden from the menu.
menu.append(pages["course"])
nav = st.navigation(menu, position="top")

# After signing in, the menu changes; land on the right page for the new role.
landing = st.session_state.pop("landing_page", None)
if landing:
    st.switch_page(pages[landing], query_params=st.session_state.pop("landing_params", None))
nav.run()
