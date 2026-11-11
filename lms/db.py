"""SQLite data layer.

The schema extends the tables created by the original prototype, so an
existing ``academy.db`` is upgraded in place by :func:`init_db`.
"""
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from . import auth, config


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def connect():
    conn = sqlite3.connect(config.db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


def _row(cur):
    r = cur.fetchone()
    return dict(r) if r else None


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_BASE_TABLES = """
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, subtitle TEXT, description TEXT, price REAL, views INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS modules (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER, title TEXT, description TEXT, module_type TEXT,
    file BLOB, link TEXT, views INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT, email TEXT UNIQUE, password TEXT, gender TEXT,
    profession TEXT, institution TEXT, first_enrollment TEXT, last_login TEXT
);
CREATE TABLE IF NOT EXISTS student_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, course_id INTEGER
);
CREATE TABLE IF NOT EXISTS module_progress (
    student_id INTEGER NOT NULL, module_id INTEGER NOT NULL, completed_at TEXT,
    PRIMARY KEY (student_id, module_id)
);
CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL, question TEXT NOT NULL, options TEXT NOT NULL,
    correct_index INTEGER NOT NULL, explanation TEXT
);
CREATE TABLE IF NOT EXISTS quiz_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL, module_id INTEGER NOT NULL,
    score REAL NOT NULL, passed INTEGER NOT NULL, attempted_at TEXT
);
CREATE TABLE IF NOT EXISTS certificates (
    cert_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, course_id INTEGER NOT NULL,
    issued_at TEXT, UNIQUE (student_id, course_id)
);
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL, course_id INTEGER NOT NULL, amount REAL,
    provider TEXT, provider_ref TEXT, payment_url TEXT,
    status TEXT NOT NULL, created_at TEXT, updated_at TEXT
);
"""

# Columns added on top of the prototype's tables: (table, column, definition)
_ADDED_COLUMNS = [
    ("courses", "category", "TEXT DEFAULT 'Other'"),
    ("courses", "level", "TEXT DEFAULT 'Beginner'"),
    ("courses", "duration_hours", "REAL DEFAULT 0"),
    ("courses", "instructor", "TEXT DEFAULT ''"),
    ("courses", "thumbnail_url", "TEXT DEFAULT ''"),
    ("courses", "learning_outcomes", "TEXT DEFAULT ''"),
    ("courses", "is_published", "INTEGER DEFAULT 1"),
    ("courses", "pass_mark", f"INTEGER DEFAULT {config.DEFAULT_PASS_MARK}"),
    ("courses", "created_at", "TEXT"),
    ("modules", "content", "TEXT DEFAULT ''"),
    ("modules", "position", "INTEGER DEFAULT 0"),
    ("modules", "file_name", "TEXT"),
    ("modules", "file_mime", "TEXT"),
    ("students", "phone", "TEXT DEFAULT ''"),
    ("students", "is_active", "INTEGER DEFAULT 1"),
    ("student_courses", "enrolled_at", "TEXT"),
    ("student_courses", "source", "TEXT DEFAULT 'self'"),
]


def init_db():
    with connect() as conn:
        conn.executescript(_BASE_TABLES)
        for table, column, definition in _ADDED_COLUMNS:
            existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        # The prototype allowed duplicate enrollments; collapse them before adding the unique index.
        conn.execute(
            "DELETE FROM student_courses WHERE id NOT IN "
            "(SELECT MIN(id) FROM student_courses GROUP BY student_id, course_id)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_enrollment ON student_courses(student_id, course_id)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_modules_course ON modules(course_id, position)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_questions_module ON quiz_questions(module_id)")
        # Give pre-existing modules a stable order.
        conn.execute("UPDATE modules SET position = module_id WHERE position IS NULL OR position = 0")
        conn.execute("UPDATE student_courses SET enrolled_at = ? WHERE enrolled_at IS NULL", (now(),))
        conn.execute("UPDATE courses SET created_at = ? WHERE created_at IS NULL", (now(),))


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
def create_student(full_name, email, password, gender="", profession="", institution="", phone=""):
    """Return the new student_id, or None if the email is already registered."""
    email = email.strip().lower()
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO students (full_name, email, password, gender, profession, institution, phone,"
                " first_enrollment, last_login) VALUES (?,?,?,?,?,?,?,?,?)",
                (full_name.strip(), email, auth.hash_password(password), gender, profession, institution,
                 phone, now(), None),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_student(student_id):
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM students WHERE student_id=?", (student_id,)))


def authenticate(email, password):
    """Return the student row on success, else None. Upgrades legacy plaintext passwords."""
    email = (email or "").strip().lower()
    with connect() as conn:
        student = _row(conn.execute("SELECT * FROM students WHERE lower(email)=?", (email,)))
        if not student or not student.get("is_active", 1):
            return None
        if not auth.verify_password(password, student["password"]):
            return None
        if not auth.is_hashed(student["password"]):
            conn.execute("UPDATE students SET password=? WHERE student_id=?",
                         (auth.hash_password(password), student["student_id"]))
        conn.execute("UPDATE students SET last_login=? WHERE student_id=?", (now(), student["student_id"]))
    return get_student(student["student_id"])


def update_student_profile(student_id, full_name, gender, profession, institution, phone):
    with connect() as conn:
        conn.execute(
            "UPDATE students SET full_name=?, gender=?, profession=?, institution=?, phone=? WHERE student_id=?",
            (full_name.strip(), gender, profession, institution, phone, student_id),
        )


def set_password(student_id, new_password):
    with connect() as conn:
        conn.execute("UPDATE students SET password=? WHERE student_id=?",
                     (auth.hash_password(new_password), student_id))


def set_student_active(student_id, active):
    with connect() as conn:
        conn.execute("UPDATE students SET is_active=? WHERE student_id=?", (1 if active else 0, student_id))


def list_students():
    """All learners with enrollment/completion counts. Never returns password hashes."""
    with connect() as conn:
        return _rows(conn.execute(
            """SELECT s.student_id, s.full_name, s.email, s.phone, s.gender, s.profession, s.institution,
                      s.first_enrollment AS registered_at, s.last_login, COALESCE(s.is_active, 1) AS is_active,
                      (SELECT COUNT(*) FROM student_courses sc WHERE sc.student_id = s.student_id) AS enrollments,
                      (SELECT COUNT(*) FROM certificates ce WHERE ce.student_id = s.student_id) AS certificates
               FROM students s ORDER BY s.student_id DESC"""
        ))


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------
_COURSE_FIELDS = ["title", "subtitle", "description", "price", "category", "level", "duration_hours",
                  "instructor", "thumbnail_url", "learning_outcomes", "is_published", "pass_mark"]


def create_course(**fields):
    data = {k: fields.get(k) for k in _COURSE_FIELDS if k in fields}
    data.setdefault("price", 0)
    data["created_at"] = now()
    cols = ", ".join(data)
    with connect() as conn:
        cur = conn.execute(f"INSERT INTO courses ({cols}) VALUES ({', '.join('?' * len(data))})",
                           tuple(data.values()))
        return cur.lastrowid


def update_course(course_id, **fields):
    data = {k: v for k, v in fields.items() if k in _COURSE_FIELDS}
    if not data:
        return
    assignments = ", ".join(f"{k}=?" for k in data)
    with connect() as conn:
        conn.execute(f"UPDATE courses SET {assignments} WHERE course_id=?", (*data.values(), course_id))


def delete_course(course_id):
    with connect() as conn:
        module_ids = [r["module_id"] for r in conn.execute("SELECT module_id FROM modules WHERE course_id=?",
                                                           (course_id,))]
        for mid in module_ids:
            _delete_module_rows(conn, mid)
        conn.execute("DELETE FROM student_courses WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM certificates WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM payments WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM courses WHERE course_id=?", (course_id,))


def get_course(course_id):
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)))


