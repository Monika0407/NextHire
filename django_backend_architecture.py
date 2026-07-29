"""
NextHire – Smart Placement & Recruitment Platform
Complete Django + MySQL Backend Architecture & RBAC System Core

This file outlines the production-ready models, views, and permission systems 
for the NextHire application, designed in compliance with Django Rest Framework (DRF) 
and MySQL schema models.
"""

import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

# ==========================================
# 1. USER MANAGER & DATABASE ROLES DEFINITIONS (RBAC)
# ==========================================

class NextHireUserManager(BaseUserManager):
    """
    Custom user manager supporting robust generation of Student,
    Recruiter, and Platform Administrator profiles.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Contact Email must be defined'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class NextHireUser(AbstractUser):
    """
    Unified User model supporting three explicit roles:
    1. Admin
    2. Recruiter
    3. Student
    """
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('recruiter', 'Recruiter Officer'),
        ('student', 'Scholar Student'),
    )
    
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    objects = NextHireUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


# ==========================================
# 2. SCHOLAR STUDENT PROFILE & EDUCATION ENTITIES
# ==========================================

class StudentProfile(models.Model):
    """
    Extended profile storing validated portfolio values, verified
    ATS Resume links, cumulative CGPA, and checked skills.
    """
    user = models.OneToOneField(NextHireUser, on_delete=models.CASCADE,特色_id="student_profile", related_name="student_profile")
    usn = models.CharField(max_length=15, unique=True, help_text="University Seat Number")
    course = models.CharField(max_length=100, default="MCA System Stream")
    specialization = models.CharField(max_length=150, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    backlogs = models.IntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, help_text="JSON list of validated technical stacks")
    resume_file_url = models.URLField(max_length=500, blank=True, null=True)
    avatar = models.CharField(max_length=5, default="👨‍💻")

    def __str__(self):
        return f"Dossier {self.usn} — {self.user.get_full_name()}"


class AcademicHistory(models.Model):
    """
    Maintains historical standard records for Class X & Class XII 
    matching rules before sending profile blocks to recruiters.
    """
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name="academic_history")
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    tenth_school = models.CharField(max_length=250)
    tenth_year = models.IntegerField()
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    twelfth_school = models.CharField(max_length=250)
    twelfth_year = models.IntegerField()


# ==========================================
# 3. RECRUITER, JOBS, & IN-PIPELINE APPLICATIONS
# ==========================================

class RecruiterCompany(models.Model):
    """
    Information regarding validated recruiters and company units logs.
    """
    user = models.OneToOneField(NextHireUser, on_delete=models.CASCADE, related_name="recruiter_company")
    company_name = models.CharField(max_length=250)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.company_name} (Recruiter: {self.user.email})"


class JobListing(models.Model):
    """
    Job positions hosted by recruiters with specific GPA constraints.
    """
    recruiter = models.ForeignKey(RecruiterCompany, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=250)
    description = models.TextField()
    salary_package = models.CharField(max_length=100, help_text="Package indicator eg: '18 LPA'")
    location = models.CharField(max_length=150)
    job_type = models.CharField(max_length=50, default="Full-time")
    skills_required = models.JSONField(default=list)
    min_cgpa_cutoff = models.DecimalField(max_digits=4, decimal_places=2, default=6.00)
    max_active_backlogs_allowed = models.IntegerField(default=0)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.recruiter.company_name}"


class JobApplication(models.Model):
    """
    Interactive student application logs linked with progress step milestones.
    """
    STATUS_CHOICES = (
        ('applied', 'Applied Status'),
        ('reviewing', 'Dossier Under Review'),
        ('shortlisted', 'Shortlisted Profile'),
        ('interview', 'Interviews Scheduled'),
        ('offered', 'Offer Issued'),
        ('rejected', 'Application Archived/Rejected'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="applicants")
    applied_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    interview_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'job')


# ==========================================
# 4. DATA SERIALIZATION PROTOCOLS
# ==========================================

class NextHireUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextHireUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone']


class StudentProfileSerializer(serializers.ModelSerializer):
    user = NextHireUserSerializer(read_only=True)
    class Meta:
        model = StudentProfile
        fields = ['user', 'usn', 'course', 'specialization', 'cgpa', 'backlogs', 'bio', 'skills', 'avatar']


class StudentRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    usn = serializers.CharField(max_length=15)
    course = serializers.CharField(max_length=100)
    cgpa = serializers.DecimalField(max_digits=4, decimal_places=2)
    skills = serializers.ListField(child=serializers.CharField())

    def validate_email(self, value):
        if NextHireUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email exists.")
        return value

    def create(self, validated_data):
        user = NextHireUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['name'],
            role='student',
            phone=validated_data['phone']
        )
        user.set_password(validated_data['password'])
        user.save()

        # Generate accompanying student profile
        StudentProfile.objects.create(
            user=user,
            usn=validated_data['usn'].upper(),
            course=validated_data['course'],
            cgpa=validated_data['cgpa'],
            skills=validated_data['skills']
        )
        return user


# ==========================================
# 5. RBAC PERMISSIONS CLASSES & API VIEWS
# ==========================================

class IsStudentUser(permissions.BasePermission):
    """
    Grants access exclusively to students registered in NextHire.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'


class IsRecruiterUser(permissions.BasePermission):
    """
    Grants access exclusively to recruiting partners.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'recruiter'


# 6. REST API CONTROLLERS
class StudentRegisterAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Student account registered successfully in MySQL database.",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": NextHireUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentDashboardAPI(APIView):
    """
    Retrieves synchronized stats for Student profile dashboards.
    """
    permission_classes = [IsStudentUser]

    def get(self, request):
        try:
            profile = request.user.student_profile
            applications = JobApplication.objects.filter(student=profile)
            
            # Format JSON response payload matching React dashboard expectations
            apps_count = applications.count()
            shortlisted_count = applications.filter(status__in=['shortlisted', 'interview']).count()
            interviews_count = applications.filter(status='interview').count()
            offers_count = applications.filter(status='offered').count()

            return Response({
                "profile": StudentProfileSerializer(profile).data,
                "metrics": {
                    "total_applications": apps_count,
                    "shortlisted": shortlisted_count,
                    "interviews": interviews_count,
                    "offers_received": offers_count
                },
                "sync_timestamp": "Django MySQL JWT validated 200 OK"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Unable to query records."}, status=status.HTTP_400_BAD_REQUEST)
