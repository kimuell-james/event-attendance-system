from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta, datetime, time

import json

from .models import *
from .forms import *

# Create your views here.
def home(request):
    now = timezone.localtime()

    # Get today's event
    event = Event.objects.filter(date=now.date()).first()

    session = None
    session_status = None  # track if it's upcoming or active

    if event:
        now_time = now.time()

        # Check for an active session (consider grace period after end)
        sessions = Session.objects.filter(event=event)

        for s in sessions:
            # Combine today's date + session times into full datetimes
            start_dt = timezone.make_aware(datetime.datetime.combine(event.date, s.start_time))
            end_dt = timezone.make_aware(datetime.datetime.combine(event.date, s.end_time))
            grace_end = end_dt + timedelta(minutes=s.grace_period)

            if start_dt <= now <= grace_end:  
                session = s
                session_status = "active"
                break

        if not session:
            # Check for next upcoming session
            session = Session.objects.filter(
                event=event,
                start_time__gt=now_time
            ).order_by("start_time").first()

            if session:
                session_status = "upcoming"

    # print("Now date:", now.date())
    # print("Now time:", now.time())
    # print("Event today:", event)
    # print("Session found:", session, "| Status:", session_status)
    # print("Events today:", Event.objects.filter(date=now.date()))
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

            # Get the latest event (today or latest by date)
            event = Event.objects.order_by('-date').first()

            # Get the latest session for that event
            session = Session.objects.filter(event=event).order_by('-start_time').first()

            if not session:
                return JsonResponse({
                    "success": False,
                    "message": "❌ No active session found."
                })

            now = timezone.localtime(timezone.now())

            # Apply grace period
            session_start = timezone.make_aware(
                timezone.datetime.combine(event.date, session.start_time),
                timezone.get_current_timezone()
            )
            session_end = timezone.make_aware(
                timezone.datetime.combine(event.date, session.end_time),
                timezone.get_current_timezone()
            )

            # Add grace period to end time
            session_end_with_grace = session_end + timedelta(minutes=session.grace_period)

            if not (session_start <= now <= session_end_with_grace):
                return JsonResponse({
                    "success": False,
                    "message": "❌ Session is not active (outside allowed time)."
                })

            # Prevent duplicate attendance
            existing = Attendance.objects.filter(student=student, session=session).first()
            if existing:
                return JsonResponse({
                    "success": False,
                    "message": f"⚠️ {student.last_name}, {student.first_name} already logged in for this session."
                })
            
            # Save attendance with status (Present or Late)
            status = "Present"
            if now > session_end:
                status = "Late"

            # Save attendance
            Attendance.objects.create(student=student, session=session, status=status)

            return JsonResponse({
                "success": True,
                "message": f"✅ {student.last_name}, {student.first_name} ({student.course} {student.year}) - Attendance Recorded"
            })

        except Student.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "❌ RFID not recognized. Please try again."
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