from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ObjectDoesNotExist

import json

from .models import *
from .forms import *

# Create your views here.
def home(request):
    now = timezone.localtime()

    # Get all events today (or could filter for future events if desired)
    events_today = Event.objects.filter(
        start_datetime__date=now.date()
    ).order_by("start_datetime")

    event = None
    session = None
    session_status = None

    for ev in events_today:
        sessions = Session.objects.filter(event=ev).order_by("start_time")
        for s in sessions:
            # Convert session start/end into timezone-aware datetimes
            start_dt = timezone.make_aware(datetime.datetime.combine(ev.start_datetime.date(), s.start_time))
            end_dt = timezone.make_aware(datetime.datetime.combine(ev.start_datetime.date(), s.end_time))
            grace_end = end_dt + timedelta(minutes=s.grace_period)

            if start_dt <= now <= grace_end:
                # Found active session
                event = ev
                session = s
                session_status = "active"
                break
        if session:
            break

    if not session and events_today.exists():
        # No active session found, get the next upcoming session
        for ev in events_today:
            upcoming_sessions = Session.objects.filter(
                event=ev,
                start_time__gt=now.time()
            ).order_by("start_time")
            if upcoming_sessions.exists():
                event = ev
                session = upcoming_sessions.first()
                session_status = "upcoming"
                break

    # print("Now date:", now.date())
    # print("Now time:", now.time())
    # print("Event today:", event)
    # print("Session found:", session, "| Status:", session_status)
    # print("Events today:", Event.objects.filter(start_datetime=now.date()))
    # print("Sessions for event:", Session.objects.filter(event=event))

    context = {
        "event": event,
        "session": session,
        "session_status": session_status
    }

    return render(request, "attendance/student_attendance.html", context)


@csrf_exempt
def markAttendance(request):
    if request.method == "POST":
        data = json.loads(request.body)
        rfid = data.get("rfid")

        try:
            student = Student.objects.get(rfid=rfid)
            now = timezone.localtime(timezone.now())

            # Find event that is currently active or started earlier today
            event = Event.objects.filter(
                start_datetime__lte=now, 
                end_datetime__gte=now
            ).order_by("start_datetime").first()

            if not event:
                return JsonResponse({"success": False, "message": "❌ No active event found."})

            # Get the latest session for that event
            session = Session.objects.filter(event=event).order_by('-start_time').first()

            if not session:
                return JsonResponse({
                    "success": False,
                    "message": "❌ No active session found.",
                    "note": f"-----"
                })

            # Apply grace period
            session_start = timezone.make_aware(
                timezone.datetime.combine(event.start_datetime, session.start_time),
                timezone.get_current_timezone()
            )
            session_end = timezone.make_aware(
                timezone.datetime.combine(event.start_datetime, session.end_time),
                timezone.get_current_timezone()
            )

            # Add grace period to end time
            session_end_with_grace = session_end + timedelta(minutes=session.grace_period)

            if not (session_start <= now <= session_end_with_grace):
                return JsonResponse({
                    "success": False,
                    "message": "❌ Session is not active (outside allowed time).",
                    "note": f"-----"
                })

            # Prevent duplicate attendance
            existing = Attendance.objects.filter(student=student, session=session).first()
            if existing:
                # Get penalty safely
                try:
                    penalty_amount = existing.penalty.amount
                except ObjectDoesNotExist:
                    penalty_amount = Decimal("0.00")
                
                penalty_display = penalty_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # Get status
                attendance_status = existing.status

                return JsonResponse({
                    "success": False,
                    "message": f"⚠️ {student.last_name}, {student.first_name} {student.course} {student.year} already logged in for this session.",
                    "note": f"Status: {attendance_status} | Penalty: ₱{penalty_display}"
                })
            
            # Save attendance with status (Present or Late)
            status = "Present"
            if now > session_end:
                status = "Late"

            # Save attendance (signal will auto-create penalty)
            attendance = Attendance.objects.create(student=student, session=session, status=status)

            # Safely fetch penalty
            try:
                penalty_amount = attendance.penalty.amount
            except ObjectDoesNotExist:
                penalty_amount = Decimal("0.00")

            penalty_display = penalty_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            return JsonResponse({
                "success": True,
                "message": f"✅ {student.last_name}, {student.first_name} ({student.course} {student.year}) - Attendance Recorded",
                "note": f"Status: {attendance.status} | Penalty: ₱{penalty_display}"
            })

        except Student.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "❌ RFID not recognized. Please try again.",
                "note": f"-----"
            })

def adminPage(request):
    return render(request, 'attendance/admin_page.html')



# def studentList(request):
#     students = Student.objects.all()

#     context = {'students': students}

#     return render(request, 'attendance/student.html', context)

# def addStudent(request):
#     student_form = StudentForm()

#     if request.method == "POST":
#         student_form = StudentForm(request.POST)

#         if student_form.is_valid():
#             student = student_form.save(commit=False)
#             student.save()

#             # return redirect(f"{reverse('student_list')}?msg=success")
#             return redirect('student_list')
#         else:
#             print("Add student - student_form errors:", student_form.errors)

#     else:
#         student_form = StudentForm()

#     context = {'student_form': student_form, 'readonly': False, "is_add": True}

#     return render(request, "attendance/student_form.html", context)