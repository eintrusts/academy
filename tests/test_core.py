import sqlite3

import pytest

from lms import auth, certificates, db, seed


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("ACADEMY_DB_PATH", str(path))
    db.init_db()
    return path


def test_password_hashing_roundtrip():
    stored = auth.hash_password("Secret#123")
    assert stored.startswith("pbkdf2_sha256$")
    assert auth.verify_password("Secret#123", stored)
    assert not auth.verify_password("wrong", stored)


def test_password_rules():
    assert auth.is_valid_password("Abcdefg1!")
    assert not auth.is_valid_password("abcdefg1!")  # no uppercase
    assert not auth.is_valid_password("Abcdefgh!")  # no digit
    assert not auth.is_valid_password("Abcdefg12")  # no special char
    assert not auth.is_valid_password("Ab1!")  # too short


def test_register_and_authenticate_case_insensitive_email():
    sid = db.create_student("Asha Rao", "Asha@Example.com", "Secret#123")
    assert sid
    assert db.create_student("Dup", "asha@example.com", "Secret#123") is None
    student = db.authenticate("ASHA@example.com", "Secret#123")
    assert student["student_id"] == sid
    assert student["last_login"]
    assert db.authenticate("asha@example.com", "nope") is None


def test_legacy_plaintext_password_is_upgraded(temp_db):
    with sqlite3.connect(temp_db) as conn:
        conn.execute("INSERT INTO students (full_name, email, password) VALUES ('Old', 'old@x.com', 'Plain#123')")
    assert db.authenticate("old@x.com", "Plain#123")
    with sqlite3.connect(temp_db) as conn:
        stored = conn.execute("SELECT password FROM students WHERE email='old@x.com'").fetchone()[0]
    assert auth.is_hashed(stored)
    assert db.authenticate("old@x.com", "Plain#123")


def test_deactivated_student_cannot_sign_in():
    sid = db.create_student("A", "a@x.com", "Secret#123")
    db.set_student_active(sid, False)
    assert db.authenticate("a@x.com", "Secret#123") is None


def test_init_db_upgrades_prototype_schema(tmp_path, monkeypatch):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE courses (course_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, subtitle TEXT,
                description TEXT, price REAL, views INTEGER DEFAULT 0);
            CREATE TABLE student_courses (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, course_id INTEGER);
            INSERT INTO courses (title, subtitle, description, price) VALUES ('Old course', '', '', 0);
            INSERT INTO student_courses (student_id, course_id) VALUES (1, 1), (1, 1);
        """)
    monkeypatch.setenv("ACADEMY_DB_PATH", str(path))
    db.init_db()
    db.init_db()  # idempotent
    course = db.list_courses()[0]
    assert course["title"] == "Old course" and course["is_published"] == 1
    assert course["enrollments"] == 1  # duplicate enrollment collapsed


def test_module_update_keeps_file_unless_replaced():
    cid = db.create_course(title="C", price=0)
    mid = db.create_module(cid, "Slides", "PDF", file=b"%PDF-1", file_name="s.pdf", file_mime="application/pdf")
    db.update_module(mid, "Slides v2", "PDF")
    assert db.get_module_file(mid)["file"] == b"%PDF-1"
    assert db.get_module(mid)["title"] == "Slides v2"
    db.update_module(mid, "Slides v2", "PDF", remove_file=True)
    assert db.get_module_file(mid)["file"] is None


def test_module_ordering():
    cid = db.create_course(title="C", price=0)
    a = db.create_module(cid, "A", "Article")
    b = db.create_module(cid, "B", "Article")
    db.move_module(b, -1)
    assert [m["module_id"] for m in db.list_modules(cid)] == [b, a]


def test_progress_quiz_and_certificate_flow():
    cid = db.create_course(title="Carbon 101", price=0, pass_mark=50)
    lesson = db.create_module(cid, "Intro", "Article", content="Hello")
    quiz = db.create_module(cid, "Quiz", "Quiz")
    q1 = db.add_question(quiz, "2+2?", ["3", "4"], 1)
    q2 = db.add_question(quiz, "Scope 1 is?", ["Direct", "Indirect"], 0)
    sid = db.create_student("Learner", "l@x.com", "Secret#123")
    db.enroll(sid, cid)
    db.enroll(sid, cid)  # no duplicates
    assert len(db.student_enrollments(sid)) == 1

    db.mark_module_complete(sid, lesson)
    assert db.course_progress(sid, cid) == (1, 2, 50)
    assert db.issue_certificate(sid, cid) is None

    score, passed, _ = db.grade_quiz(sid, quiz, {q1: 0, q2: 1}, pass_mark=50)
    assert (score, passed) == (0.0, False)
    score, passed, _ = db.grade_quiz(sid, quiz, {q1: 1, q2: 1}, pass_mark=50)
    assert (score, passed) == (50.0, True)
    assert db.best_quiz_score(sid, quiz) == 50.0
    assert db.course_progress(sid, cid)[2] == 100

    cert_id = db.issue_certificate(sid, cid)
    assert cert_id.startswith("EINT-")
    assert db.issue_certificate(sid, cid) == cert_id  # idempotent
    cert = db.get_certificate(cert_id.lower())
    assert cert["full_name"] == "Learner" and cert["course_title"] == "Carbon 101"

    pdf = certificates.build_certificate(cert["full_name"], cert["course_title"], cert_id, cert["issued_at"], 2)
    assert pdf.startswith(b"%PDF")


def test_certificate_handles_non_latin_names():
    pdf = certificates.build_certificate("José Ñúñez 李", "ESG — Basics", "EINT-TEST", "2026-01-01 10:00:00")
    assert pdf.startswith(b"%PDF")


def test_manual_enrollment_request_approval():
    from lms import payments

    cid = db.create_course(title="Paid", price=4999)
    sid = db.create_student("P", "p@x.com", "Secret#123")
    payments.request_enrollment(db.get_student(sid), db.get_course(cid))
    pending = db.open_payment(sid, cid)
    assert pending["status"] == "requested"
    assert db.stats()["pending_requests"] == 1
    payments.approve_request(pending)
    assert db.is_enrolled(sid, cid)
    assert db.stats()["revenue"] == 4999


def test_delete_course_cleans_up():
    cid = db.create_course(title="Gone", price=0)
    mid = db.create_module(cid, "Q", "Quiz")
    db.add_question(mid, "q", ["a", "b"], 0)
    sid = db.create_student("D", "d@x.com", "Secret#123")
    db.enroll(sid, cid)
    db.mark_module_complete(sid, mid)
    db.delete_course(cid)
    assert db.get_course(cid) is None
    assert db.list_questions(mid) == []
    assert db.student_enrollments(sid) == []


def test_starter_courses_load_as_drafts_and_are_idempotent():
    assert seed.load_starter_courses() == len(seed.STARTER_COURSES)
    assert seed.load_starter_courses() == 0
    assert db.list_courses(published_only=True) == []
    drafts = db.list_courses(published_only=False)
    assert all(c["module_count"] >= 2 for c in drafts)
    quiz = [m for m in db.list_modules(drafts[0]["course_id"]) if m["module_type"] == "Quiz"][0]
    assert db.list_questions(quiz["module_id"])