def list_courses(published_only=True):
    sql = """SELECT c.*,
                    (SELECT COUNT(*) FROM modules m WHERE m.course_id = c.course_id) AS module_count,
                    (SELECT COUNT(*) FROM student_courses sc WHERE sc.course_id = c.course_id) AS enrollments
             FROM courses c"""
    if published_only:
        sql += " WHERE COALESCE(c.is_published, 1) = 1"
    sql += " ORDER BY c.course_id DESC"
    with connect() as conn:
        return _rows(conn.execute(sql))


def increment_course_views(course_id):
    with connect() as conn:
        conn.execute("UPDATE courses SET views = COALESCE(views, 0) + 1 WHERE course_id=?", (course_id,))


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------
_MODULE_META = ("module_id, course_id, title, description, module_type, link, views, content, position, "
                "file_name, file_mime, (file IS NOT NULL AND length(file) > 0) AS has_file")


def list_modules(course_id):
    """Modules in order, without file payloads."""
    with connect() as conn:
        return _rows(conn.execute(
            f"SELECT {_MODULE_META} FROM modules WHERE course_id=? ORDER BY position, module_id", (course_id,)
        ))


def get_module(module_id):
    with connect() as conn:
        return _row(conn.execute(f"SELECT {_MODULE_META} FROM modules WHERE module_id=?", (module_id,)))


