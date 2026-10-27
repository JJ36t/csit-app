# -*- coding: utf-8 -*-
"""بيانات تجريبية كاملة مؤرخة بالوقت الحالي (تطوير/عرض فقط).

    python scripts/demo_full_seed.py            # إنشاء/إكمال بلا تكرار
    python scripts/demo_full_seed.py --reset    # حذف كل البيانات ثم البناء

ماذا يُنشئ؟
- 4 أقسام، سنة 2026–2027، فصل أول، 8 شعب (مراحل مختلفة).
- 18 مقرراً و18 عرض مادة موزّعة على 6 تدريسيين ورؤساء الأقسام.
- 48 طالباً (6 لكل شعبة) بكلمة مرور موحّدة للتجربة.
- جدول أسبوعي كامل + جلسات هذا الأسبوع حتى اليوم + حضور تاريخي واقعي.
- تقييمات منشورة ودرجات، مواد تعليمية، إعلانات، أعذار (قيد المراجعة/مقبولة)،
  وطلبات مع محادثات — كلها بتواريخ اليوم كي تبدو الشاشات «حية».

كلمة المرور الموحّدة: Test#12345 — والمدير Admin#2026.
"""
import argparse
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AbsenceExcuse,
    AcademicYear,
    Announcement,
    AnnouncementRead,
    Assessment,
    AttendanceRecord,
    AuditLog,
    Course,
    CourseOffering,
    Department,
    Device,
    Enrollment,
    FcmToken,
    Grade,
    Group,
    LectureSession,
    Material,
    Notification,
    PushOutbox,
    RefreshToken,
    Request,
    RequestMessage,
    Room,
    StoredFile,
    Student,
    Staff,
    Term,
    TimetableSlot,
    User,
)
from app.models.enums import (  # noqa: E402
    AnnouncementScope,
    AssessmentKind,
    AttendanceMethod,
    AttendanceStatus,
    EnrollmentSource,
    EnrollmentStatus,
    ExcuseStatus,
    LectureSessionStatus,
    MaterialKind,
    RequestStatus,
    SessionKind,
    StudentStatus,
    StudyType,
    UserRole,
    UserStatus,
)
from app.security import hash_password  # noqa: E402
from app.services.notifications import notify_users  # noqa: E402

PASSWORD = "Test#12345"
ADMIN_PASSWORD = "Admin#2026"
BAGHDAD = timezone(timedelta(hours=3))
RNG = random.Random(20261027)

DEPARTMENTS = [
    ("CS", "علوم الحاسوب"),
    ("IS", "نظم المعلومات"),
    ("MS", "الأنظمة الطبية"),
    ("CY", "الأمن السيبراني"),
]

COURSES = [
    # (code, name, dept, stage, kind)
    ("CS101", "مقدمة في علوم الحاسوب", "CS", 1, SessionKind.THEORY),
    ("CS102", "البرمجة المهيكلة", "CS", 1, SessionKind.THEORY),
    ("CS103", "الرياضيات المتقطعة", "CS", 1, SessionKind.THEORY),
    ("CS104", "مهارات الحاسوب العملية", "CS", 1, SessionKind.LAB),
    ("CS201", "هياكل البيانات", "CS", 2, SessionKind.THEORY),
    ("CS202", "البرمجة الكيانية", "CS", 2, SessionKind.THEORY),
    ("CS203", "قواعد البيانات", "CS", 2, SessionKind.LAB),
    ("CS301", "تحليل الخوارزميات", "CS", 3, SessionKind.THEORY),
    ("CS302", "شبكات الحاسوب", "CS", 3, SessionKind.THEORY),
    ("CS303", "نظم التشغيل", "CS", 3, SessionKind.LAB),
    ("CS401", "هندسة البرمجيات", "CS", 4, SessionKind.THEORY),
    ("CS402", "الذكاء الاصطناعي", "CS", 4, SessionKind.THEORY),
    ("IS101", "أساسيات نظم المعلومات", "IS", 1, SessionKind.THEORY),
    ("IS102", "تحليل وتصميم النظم", "IS", 2, SessionKind.THEORY),
    ("MS101", "مدخل إلى الأنظمة الطبية", "MS", 1, SessionKind.THEORY),
    ("MS102", "الأجهزة الطبية الرقمية", "MS", 2, SessionKind.LAB),
    ("CY101", "مقدمة في الأمن السيبراني", "CY", 1, SessionKind.THEORY),
    ("CY102", "التشفير وأمن الشبكات", "CY", 1, SessionKind.THEORY),
]

