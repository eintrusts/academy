"""Shared UI helpers: styling, session state, navigation registry and course cards."""
import streamlit as st

from . import config, db

# Page objects are registered by academy.py so views can link to each other.
PAGES = {}

CSS = """
<style>
.ea-brand {display:flex; align-items:center; gap:14px; margin-bottom:0.5rem;}
.ea-brand img {width:52px; height:52px; object-fit:contain;}
.ea-brand h1 {margin:0; padding:0; font-size:1.9rem;}
.ea-brand p {margin:0; opacity:0.75;}
.ea-tag {display:inline-block; padding:2px 10px; margin:0 6px 6px 0; border-radius:999px;
         font-size:0.78rem; border:1px solid rgba(76,175,80,0.6); color:#7bc67e;}
.ea-price {font-weight:700; font-size:1.05rem;}
.ea-footer {text-align:center; opacity:0.6; padding:24px 0 8px 0; font-size:0.85rem;}
</style>
"""


def apply_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def brand_header(subtitle=None):
    st.markdown(
        f"""<div class="ea-brand"><img src="{config.LOGO_URL}" alt="">
        <div><h1>{config.BRAND_NAME}</h1><p>{subtitle or config.TAGLINE}</p></div></div>""",
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(
        f"""<div class="ea-footer">&copy; {config.COMPANY_NAME} &middot;
        <a href="{config.COMPANY_WEBSITE}" target="_blank">{config.COMPANY_WEBSITE.replace('https://', '')}</a></div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
def current_student():
    sid = st.session_state.get("student_id")
    if not sid:
        return None
    student = db.get_student(sid)
    if not student or not student.get("is_active", 1):
        st.session_state.pop("student_id", None)
        return None
    return student


def is_admin():
    return bool(st.session_state.get("is_admin"))


def sign_out():
    for key in ("student_id", "is_admin", "payments_refreshed"):
        st.session_state.pop(key, None)


def go(page_key, **query_params):
    st.switch_page(PAGES[page_key], query_params=query_params or None)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def price_label(price):
    price = float(price or 0)
    return "Free" if price == 0 else f"₹{price:,.0f}"


def course_tags(course):
    tags = [course.get("category"), course.get("level")]
    if course.get("duration_hours"):
        tags.append(f"{course['duration_hours']:g} hrs")
    html = "".join(f'<span class="ea-tag">{_esc(t)}</span>' for t in tags if t)
    if html:
        st.markdown(html, unsafe_allow_html=True)


def _esc(text):
    import html

    return html.escape(str(text))


def course_card(course, key_prefix, action_label="View course"):
    with st.container(border=True):
        if course.get("thumbnail_url"):
            st.image(course["thumbnail_url"], width="stretch")
        st.subheader(course["title"] or "Untitled course", anchor=False)
        course_tags(course)
        if course.get("subtitle"):
            st.caption(course["subtitle"])
        desc = (course.get("description") or "").strip()
        if desc:
            st.write(desc[:180] + ("…" if len(desc) > 180 else ""))
        left, right = st.columns([1, 1])
        left.markdown(f'<span class="ea-price">{price_label(course.get("price"))}</span>', unsafe_allow_html=True)
        if right.button(action_label, key=f"{key_prefix}_{course['course_id']}", width="stretch"):
            go("course", id=course["course_id"])
