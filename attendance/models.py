from django.db import models
from datetime import timedelta, datetime, time
from django.utils import timezone
import datetime


class Student(models.Model):
    BSCS = "BSCS"
    BSIS = "BSIS"
    BLIS = "BLIS"

    COURSE_CHOICES = [
        (BSCS, "BSCS"),
        (BSIS, "BSIS"),
        (BLIS, "BLIS"),
    ]
    
    rfid = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    penalty_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.date})"


class Session(models.Model):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CUSTOM = "Custom"

    SESSION_CHOICES = [
        (LOGIN, "LOGIN"),
        (LOGOUT, "LOGOUT"),
        (CUSTOM, "Custom"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    session_name = models.CharField(max_length=100, choices=SESSION_CHOICES, default=CUSTOM)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period = models.IntegerField(default=30)  # in minutes

    def __str__(self):
        return f"{self.event.name} - {self.session_name} ({self.start_time} to {self.end_time})"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    log_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=[("Present", "Present"), ("Late", "Late"), ("Absent", "Absent")],
        default="Present"
    )

    class Meta:
        unique_together = ('student', 'session')  # one attendance record per student per session

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"

    def calculate_penalty(self):
        if not self.log_time:
            return self.session.event.penalty_amount or 0

        # Create session start datetime (naive)
        session_start = datetime.datetime.combine(
            self.log_time.date(),
            self.session.start_time
        )

        # Make it timezone-aware to match self.log_time
        if timezone.is_naive(session_start):
            session_start = timezone.make_aware(session_start, timezone.get_current_timezone())

        grace_end = session_start + timedelta(minutes=self.session.grace_period)
        max_penalty = float(self.session.event.penalty_amount or 0)

        if self.log_time <= session_start:
            return 0
        elif self.log_time <= grace_end:
            delay = (self.log_time - session_start).total_seconds()
            grace_period_seconds = self.session.grace_period * 60
            penalty_fraction = delay / grace_period_seconds
            return round(max_penalty * penalty_fraction, 2)
        else:
            return max_penalty  # Beyond grace → full penalty

class Penalty(models.Model):
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        # Auto-compute penalty before saving
        if self.attendance:
            self.amount = self.attendance.calculate_penalty()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attendance} - Penalty: {self.amount}"