def get_module_file(module_id):
    with connect() as conn:
        return _row(conn.execute("SELECT file, file_name, file_mime FROM modules WHERE module_id=?", (module_id,)))


def create_module(course_id, title, module_type, description="", content="", link="",
                  file=None, file_name=None, file_mime=None):
    with connect() as conn:
        pos = conn.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM modules WHERE course_id=?",
                           (course_id,)).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO modules (course_id, title, description, module_type, content, link, file, file_name,"
            " file_mime, position) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (course_id, title, description, module_type, content, link, file, file_name, file_mime, pos),
        )
        return cur.lastrowid


def update_module(module_id, title, module_type, description="", content="", link="",
                  file=None, file_name=None, file_mime=None, remove_file=False):
    """Update a module. The stored file is kept unless a new one is given or ``remove_file`` is set."""
    with connect() as conn:
        conn.execute(
            "UPDATE modules SET title=?, description=?, module_type=?, content=?, link=? WHERE module_id=?",
            (title, description, module_type, content, link, module_id),
        )
        if file is not None:
            conn.execute("UPDATE modules SET file=?, file_name=?, file_mime=? WHERE module_id=?",
                         (file, file_name, file_mime, module_id))
        elif remove_file:
            conn.execute("UPDATE modules SET file=NULL, file_name=NULL, file_mime=NULL WHERE module_id=?",
                         (module_id,))


def _delete_module_rows(conn, module_id):
    conn.execute("DELETE FROM quiz_questions WHERE module_id=?", (module_id,))
    conn.execute("DELETE FROM quiz_attempts WHERE module_id=?", (module_id,))
    conn.execute("DELETE FROM module_progress WHERE module_id=?", (module_id,))
    conn.execute("DELETE FROM modules WHERE module_id=?", (module_id,))


def delete_module(module_id):
    with connect() as conn:
        _delete_module_rows(conn, module_id)


def move_module(module_id, direction):
    """Swap a module with its neighbour. direction: -1 (up) or +1 (down)."""
    module = get_module(module_id)
    if not module:
        return
    ordered = list_modules(module["course_id"])
    ids = [m["module_id"] for m in ordered]
    i = ids.index(module_id)
    j = i + direction
    if j < 0 or j >= len(ids):
        return
    ids[i], ids[j] = ids[j], ids[i]
    with connect() as conn:
        for pos, mid in enumerate(ids, start=1):
            conn.execute("UPDATE modules SET position=? WHERE module_id=?", (pos, mid))


def increment_module_views(module_id):
    with connect() as conn:
        conn.execute("UPDATE modules SET views = COALESCE(views, 0) + 1 WHERE module_id=?", (module_id,))


# ---------------------------------------------------------------------------
# Quizzes
# ---------------------------------------------------------------------------
def list_questions(module_id):
    with connect() as conn:
        rows = _rows(conn.execute("SELECT * FROM quiz_questions WHERE module_id=? ORDER BY question_id",
                                  (module_id,)))
    for r in rows:
        r["options"] = json.loads(r["options"])
    return rows


def add_question(module_id, question, options, correct_index, explanation=""):
    options = [o.strip() for o in options if o and o.strip()]
    if len(options) < 2 or not 0 <= correct_index < len(options):
        raise ValueError("A question needs at least two options and a valid correct answer.")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO quiz_questions (module_id, question, options, correct_index, explanation) VALUES (?,?,?,?,?)",
            (module_id, question.strip(), json.dumps(options), correct_index, explanation),
        )
        return cur.lastrowid


