from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path("mark_attendance/", views.markAttendance, name="mark_attendance"),

    path("admin_page/", views.adminPage, name='admin_page'),
    path("admin/", admin.site.urls),

    # path('student_list/', views.studentList, name='student_list'),

    # path('add_student/add/', views.addStudent, name="add_student"),
    # path('view_record/<int:pk>/view/', views.viewStudentRecord, name="view_record"),
    # path('update_record/<int:pk>/edit/', views.updateStudentRecord, name="update_record"),
    # path('delete_record/<int:pk>/', views.deleteStudentRecord, name='delete_record'),



]