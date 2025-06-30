from django.urls import path
from .views import (
    SignupView, SigninView, LogoutView,
    JobListView, PostJobView, ApplyJobView,
    MyApplicationsView, JobApplicantsView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('jobs/post/', PostJobView.as_view(), name='post-job'),
    path('jobs/<int:job_id>/apply/', ApplyJobView.as_view(), name='apply-job'),
    path('applications/', MyApplicationsView.as_view(), name='my-applications'),
    path('jobs/<int:job_id>/applicants/', JobApplicantsView.as_view(), name='job-applicants'),
]