def delete_question(question_id):
    with connect() as conn:
        conn.execute("DELETE FROM quiz_questions WHERE question_id=?", (question_id,))


def grade_quiz(student_id, module_id, answers, pass_mark):
    """Grade ``answers`` (question_id -> chosen option index), record the attempt and
    mark the module complete on a pass. Returns (score_percent, passed, per-question results)."""
    questions = list_questions(module_id)
    if not questions:
        return 0.0, False, []
    results = []
    correct = 0
    for q in questions:
        chosen = answers.get(q["question_id"])
        ok = chosen == q["correct_index"]
        correct += ok
        results.append({"question": q, "chosen": chosen, "correct": ok})
    score = round(100.0 * correct / len(questions), 1)
    passed = score >= pass_mark
    with connect() as conn:
        conn.execute(
            "INSERT INTO quiz_attempts (student_id, module_id, score, passed, attempted_at) VALUES (?,?,?,?,?)",
            (student_id, module_id, score, int(passed), now()),
        )
    if passed:
        mark_module_complete(student_id, module_id)
    return score, passed, results


def best_quiz_score(student_id, module_id):
    with connect() as conn:
        r = conn.execute("SELECT MAX(score) FROM quiz_attempts WHERE student_id=? AND module_id=?",
                         (student_id, module_id)).fetchone()
    return r[0]


# ---------------------------------------------------------------------------
# Enrollment & progress
# ---------------------------------------------------------------------------
def enroll(student_id, course_id, source="self"):
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO student_courses (student_id, course_id, enrolled_at, source) VALUES (?,?,?,?)",
            (student_id, course_id, now(), source),
        )


def unenroll(student_id, course_id):
    with connect() as conn:
        conn.execute("DELETE FROM student_courses WHERE student_id=? AND course_id=?", (student_id, course_id))


def is_enrolled(student_id, course_id):
    with connect() as conn:
        return conn.execute("SELECT 1 FROM student_courses WHERE student_id=? AND course_id=?",
                            (student_id, course_id)).fetchone() is not None


def mark_module_complete(student_id, module_id):
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO module_progress (student_id, module_id, completed_at) VALUES (?,?,?)",
                     (student_id, module_id, now()))


def completed_module_ids(student_id, course_id):
    with connect() as conn:
        return {r[0] for r in conn.execute(
            "SELECT mp.module_id FROM module_progress mp JOIN modules m ON m.module_id = mp.module_id "
            "WHERE mp.student_id=? AND m.course_id=?", (student_id, course_id))}


def course_progress(student_id, course_id):
    """Return (completed_count, total_count, percent)."""
    total = len(list_modules(course_id))
    done = len(completed_module_ids(student_id, course_id))
    pct = round(100.0 * done / total) if total else 0
    return done, total, pct


def student_enrollments(student_id):
    with connect() as conn:
        rows = _rows(conn.execute(
            "SELECT c.*, sc.enrolled_at FROM courses c JOIN student_courses sc ON sc.course_id = c.course_id "
            "WHERE sc.student_id=? ORDER BY sc.enrolled_at DESC", (student_id,)))
    for r in rows:
        r["done"], r["total"], r["progress"] = course_progress(student_id, r["course_id"])
    return rows


def course_learners(course_id):
    with connect() as conn:
        rows = _rows(conn.execute(
            "SELECT s.student_id, s.full_name, s.email, sc.enrolled_at, sc.source FROM students s "
            "JOIN student_courses sc ON sc.student_id = s.student_id WHERE sc.course_id=? "
            "ORDER BY sc.enrolled_at DESC", (course_id,)))
    for r in rows:
        r["done"], r["total"], r["progress"] = course_progress(r["student_id"], course_id)
    return rows


# ---------------------------------------------------------------------------
# Certificates
# ---------------------------------------------------------------------------
def issue_certificate(student_id, course_id):
    """Issue (or return the existing) certificate once every module is complete. Returns cert_id or None."""
    done, total, _ = course_progress(student_id, course_id)
    if total == 0 or done < total:
        return None
    with connect() as conn:
        existing = conn.execute("SELECT cert_id FROM certificates WHERE student_id=? AND course_id=?",
                                (student_id, course_id)).fetchone()
        if existing:
            return existing[0]
        cert_id = "EINT-" + secrets.token_hex(4).upper()
        conn.execute("INSERT INTO certificates (cert_id, student_id, course_id, issued_at) VALUES (?,?,?,?)",
                     (cert_id, student_id, course_id, now()))
        return cert_id