INSTRUCTORS = [
    ("T-101", "د. أحمد كريم التدريسي", "CS", "أستاذ مساعد"),
    ("T-102", "د. سارة عبد الحسين", "CS", "مدرس"),
    ("T-103", "د. مصطفى جواد", "IS", "مدرس"),
    ("T-104", "د. هدى علي", "MS", "أستاذ مساعد"),
    ("T-105", "د. علي ناصر", "CY", "مدرس"),
    ("T-106", "م. زينب حسن", "CS", "مساعد تدريسي"),
]

HEADS = [
    ("HEAD-CS", "أ.د. حسن عبد الأمير", "CS"),
    ("HEAD-IS", "أ.د. منى كاظم", "IS"),
    ("HEAD-MS", "أ.د. رعد سلمان", "MS"),
    ("HEAD-CY", "أ.د. إيمان فاضل", "CY"),
]

FIRST_NAMES = [
    "علي", "زينب", "محمد", "فاطمة", "حسين", "نور", "أمير", "رقية",
    "كرار", "مريم", "عباس", "هدى", "يوسف", "سجاد", "تبارك", "مصطفى",
]
LAST_NAMES = [
    "الجبوري", "الحسيني", "العبادي", "الشمري", "الزيدي", "الكعبي",
    "الطائي", "البديري", "الخفاجي", "الربيعي", "العامري", "الفاطمي",
]


def _bulk_delete(db) -> None:
    """حذف كل البيانات بالترتيب الذي يحترم المفاتيح الأجنبية (تطوير فقط)."""
    for model in (
        Grade,
        Assessment,
        AttendanceRecord,
        AbsenceExcuse,
        Material,
        Enrollment,
        LectureSession,
        TimetableSlot,
        CourseOffering,
        Course,
        Group,
        Student,
        Staff,
        RequestMessage,
        Request,
        AnnouncementRead,
        Notification,
        PushOutbox,
        Announcement,
        FcmToken,
        RefreshToken,
        Device,
        AuditLog,
        StoredFile,
        User,
        Term,
        AcademicYear,
        Department,
    ):
        db.execute(delete(model))
    db.commit()


def _get_or_create(db, model, defaults: dict | None = None, **filters):
    row = db.scalar(select(model).filter_by(**filters))
    if row is not None:
        return row, False
    row = model(**filters, **(defaults or {}))
    db.add(row)
    db.flush()
    return row, True


def _ensure_user(db, university_id: str, name: str, role: UserRole, password: str):
    row = db.scalar(select(User).where(User.university_id == university_id))
    if row is not None:
        return row, False
    row = User(
        university_id=university_id,
        full_name_ar=name,
        role=role,
        password_hash=hash_password(password, rounds=4),
        status=UserStatus.ACTIVE,
        must_change_password=False,
    )
    db.add(row)
    db.flush()
    return row, True


def _db_weekday(day: date) -> int:
    """0=الأحد … 6=السبت (اتفاق الجدول في المشروع)."""
    return (day.weekday() + 1) % 7


