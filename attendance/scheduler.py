import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from .models import Attendance, Session, Student


def mark_absent_students():
    now = datetime.datetime.now()
    sessions = Session.objects.filter(is_closed=False)

    print(f"[SCHEDULER] Checking at {now}, found {sessions.count()} sessions")

    for session in sessions:
        session_end = session.grace_end_datetime  # ✅ safe helper from model

        print(f"[SESSION] {session.id} - Grace end at {session_end}")

        # Only process sessions that already ended
        if now > session_end:
            students_in_event = Student.objects.values_list("id", flat=True)

            for student_id in students_in_event:
                # Skip students who already have attendance
                if Attendance.objects.filter(student_id=student_id, session=session).exists():
                    continue

                Attendance.objects.create(
                    student_id=student_id,
                    session=session,
                    status="Absent"
                )
                print(f"[ABSENT MARKED] Student {student_id} in session {session.id}")

            # ✅ Mark session as closed to avoid reprocessing
            session.is_closed = True
            session.save(update_fields=["is_closed"])
            print(f"[SESSION CLOSED] {session.id}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(mark_absent_students, "interval", minutes=1)  # run every 1 min
    scheduler.start()