def get_certificate(cert_id):
    with connect() as conn:
        return _row(conn.execute(
            "SELECT ce.cert_id, ce.issued_at, s.full_name, s.student_id, c.title AS course_title, c.course_id, "
            "c.duration_hours FROM certificates ce JOIN students s ON s.student_id = ce.student_id "
            "JOIN courses c ON c.course_id = ce.course_id WHERE ce.cert_id=?", ((cert_id or "").strip().upper(),)))


def student_certificates(student_id):
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT ce.cert_id, ce.issued_at, c.title AS course_title, c.course_id FROM certificates ce "
            "JOIN courses c ON c.course_id = ce.course_id WHERE ce.student_id=? ORDER BY ce.issued_at DESC",
            (student_id,)))


def list_certificates():
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT ce.cert_id, ce.issued_at, s.full_name, s.email, c.title AS course_title FROM certificates ce "
            "JOIN students s ON s.student_id = ce.student_id JOIN courses c ON c.course_id = ce.course_id "
            "ORDER BY ce.issued_at DESC"))


# ---------------------------------------------------------------------------
# Payments / enrollment requests
# ---------------------------------------------------------------------------
def create_payment(student_id, course_id, amount, provider, status, provider_ref=None, payment_url=None):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO payments (student_id, course_id, amount, provider, provider_ref, payment_url, status,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (student_id, course_id, amount, provider, provider_ref, payment_url, status, now(), now()),
        )
        return cur.lastrowid


def set_payment_status(payment_id, status):
    with connect() as conn:
        conn.execute("UPDATE payments SET status=?, updated_at=? WHERE payment_id=?", (status, now(), payment_id))


def open_payment(student_id, course_id):
    """Most recent payment/request for this course that is still awaiting completion."""
    with connect() as conn:
        return _row(conn.execute(
            "SELECT * FROM payments WHERE student_id=? AND course_id=? AND status IN ('created', 'requested') "
            "ORDER BY payment_id DESC LIMIT 1", (student_id, course_id)))


def list_payments(status=None):
    sql = ("SELECT p.*, s.full_name, s.email, c.title AS course_title FROM payments p "
           "JOIN students s ON s.student_id = p.student_id JOIN courses c ON c.course_id = p.course_id")
    params = ()
    if status:
        sql += " WHERE p.status=?"
        params = (status,)
    sql += " ORDER BY p.payment_id DESC"
    with connect() as conn:
        return _rows(conn.execute(sql, params))


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
def stats():
    with connect() as conn:
        q = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "courses": q("SELECT COUNT(*) FROM courses"),
            "published": q("SELECT COUNT(*) FROM courses WHERE COALESCE(is_published, 1) = 1"),
            "modules": q("SELECT COUNT(*) FROM modules"),
            "students": q("SELECT COUNT(*) FROM students"),
            "enrollments": q("SELECT COUNT(*) FROM student_courses"),
            "certificates": q("SELECT COUNT(*) FROM certificates"),
            "revenue": q("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='paid'"),
            "pending_requests": q("SELECT COUNT(*) FROM payments WHERE status='requested'"),
        }


def enrollments_by_month():
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT substr(enrolled_at, 1, 7) AS month, COUNT(*) AS enrollments FROM student_courses "
            "WHERE enrolled_at IS NOT NULL GROUP BY month ORDER BY month"))


def course_performance():
    with connect() as conn:
        return _rows(conn.execute(
            """SELECT c.course_id, c.title, COALESCE(c.views, 0) AS views,
                      (SELECT COUNT(*) FROM student_courses sc WHERE sc.course_id = c.course_id) AS enrollments,
                      (SELECT COUNT(*) FROM certificates ce WHERE ce.course_id = c.course_id) AS completions,
                      (SELECT COALESCE(SUM(amount), 0) FROM payments p
                        WHERE p.course_id = c.course_id AND p.status = 'paid') AS revenue
               FROM courses c ORDER BY enrollments DESC"""))