def build(reset: bool) -> None:
    now = datetime.now(timezone.utc)
    today = now.astimezone(BAGHDAD).date()
    counters = {key: 0 for key in ("users", "groups", "courses", "offerings", "sessions", "records", "grades")}

    with SessionLocal() as db:
        if reset:
            _bulk_delete(db)

        # --- الأقسام والسنة والفصل ---
        departments: dict[str, Department] = {}
        for code, name_ar in DEPARTMENTS:
            row, _ = _get_or_create(
                db,
                Department,
                {"name_ar": name_ar, "name_en": code},
                code=code,
            )
            departments[code] = row

        year, _ = _get_or_create(
            db, AcademicYear, {"is_current": True}, label="2026–2027"
        )
        year.is_current = True

        term = db.scalar(
            select(Term).where(Term.academic_year_id == year.id, Term.is_current.is_(True))
        )
        if term is None:
            term = Term(
                academic_year_id=year.id,
                name="الفصل الأول",
                is_current=True,
                start_date=date(2026, 10, 1),
                end_date=date(2027, 1, 31),
            )
            db.add(term)
            db.flush()
        db.commit()

        # --- الشعب ---
        groups: dict[tuple[str, int], Group] = {}
        for code in departments:
            stages = (1, 2, 3, 4) if code == "CS" else (1, 2)
            for stage in stages:
                group, _ = _get_or_create(
                    db,
                    Group,
                    {
                        "study_type": StudyType.MORNING,
                        "term_id": term.id,
                    },
                    department_id=departments[code].id,
                    stage=stage,
                    name="A",
                )
                groups[(code, stage)] = group
                counters["groups"] += 1

        # --- التدريسيون والرؤساء والمدير ---
        staff_rows: dict[str, User] = {}
        for university_id, name, dept_code, title in INSTRUCTORS:
            user, _ = _ensure_user(db, university_id, name, UserRole.INSTRUCTOR, PASSWORD)
            staff_rows[university_id] = user
            if db.get(Staff, user.id) is None:
                db.add(
                    Staff(
                        user_id=user.id,
                        department_id=departments[dept_code].id,
                        academic_title=title,
                        office=f"مبنى الحاسوب — {dept_code}-201",
                    )
                )
            counters["users"] += 1

        for university_id, name, dept_code in HEADS:
            user, _ = _ensure_user(db, university_id, name, UserRole.DEPARTMENT_HEAD, PASSWORD)
            staff_rows[university_id] = user
            if db.get(Staff, user.id) is None:
                db.add(
                    Staff(
                        user_id=user.id,
                        department_id=departments[dept_code].id,
                        academic_title="أستاذ دكتور",
                    )
                )
            counters["users"] += 1

        _ensure_user(db, "ADMIN-001", "مدير الكلية", UserRole.COLLEGE_ADMIN, ADMIN_PASSWORD)

        # --- الطلبة: 6 لكل شعبة ---
        students: dict[tuple[str, int], list[User]] = {}
        for (dept_code, stage), group in groups.items():
            roster: list[User] = []
            for index in range(1, 7):
                university_id = f"S-{dept_code}{stage}-{index:02d}"
                name = f"{RNG.choice(FIRST_NAMES)} {RNG.choice(LAST_NAMES)}"
                user, _ = _ensure_user(db, university_id, name, UserRole.STUDENT, PASSWORD)
                if db.get(Student, user.id) is None:
                    db.add(
                        Student(
                            user_id=user.id,
                            department_id=departments[dept_code].id,
                            stage=stage,
                            study_type=StudyType.MORNING,
                            group_id=group.id,
                            enrollment_year=2026 - (stage - 1),
                            status=StudentStatus.ACTIVE,
                        )
                    )
                roster.append(user)
                counters["users"] += 1
            students[(dept_code, stage)] = roster

        # --- المقررات وعروضها ---
        rooms = []
        for name, lat, lng, radius in (
            ("قاعة 101", 31.9901, 44.9201, 120),
            ("قاعة 102", 31.9902, 44.9204, 120),
            ("قاعة 203", 31.9905, 44.9202, 100),
            ("مختبر 201", 31.9907, 44.9208, 80),
            ("مختبر 202", 31.9908, 44.9210, 80),
            ("قاعة المؤتمرات", 31.9899, 44.9195, 150),
        ):
            room, _ = _get_or_create(
                db,
                Room,
                {"lat": lat, "lng": lng, "radius_m": radius, "building": "مبنى علوم الحاسوب"},
                name=name,
            )
            rooms.append(room)

        offerings: dict[str, CourseOffering] = {}
        slot_counter: dict[str, int] = {}
        today_wd = _db_weekday(today)
        bands = [time(8, 30), time(10, 0), time(11, 30)]
        instructor_ids = list(staff_rows.values())

        for index, (code, name_ar, dept_code, stage, kind) in enumerate(COURSES):
            course, _ = _get_or_create(
                db,
                Course,
                {
                    "name_ar": name_ar,
                    "department_id": departments[dept_code].id,
                    "stage": stage,
                    "units": 3,
                    "kind": kind,
                },
                code=code,
            )
            counters["courses"] += 1
            group = groups[(dept_code, stage)]
            instructor = instructor_ids[index % len(instructor_ids)]
            if instructor.role not in (UserRole.INSTRUCTOR, UserRole.DEPARTMENT_HEAD):
                instructor = staff_rows["T-101"]
            offering, _ = _get_or_create(
                db,
                CourseOffering,
                {
                    "instructor_id": instructor.id,
                    "session_kind": kind,
                },
                course_id=course.id,
                term_id=term.id,
                group_id=group.id,
            )
            offerings[code] = offering
            counters["offerings"] += 1
            # إن كان العرض موجوداً من تشغيل سابق (أو من demo_seed المصغّر) نُثبّت
            # التدريسي المختار كي تتطابق الأعذار والتقارير مع حساب العرض.
            if offering.instructor_id != instructor.id:
                offering.instructor_id = instructor.id

            # تسجيل الطلبة (تلقائي)
            for student_user in students[(dept_code, stage)]:
                exists = db.scalar(
                    select(Enrollment).where(
                        Enrollment.student_id == student_user.id,
                        Enrollment.offering_id == offering.id,
                    )
                )
                if exists is None:
                    db.add(
                        Enrollment(
                            student_id=student_user.id,
                            offering_id=offering.id,
                            source=EnrollmentSource.AUTO,
                            status=EnrollmentStatus.ACTIVE,
                        )
                    )

            # حصة أسبوعية: توزيع بلا تعارض داخل الشعبة
            group_key = str(group.id)
            slot_index = slot_counter.get(group_key, 0)
            slot_counter[group_key] = slot_index + 1
            # أول حصة لكل شعبة اليوم (للعرض الحي)، وما بعدها في أيام سابقة
            weekday = (today_wd - slot_index) % 5
            start_time = bands[slot_index % len(bands)]
            if db.scalar(select(TimetableSlot).where(TimetableSlot.offering_id == offering.id)) is None:
                db.add(
                    TimetableSlot(
                        offering_id=offering.id,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=time(start_time.hour + 1, 30),
                        room_id=rooms[index % len(rooms)].id,
                        kind=kind,
                    )
                )

        db.commit()

        # --- جلسات هذا الأسبوع حتى اليوم + الحضور ---
        week_start = today - timedelta(days=_db_weekday(today))
        for offset in range(_db_weekday(today) + 1):
            session_date = week_start + timedelta(days=offset)
            weekday = _db_weekday(session_date)
            day_slots = list(
                db.scalars(select(TimetableSlot).where(TimetableSlot.weekday == weekday))
            )
            for slot in day_slots:
                offering = db.get(CourseOffering, slot.offering_id)
                if offering is None:
                    continue
                exists = db.scalar(
                    select(LectureSession).where(
                        LectureSession.offering_id == offering.id,
                        LectureSession.date == session_date,
                    )
                )
                if exists is not None:
                    continue

                starts_local = datetime.combine(session_date, slot.start_time, tzinfo=BAGHDAD)
                starts = starts_local.astimezone(timezone.utc)
                ends = starts + timedelta(minutes=90)
                is_today = session_date == today
                if is_today:
                    # جلسة اليوم تبدأ قبل الآن بقليل كي تُفتح وتُمسح في العرض
                    starts = now - timedelta(minutes=5)
                    ends = starts + timedelta(minutes=90)
                status = (
                    LectureSessionStatus.SCHEDULED
                    if is_today
                    else LectureSessionStatus.CLOSED
                )
                session = LectureSession(
                    offering_id=offering.id,
                    slot_id=slot.id,
                    date=session_date,
                    starts_at=starts,
                    ends_at=ends,
                    status=status,
                    window_s=20,
                )
                db.add(session)
                db.flush()
                counters["sessions"] += 1

                if not is_today:
                    roster = list(
                        db.scalars(
                            select(Enrollment.student_id).where(
                                Enrollment.offering_id == offering.id,
                                Enrollment.status == EnrollmentStatus.ACTIVE,
                            )
                        )
                    )
                    for student_id in roster:
                        roll = RNG.random()
                        if roll < 0.78:
                            status_value, method = AttendanceStatus.PRESENT, AttendanceMethod.QR
                        elif roll < 0.9:
                            status_value, method = AttendanceStatus.LATE, AttendanceMethod.QR
                        else:
                            status_value, method = AttendanceStatus.ABSENT, AttendanceMethod.MANUAL
                        db.add(
                            AttendanceRecord(
                                session_id=session.id,
                                student_id=student_id,
                                status=status_value,
                                method=method,
                                scanned_at=starts + timedelta(minutes=RNG.randint(0, 12)),
                                flag_reason=None,
                            )
                        )
                        counters["records"] += 1
        db.commit()

        # --- تقييمات ودرجات منشورة ---
        for code in ("CS101", "CS102", "CS201", "IS101"):
            offering = offerings.get(code)
            if offering is None:
                continue
            for name, kind, max_score, weight, publish in (
                ("كوز أول", AssessmentKind.QUIZ, 10, 10, True),
                ("الواجب العملي", AssessmentKind.LAB, 10, 10, True),
                ("الامتحان النصفي", AssessmentKind.MIDTERM, 40, 30, True),
                ("الامتحان النهائي", AssessmentKind.FINAL, 50, 50, False),
            ):
                assessment, created = _get_or_create(
                    db,
                    Assessment,
                    {"weight": weight, "is_published": publish},
                    offering_id=offering.id,
                    name=name,
                    kind=kind,
                    max_score=max_score,
                )
                if not created or not publish:
                    continue
                roster = list(
                    db.scalars(
                        select(Enrollment.student_id).where(
                            Enrollment.offering_id == offering.id,
                            Enrollment.status == EnrollmentStatus.ACTIVE,
                        )
                    )
                )
                for student_id in roster:
                    score = round(float(max_score) * RNG.uniform(0.55, 0.98), 1)
                    db.add(
                        Grade(
                            assessment_id=assessment.id,
                            student_id=student_id,
                            score=score,
                            entered_by=offering.instructor_id,
                        )
                    )
                    counters["grades"] += 1
        db.commit()

        # --- مواد تعليمية ---
        for code, offering in offerings.items():
            for week in (1, 2, 3):
                _get_or_create(
                    db,
                    Material,
                    {
                        "kind": MaterialKind.LINK,
                        "url": f"https://example.edu/csit/{code.lower()}/week{week}.pdf",
                        "is_published": True,
                    },
                    offering_id=offering.id,
                    title=f"{code} — محاضرة الأسبوع {week}",
                    week_no=week,
                )
        db.commit()

        # --- إعلانات ---
        admin = db.scalar(select(User).where(User.university_id == "ADMIN-001"))
        cs_head = staff_rows["HEAD-CS"]
        announcements = [
            (AnnouncementScope.COLLEGE, None, None, "بدء المحاضرات — الفصل الأول",
             "تنتظم المحاضرات اعتباراً من يوم الأحد. يُرجى من الطلبة الالتزام بالجدول المعروض في التطبيق.", True),
            (AnnouncementScope.COLLEGE, None, None, "حملة توعية أمن المعلومات",
             "يقيم قسم الأمن السيبراني ورشة مجانية عن حماية الحسابات الجامعية يوم الخميس في قاعة المؤتمرات.", False),
            (AnnouncementScope.DEPARTMENT, departments["CS"].id, None, "اجتماع طلبة المرحلة الأولى",
             "اجتماع إرشادي لطلبة المرحلة الأولى مع رئيس القسم يوم الثلاثاء الساعة 11:00.", False),
            (AnnouncementScope.STAGE, departments["CS"].id, 1, "تغيير موعد مختبر الحاسوب",
             "نُقل مختبر الحاسوب لطلبة المرحلة الأولى إلى مختبر 202 بدءاً من هذا الأسبوع.", False),
        ]
        for scope, scope_id, stage, title, body, pinned in announcements:
            row, created = _get_or_create(
                db,
                Announcement,
                {
                    "scope": scope,
                    "scope_id": scope_id,
                    "stage": stage,
                    "body": body,
                    "pinned": pinned,
                    "created_by": admin.id,
                },
                title=title,
            )
            if created:
                # محاكاة توزيع الإشعارات الذي يفعله الـAPI عند النشر
                audience = [
                    user.id
                    for user in db.scalars(
                        select(User).where(
                            User.role == UserRole.STUDENT,
                            User.status == UserStatus.ACTIVE,
                            User.deleted_at.is_(None),
                        )
                    )
                ]
                notify_users(
                    db,
                    audience,
                    type_="announcement",
                    title=title,
                    body=body[:200],
                    data={"announcement_id": str(row.id), "scope": scope.value},
                )
        # إعلان مادة على CS101
        _get_or_create(
            db,
            Announcement,
            {
                "scope": AnnouncementScope.OFFERING,
                "scope_id": offerings["CS101"].id,
                "body": "الامتحان النصفي يوم الأحد القادم في قاعة 101، ويشمل الفصول 1–4.",
                "created_by": staff_rows["T-101"].id,
            },
            title="موعد الامتحان النصفي",
        )
        db.commit()

        # --- أعذار: معلّق ومقبول ---
        cs_students = students[("CS", 1)]
        closed_sessions = list(
            db.scalars(
                select(LectureSession)
                .where(
                    LectureSession.offering_id == offerings["CS101"].id,
                    LectureSession.status == LectureSessionStatus.CLOSED,
                )
                .order_by(LectureSession.date.desc())
            )
        )
        if not closed_sessions:
            # محاضرة سابقة إضافية لـCS101 كي توجد أعذار قابلة للمراجعة
            past_date = today - timedelta(days=7)
            past_start = datetime.combine(past_date, time(10, 0), tzinfo=BAGHDAD).astimezone(
                timezone.utc
            )
            past_session = LectureSession(
                offering_id=offerings["CS101"].id,
                date=past_date,
                starts_at=past_start,
                ends_at=past_start + timedelta(minutes=90),
                status=LectureSessionStatus.CLOSED,
                window_s=20,
            )
            db.add(past_session)
            db.flush()
            closed_sessions = [past_session]
        if closed_sessions and cs_students:
            target_session = closed_sessions[0]
            for index, student_user in enumerate(cs_students[:2]):
                record = db.scalar(
                    select(AttendanceRecord).where(
                        AttendanceRecord.session_id == target_session.id,
                        AttendanceRecord.student_id == student_user.id,
                    )
                )
                approved = index == 1
                if record is None:
                    record = AttendanceRecord(
                        session_id=target_session.id,
                        student_id=student_user.id,
                        status=AttendanceStatus.ABSENT,
                        method=AttendanceMethod.MANUAL,
                    )
                    db.add(record)
                    db.flush()
                if approved:
                    record.status = AttendanceStatus.EXCUSED
                _get_or_create(
                    db,
                    AbsenceExcuse,
                    {
                        "reason": "تقرير طبي مرفق يوضح عدم القدرة على الحضور.",
                        "status": ExcuseStatus.APPROVED if approved else ExcuseStatus.PENDING,
                        "reviewed_by": staff_rows["T-101"].id if approved else None,
                        "reviewed_at": now - timedelta(days=1) if approved else None,
                        "review_note": "عذر مقبول — تم تحديث سجل الحضور." if approved else None,
                    },
                    student_id=student_user.id,
                    session_id=target_session.id,
                )
        db.commit()

        # --- طلبات ومحادثات ---
        cs_head_row = db.get(User, cs_head.id)
        sample_requests = [
            ("academic", "طلب تأجيل الامتحان النصفي", "أرجو تأجيل الامتحان بسبب ظرف عائلي طارئ.",
             RequestStatus.IN_PROGRESS, "تم تحويل الطلب إلى لجنة الاختبارات، وسيصلك القرار خلال يومين."),
            ("documents", "تأييد استمرار بالدراسة", "أحتاج تأييداً بالاستمرار بالدراسة لتقديمه إلى دائرة أخرى.",
             RequestStatus.RESOLVED, "التأييد جاهز في مكتب القسم، يمكنك استلامه يوم الأحد."),
            ("grades", "مراجعة درجة الكوز الأول", "أرى أن درجتي في الكوز الأول أقل من المتوقع.",
             RequestStatus.OPEN, None),
        ]
        for index, (category, subject, body, status, reply) in enumerate(sample_requests):
            student_user = cs_students[index % len(cs_students)]
            existing = db.scalar(
                select(Request).where(Request.student_id == student_user.id, Request.subject == subject)
            )
            if existing is not None:
                continue
            row = Request(
                student_id=student_user.id,
                department_id=departments["CS"].id,
                category=category,
                subject=subject,
                status=status,
                assigned_to=staff_rows["T-101"].id if status != RequestStatus.OPEN else None,
            )
            db.add(row)
            db.flush()
            db.add(RequestMessage(request_id=row.id, sender_id=student_user.id, body=body))
            if reply:
                db.add(
                    RequestMessage(
                        request_id=row.id, sender_id=cs_head_row.id, body=reply
                    )
                )
        db.commit()

        # إشعارات ترحيبية لمن لم يستلم شيئاً بعد
        if db.scalar(select(Notification).limit(1)) is None:  # pragma: no cover - حالة نادرة
            for student_user in cs_students[:3]:
                db.add(
                    Notification(
                        user_id=student_user.id,
                        type="welcome",
                        title="أهلاً بك في تطبيق الكلية",
                        body="جدولك وموادك ودرجاتك أصبحت في مكان واحد.",
                        data={},
                    )
                )
            db.commit()

        # أرقام نهائية
        totals = {
            "المستخدمون": _count(db, User),
            "الشعب": _count(db, Group),
            "المقررات": _count(db, Course),
            "عروض المواد": _count(db, CourseOffering),
            "الجلسات": _count(db, LectureSession),
            "سجلات الحضور": _count(db, AttendanceRecord),
            "الدرجات": _count(db, Grade),
            "المواد": _count(db, Material),
            "الأعذار": _count(db, AbsenceExcuse),
            "الإشعارات": _count(db, Notification),
            "الإعلانات": _count(db, Announcement),
            "الطلبات": _count(db, Request),
        }

    print("تم تجهيز بيانات العرض الكاملة (مؤرخة اليوم):")
    for key, value in totals.items():
        print(f"  {key}: {value}")
    print("\nحسابات الدخول:")
    print(f"  مدير الكلية:      ADMIN-001 / {ADMIN_PASSWORD}")
    print(f"  رئيس قسم CS:      HEAD-CS    / {PASSWORD}")
    print(f"  تدريسي:           T-101      / {PASSWORD}")
    print(f"  طالب مرحلة أولى:  S-CS1-01   / {PASSWORD}")
    print(f"  طالب مرحلة ثانية: S-CS2-01   / {PASSWORD}")
    print("\nملاحظة: أول دخول يربط الجهاز؛ لتغيير الجهاز:")
    print("  python scripts/dev_reset_devices.py S-CS1-01")


def _count(db, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="بيانات تجريبية كاملة للتطبيق")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="حذف كل البيانات قبل البناء (تطوير فقط؛ يتطلب --force على PostgreSQL)",
    )
    parser.add_argument("--force", action="store_true", help="تأكيد الحذف على قاعدة غير SQLite")
    args = parser.parse_args()

    from app.config import settings

    if args.reset and not settings.database_url.startswith("sqlite") and not args.force:
        raise SystemExit("قاعدة غير SQLite: أضف --force لتأكيد حذف كل البيانات")

    build(reset=args.reset)


if __name__ == "__main__":
    main()
