from django.contrib import admin
from .models import Student, Event, Session, Attendance, Penalty


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("rfid", "first_name", "last_name", "course", "year")
    search_fields = ("rfid", "first_name", "last_name", "course")


class SessionInline(admin.TabularInline):
    model = Session
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "start_datetime", "end_datetime", "penalty_amount")
    inlines = [SessionInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("event", "session_name", "start_time", "end_time")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "log_time", "status")
    list_filter = ("session__event", "session__session_name")
    search_fields = ("student__first_name", "student__last_name", "student__rfid")



@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ("attendance", "amount")
