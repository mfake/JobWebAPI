from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User, Job, Application
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, JobSerializer, ApplicationSerializer
from django.conf import settings

# --- Signup View ---
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        user_type = request.data.get('user_type')
        if not all([name, email, password, user_type]):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email, email=email, password=password, user_type=user_type)
        user.first_name = name
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'created',
            'user_id': user.id,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

# --- Sign In View ---
class SigninView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not all([email, password]):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'logged_in',
            'user_id': user.id,
            'name': user.first_name,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

# --- JWT Logout View ---
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Try to get the refresh token from both JSON and form data
        refresh_token = request.data.get('refresh') or request.POST.get('refresh')
        if not refresh_token or not isinstance(refresh_token, str):
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token.strip())
            # Check if blacklist app is installed
            if hasattr(token, "blacklist"):
                token.blacklist()
                return Response({"status": "logged_out"}, status=status.HTTP_205_RESET_CONTENT)
            else:
                return Response({"error": "Token blacklisting not enabled. Add 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS."}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            return Response({"error": f"Invalid refresh token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

# --- Job List ---
class JobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

# --- Post Job ---
class PostJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'recruiter':
            return Response({'error': 'Only recruiters can post jobs'}, status=status.HTTP_403_FORBIDDEN)
        title = request.data.get('title')
        description = request.data.get('description')
        if not title or not description:
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
        job = Job.objects.create(title=title, description=description, posted_by=request.user)
        return Response({'status': 'job_posted', 'job_id': job.id})

# --- Apply to Job ---
class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.user_type != 'candidate':
            return Response({'error': 'Only candidates can apply'}, status=status.HTTP_403_FORBIDDEN)
        job = get_object_or_404(Job, id=job_id)
        application, created = Application.objects.get_or_create(candidate=request.user, job=job)
        if not created:
            return Response({'status': 'already_applied'})

        # Email to candidate
        subject_candidate = f"Application Submitted: {job.title}"
        message_candidate = (
            f"Dear {request.user.first_name},\n\n"
            f"You have successfully applied to the job '{job.title}'.\n\n"
            f"Job Description:\n{job.description}\n\n"
            f"Recruiter: {job.posted_by.first_name or job.posted_by.username}\n"
            f"Thank you for using our platform.\n\n"
            f"Best regards,\nJob Portal Team"
        )
        send_mail(
            subject_candidate,
            message_candidate,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )

        # Email to recruiter
        subject_recruiter = f"You have received a new application for '{job.title}'"
        message_recruiter = (
            f"Dear {job.posted_by.first_name or job.posted_by.username},\n\n"
            f"You have received a new application for your job posting '{job.title}'.\n\n"
            f"Candidate: {request.user.first_name} ({request.user.email})\n"
            f"Thank you for using our platform.\n\n"
            f"Best regards,\nJob Portal Team"
        )
        send_mail(
            subject_recruiter,
            message_recruiter,
            settings.DEFAULT_FROM_EMAIL,
            [job.posted_by.email],
            fail_silently=True,
        )

        return Response({'status': 'applied'})

# --- My Applications ---
class MyApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type != 'candidate':
            return Response({'error': 'Only candidates can view this'}, status=status.HTTP_403_FORBIDDEN)
        apps = Application.objects.filter(candidate=request.user).select_related('job')
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)

# --- Job Applicants ---
class JobApplicantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        if request.user.user_type != 'recruiter':
            return Response({'error': 'Only recruiters can view this'}, status=status.HTTP_403_FORBIDDEN)
        job = get_object_or_404(Job, id=job_id, posted_by=request.user)
        apps = Application.objects.filter(job=job).select_related('candidate')
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)
