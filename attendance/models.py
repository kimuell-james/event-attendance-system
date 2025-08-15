from django.db import models


class Student(models.Model):
    rfid = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.date})"


class Session(models.Model):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    CUSTOM = "Custom"

    SESSION_CHOICES = [
        (MORNING, "Morning"),
        (AFTERNOON, "Afternoon"),
        (CUSTOM, "Custom"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    session_name = models.CharField(max_length=100, choices=SESSION_CHOICES, default=CUSTOM)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.event.name} - {self.session_name} ({self.start_time} to {self.end_time})"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'session')  # Avoid duplicate entries

    def __str__(self):
        return f"{self.student} - {self.session}"


class Penalty(models.Model):
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.attendance} - Penalty: {self.amount}"
