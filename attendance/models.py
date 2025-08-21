from django.db import models
from datetime import timedelta, datetime, time
from django.utils import timezone
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP

class Student(models.Model):
    BSCS = "BSCS"
    BSIS = "BSIS"
    BLIS = "BLIS"

    COURSE_CHOICES = [
        (BSCS, "BSCS"),
        (BSIS, "BSIS"),
        (BLIS, "BLIS"),
    ]
    
    rfid = models.CharField(max_length=50, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Event(models.Model):
    name = models.CharField(max_length=200)
    start_datetime = models.DateTimeField(default=timezone.now)  # start date and time
    end_datetime = models.DateTimeField(default=timezone.now)
    penalty_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    flat_rate = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)  
    per_minute_penalty = models.DecimalField(max_digits=6, decimal_places=2, default=0.50)

    def __str__(self):
        return f"{self.name} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"


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

    def get_start_datetime(self):
        return timezone.make_aware(
            datetime.datetime.combine(self.event.start_datetime.date(), self.start_time)
    )

    def get_end_datetime(self):
        return timezone.make_aware(
            datetime.datetime.combine(self.event.start_datetime.date(), self.end_time)
        )
    
    @property
    def grace_end_time(self):
        # Combine event date and session end_time
        end_dt = datetime.datetime.combine(self.event.start_datetime.date(), self.end_time)
        # Add grace period
        end_dt += timedelta(minutes=self.grace_period)
        # Make timezone-aware (optional, if you need)
        end_dt = timezone.make_aware(end_dt)
        # Return just the time portion
        return end_dt.time()

    def __str__(self):
        return f"{self.event.name} - {self.session_name} ({self.start_time} - {self.end_time})"


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

    def calculate_status_and_penalty(self):
        now = self.log_time
        session_start = self.session.get_start_datetime()
        session_end = self.session.get_end_datetime()
        grace_end = session_end + timedelta(minutes=self.session.grace_period)

        flat_rate = self.session.event.flat_rate
        per_minute_penalty = self.session.event.per_minute_penalty
        absent_penalty = float(self.session.event.penalty_amount)

        if session_start <= now <= session_end:
            self.status = "Present"
            penalty = Decimal("0.00")
        elif session_end < now <= grace_end:
            self.status = "Late"
            late_minutes = Decimal((now - session_end).total_seconds() // 60)
            penalty = flat_rate + (late_minutes * per_minute_penalty)
        else:
            self.status = "Absent"
            penalty = absent_penalty

        return penalty

class Penalty(models.Model):
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        # Auto-compute penalty before saving
        if self.attendance:
            self.amount = self.attendance.calculate_status_and_penalty()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attendance} - Penalty: {self.amount}"

# Signal to auto-create/update penalty when attendance is saved
@receiver(post_save, sender=Attendance)
def create_or_update_penalty(sender, instance, created, **kwargs):
    # Only for Late or Absent
    if instance.status in ["Late", "Absent"]:
        Penalty.objects.update_or_create(
            attendance=instance,
            defaults={"amount": instance.calculate_status_and_penalty()}
        )